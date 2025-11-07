"""
Cloud KVA Analytics Engine
Distributed key-value analytics with TimescaleDB and Redis integration
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncpg
import aioredis
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class AggregationType(Enum):
    """Supported aggregation types"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    STDDEV = "stddev"
    VARIANCE = "variance"


class TimeGranularity(Enum):
    """Time bucket granularities"""
    SECOND = "1 second"
    MINUTE = "1 minute"
    HOUR = "1 hour"
    DAY = "1 day"
    WEEK = "1 week"
    MONTH = "1 month"


@dataclass
class QueryConfig:
    """Analytics query configuration"""
    metric_name: str
    aggregation: AggregationType
    time_range: Tuple[datetime, datetime]
    granularity: TimeGranularity = TimeGranularity.MINUTE
    group_by: Optional[List[str]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = None


@dataclass
class AnalyticsResult:
    """Analytics query result"""
    metric_name: str
    aggregation: AggregationType
    data: pd.DataFrame
    metadata: Dict[str, Any]
    computed_at: datetime
    cache_key: Optional[str] = None


class TimescaleDBManager:
    """TimescaleDB time-series database manager"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("TimescaleDB connection pool initialized")

            # Create tables if not exist
            await self._initialize_schema()
        except Exception as e:
            logger.error(f"Failed to initialize TimescaleDB: {e}")
            raise

    async def _initialize_schema(self):
        """Initialize database schema"""
        async with self.pool.acquire() as conn:
            # Create extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

            # Create metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    time TIMESTAMPTZ NOT NULL,
                    metric_name TEXT NOT NULL,
                    value DOUBLE PRECISION,
                    labels JSONB,
                    source TEXT,
                    device_id TEXT
                );
            """)

            # Create hypertable
            await conn.execute("""
                SELECT create_hypertable('metrics', 'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name_time
                ON metrics (metric_name, time DESC);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_labels
                ON metrics USING GIN (labels);
            """)

            # Create continuous aggregates
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 hour', time) AS hour,
                    metric_name,
                    AVG(value) as avg_value,
                    MAX(value) as max_value,
                    MIN(value) as min_value,
                    COUNT(*) as count
                FROM metrics
                GROUP BY hour, metric_name
                WITH NO DATA;
            """)

            # Add refresh policy
            await conn.execute("""
                SELECT add_continuous_aggregate_policy('metrics_hourly',
                    start_offset => INTERVAL '3 hours',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour',
                    if_not_exists => TRUE
                );
            """)

            logger.info("TimescaleDB schema initialized")

    async def insert_metric(self, metric_name: str, value: float,
                           labels: Optional[Dict[str, Any]] = None,
                           source: Optional[str] = None,
                           device_id: Optional[str] = None,
                           timestamp: Optional[datetime] = None):
        """Insert a metric data point"""
        if timestamp is None:
            timestamp = datetime.now()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO metrics (time, metric_name, value, labels, source, device_id)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, timestamp, metric_name, value, labels or {}, source, device_id)

    async def insert_metrics_batch(self, metrics: List[Dict[str, Any]]):
        """Batch insert metrics"""
        async with self.pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO metrics (time, metric_name, value, labels, source, device_id)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, [
                (
                    m.get('timestamp', datetime.now()),
                    m['metric_name'],
                    m['value'],
                    m.get('labels', {}),
                    m.get('source'),
                    m.get('device_id')
                )
                for m in metrics
            ])

    async def query_metrics(self, query_config: QueryConfig) -> pd.DataFrame:
        """Query metrics with aggregation"""
        start_time, end_time = query_config.time_range

        # Build query
        select_clause = self._build_select_clause(query_config)
        where_clause = self._build_where_clause(query_config)
        group_by_clause = self._build_group_by_clause(query_config)

        query = f"""
            SELECT
                time_bucket('{query_config.granularity.value}', time) AS bucket,
                {select_clause}
            FROM metrics
            WHERE metric_name = $1
              AND time >= $2
              AND time <= $3
              {where_clause}
            {group_by_clause}
            ORDER BY bucket DESC
        """

        if query_config.limit:
            query += f" LIMIT {query_config.limit}"

        # Execute query
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query,
                query_config.metric_name,
                start_time,
                end_time
            )

        # Convert to DataFrame
        df = pd.DataFrame(
            [dict(row) for row in rows],
            columns=[desc.name for desc in rows[0].keys()] if rows else []
        )

        return df

    def _build_select_clause(self, config: QueryConfig) -> str:
        """Build SELECT clause for aggregation"""
        agg_map = {
            AggregationType.SUM: "SUM(value)",
            AggregationType.AVG: "AVG(value)",
            AggregationType.MIN: "MIN(value)",
            AggregationType.MAX: "MAX(value)",
            AggregationType.COUNT: "COUNT(*)",
            AggregationType.STDDEV: "STDDEV(value)",
            AggregationType.VARIANCE: "VARIANCE(value)",
        }

        select = agg_map.get(config.aggregation, "AVG(value)")

        if config.group_by:
            group_fields = ", ".join(config.group_by)
            return f"{group_fields}, {select} as value"

        return f"{select} as value"

    def _build_where_clause(self, config: QueryConfig) -> str:
        """Build WHERE clause for filters"""
        if not config.filters:
            return ""

        conditions = []
        for key, value in config.filters.items():
            if isinstance(value, str):
                conditions.append(f"labels->'{key}' = '\"{value}\"'")
            else:
                conditions.append(f"labels->'{key}' = '{value}'")

        return " AND " + " AND ".join(conditions) if conditions else ""

    def _build_group_by_clause(self, config: QueryConfig) -> str:
        """Build GROUP BY clause"""
        if config.group_by:
            group_fields = ", ".join(config.group_by)
            return f"GROUP BY bucket, {group_fields}"
        return "GROUP BY bucket"

    async def get_metric_summary(self, metric_name: str,
                                time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        start_time, end_time = time_range

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    COUNT(*) as count,
                    AVG(value) as avg,
                    MIN(value) as min,
                    MAX(value) as max,
                    STDDEV(value) as stddev,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as p50,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99
                FROM metrics
                WHERE metric_name = $1
                  AND time >= $2
                  AND time <= $3
            """, metric_name, start_time, end_time)

        return dict(row) if row else {}

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()


class RedisAnalyticsCache:
    """Redis-based analytics cache"""

    def __init__(self, redis_url: str, ttl: int = 300):
        self.redis_url = redis_url
        self.default_ttl = ttl
        self.redis: Optional[aioredis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            logger.info("Redis analytics cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis = None

    async def get(self, cache_key: str) -> Optional[AnalyticsResult]:
        """Get cached analytics result"""
        if not self.redis:
            return None

        try:
            data = await self.redis.get(cache_key)
            if data:
                # Deserialize (simplified - would use pickle in production)
                return None  # TODO: Implement deserialization
        except Exception as e:
            logger.error(f"Cache get failed: {e}")

        return None

    async def set(self, cache_key: str, result: AnalyticsResult,
                 ttl: Optional[int] = None):
        """Cache analytics result"""
        if not self.redis:
            return

        try:
            ttl = ttl or self.default_ttl
            # Serialize (simplified - would use pickle in production)
            # await self.redis.setex(cache_key, ttl, serialized_data)
            pass  # TODO: Implement serialization
        except Exception as e:
            logger.error(f"Cache set failed: {e}")

    async def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self.redis:
            return

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()


class KVAAnalyticsEngine:
    """Main KVA analytics engine"""

    def __init__(self, timescale_conn_str: str, redis_url: str):
        self.timescale = TimescaleDBManager(timescale_conn_str)
        self.cache = RedisAnalyticsCache(redis_url)
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_inserts": 0,
            "query_latency_ms": []
        }

    async def initialize(self):
        """Initialize analytics engine"""
        await self.timescale.initialize()
        await self.cache.initialize()
        logger.info("KVA Analytics Engine initialized")

    async def insert_metric(self, metric_name: str, value: float,
                           labels: Optional[Dict[str, Any]] = None,
                           source: Optional[str] = None,
                           device_id: Optional[str] = None):
        """Insert a single metric"""
        await self.timescale.insert_metric(
            metric_name, value, labels, source, device_id
        )
        self.stats["total_inserts"] += 1

        # Invalidate related cache entries
        cache_pattern = f"analytics:{metric_name}:*"
        await self.cache.invalidate(cache_pattern)

    async def insert_metrics_batch(self, metrics: List[Dict[str, Any]]):
        """Batch insert metrics"""
        await self.timescale.insert_metrics_batch(metrics)
        self.stats["total_inserts"] += len(metrics)

        # Invalidate cache for all affected metrics
        metric_names = set(m['metric_name'] for m in metrics)
        for metric_name in metric_names:
            await self.cache.invalidate(f"analytics:{metric_name}:*")

    async def query(self, query_config: QueryConfig) -> AnalyticsResult:
        """Execute analytics query with caching"""
        start_time = datetime.now()
        self.stats["total_queries"] += 1

        # Generate cache key
        cache_key = self._generate_cache_key(query_config)

        # Check cache
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            self.stats["cache_hits"] += 1
            logger.debug(f"Cache hit for query: {cache_key}")
            return cached_result

        self.stats["cache_misses"] += 1

        # Execute query
        df = await self.timescale.query_metrics(query_config)

        # Create result
        result = AnalyticsResult(
            metric_name=query_config.metric_name,
            aggregation=query_config.aggregation,
            data=df,
            metadata={
                "query_config": {
                    "granularity": query_config.granularity.value,
                    "time_range": [
                        query_config.time_range[0].isoformat(),
                        query_config.time_range[1].isoformat()
                    ]
                },
                "row_count": len(df)
            },
            computed_at=datetime.now(),
            cache_key=cache_key
        )

        # Cache result
        await self.cache.set(cache_key, result)

        # Track latency
        latency = (datetime.now() - start_time).total_seconds() * 1000
        self.stats["query_latency_ms"].append(latency)

        return result

    async def get_summary(self, metric_name: str,
                         time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get metric summary statistics"""
        return await self.timescale.get_metric_summary(metric_name, time_range)

    def _generate_cache_key(self, config: QueryConfig) -> str:
        """Generate cache key for query config"""
        start, end = config.time_range
        key_parts = [
            "analytics",
            config.metric_name,
            config.aggregation.value,
            config.granularity.value,
            start.isoformat(),
            end.isoformat()
        ]

        if config.group_by:
            key_parts.append(",".join(config.group_by))

        if config.filters:
            filter_str = ",".join(f"{k}={v}" for k, v in sorted(config.filters.items()))
            key_parts.append(filter_str)

        return ":".join(key_parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get analytics engine statistics"""
        cache_hit_rate = (
            self.stats["cache_hits"] / self.stats["total_queries"]
            if self.stats["total_queries"] > 0 else 0
        )

        avg_latency = (
            np.mean(self.stats["query_latency_ms"])
            if self.stats["query_latency_ms"] else 0
        )

        p95_latency = (
            np.percentile(self.stats["query_latency_ms"], 95)
            if self.stats["query_latency_ms"] else 0
        )

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "avg_query_latency_ms": avg_latency,
            "p95_query_latency_ms": p95_latency
        }

    async def close(self):
        """Close all connections"""
        await self.timescale.close()
        await self.cache.close()


# Global analytics engine instance
_analytics_engine = None

def get_analytics_engine() -> KVAAnalyticsEngine:
    """Get global analytics engine instance"""
    global _analytics_engine
    if _analytics_engine is None:
        # TODO: Load from config
        timescale_conn = "postgresql://postgres:SparkAI2025!@localhost:5433/timescale"
        redis_url = "redis://localhost:6379"
        _analytics_engine = KVAAnalyticsEngine(timescale_conn, redis_url)
    return _analytics_engine
