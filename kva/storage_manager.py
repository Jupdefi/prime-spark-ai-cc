"""
KVA Storage Layer Manager
Unified interface for Redis, PostgreSQL, ClickHouse, and Object Storage
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import pickle

import aioredis
import asyncpg
from aiobotocore.session import get_session
import clickhouse_connect

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Storage backend types"""
    REDIS = "redis"
    POSTGRES = "postgres"
    CLICKHOUSE = "clickhouse"
    OBJECT_STORAGE = "s3"


@dataclass
class StorageConfig:
    """Storage configuration"""
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_cluster_nodes: List[str] = None

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "prime_spark"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # ClickHouse
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "prime_spark"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    # Object Storage (S3/MinIO)
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "prime-spark"
    s3_region: str = "us-east-1"


class RedisManager:
    """Redis cluster manager for hot data"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        self.stats = {"gets": 0, "sets": 0, "deletes": 0}

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.create_redis_pool(
                f'redis://{self.config.redis_host}:{self.config.redis_port}',
                db=self.config.redis_db,
                password=self.config.redis_password,
                encoding='utf-8',
                minsize=5,
                maxsize=20
            )
            logger.info(f"Redis connected: {self.config.redis_host}:{self.config.redis_port}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = await self.redis.get(key)
            self.stats["gets"] += 1
            if value:
                return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from Redis"""
        try:
            await self.redis.delete(key)
            self.stats["deletes"] += 1
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple values"""
        try:
            values = await self.redis.mget(*keys)
            self.stats["gets"] += len(keys)
            return [json.loads(v) if v else None for v in values]
        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return [None] * len(keys)

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()


class PostgreSQLManager:
    """PostgreSQL manager for relational analytics"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.stats = {"queries": 0, "inserts": 0}

    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_database,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                min_size=5,
                max_size=20
            )
            logger.info(f"PostgreSQL connected: {self.config.postgres_host}:{self.config.postgres_port}")
            await self._initialize_schema()
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise

    async def _initialize_schema(self):
        """Initialize database schema"""
        async with self.pool.acquire() as conn:
            # Events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    event_data JSONB NOT NULL,
                    source VARCHAR(100),
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    metadata JSONB
                );
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
            """)

            # Metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DOUBLE PRECISION NOT NULL,
                    labels JSONB,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
            """)

            # User sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    metadata JSONB
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
            """)

    async def execute(self, query: str, *args) -> str:
        """Execute SQL query"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *args)
                self.stats["queries"] += 1
                return result
        except Exception as e:
            logger.error(f"PostgreSQL execute error: {e}")
            raise

    async def fetch(self, query: str, *args) -> List[Dict]:
        """Fetch query results"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                self.stats["queries"] += 1
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"PostgreSQL fetch error: {e}")
            return []

    async def insert_event(self, event_type: str, event_data: Dict,
                          source: str = None, metadata: Dict = None):
        """Insert event"""
        await self.execute(
            "INSERT INTO events (event_type, event_data, source, metadata) VALUES ($1, $2, $3, $4)",
            event_type, json.dumps(event_data), source, json.dumps(metadata) if metadata else None
        )
        self.stats["inserts"] += 1

    async def insert_metric(self, metric_name: str, value: float, labels: Dict = None):
        """Insert metric"""
        await self.execute(
            "INSERT INTO metrics (metric_name, metric_value, labels) VALUES ($1, $2, $3)",
            metric_name, value, json.dumps(labels) if labels else None
        )
        self.stats["inserts"] += 1

    async def close(self):
        """Close PostgreSQL pool"""
        if self.pool:
            await self.pool.close()


class ClickHouseManager:
    """ClickHouse manager for time-series data"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.client: Optional[clickhouse_connect.driver.Client] = None
        self.stats = {"inserts": 0, "queries": 0}

    async def initialize(self):
        """Initialize ClickHouse connection"""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.config.clickhouse_host,
                port=self.config.clickhouse_port,
                username=self.config.clickhouse_user,
                password=self.config.clickhouse_password,
                database=self.config.clickhouse_database
            )
            logger.info(f"ClickHouse connected: {self.config.clickhouse_host}:{self.config.clickhouse_port}")
            await self._initialize_schema()
        except Exception as e:
            logger.error(f"ClickHouse connection failed: {e}")
            raise

    async def _initialize_schema(self):
        """Initialize ClickHouse schema"""
        # Time-series events table
        self.client.command("""
            CREATE TABLE IF NOT EXISTS time_series_events (
                timestamp DateTime64(3),
                event_type String,
                metric_name String,
                metric_value Float64,
                labels Map(String, String),
                source String
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(timestamp)
            ORDER BY (timestamp, event_type, metric_name)
        """)

        # Aggregated metrics (materialized view)
        self.client.command("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly
            ENGINE = AggregatingMergeTree()
            PARTITION BY toYYYYMM(hour)
            ORDER BY (hour, metric_name)
            AS SELECT
                toStartOfHour(timestamp) AS hour,
                metric_name,
                avgState(metric_value) AS avg_value,
                maxState(metric_value) AS max_value,
                minState(metric_value) AS min_value,
                countState() AS count
            FROM time_series_events
            GROUP BY hour, metric_name
        """)

    async def insert_events(self, events: List[Dict]):
        """Batch insert events"""
        if not events:
            return

        data = [
            [
                e.get('timestamp', datetime.now()),
                e['event_type'],
                e['metric_name'],
                e['metric_value'],
                e.get('labels', {}),
                e.get('source', '')
            ]
            for e in events
        ]

        self.client.insert('time_series_events', data,
                          column_names=['timestamp', 'event_type', 'metric_name',
                                      'metric_value', 'labels', 'source'])
        self.stats["inserts"] += len(events)

    async def query(self, query: str) -> List[Dict]:
        """Execute query"""
        try:
            result = self.client.query(query)
            self.stats["queries"] += 1
            return result.result_rows
        except Exception as e:
            logger.error(f"ClickHouse query error: {e}")
            return []

    async def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.close()


class ObjectStorageManager:
    """S3/MinIO manager for large datasets"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.session = get_session()
        self.stats = {"uploads": 0, "downloads": 0}

    async def initialize(self):
        """Initialize object storage"""
        try:
            # Create bucket if not exists
            async with self.session.create_client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                region_name=self.config.s3_region
            ) as client:
                try:
                    await client.head_bucket(Bucket=self.config.s3_bucket)
                except:
                    await client.create_bucket(Bucket=self.config.s3_bucket)
            logger.info(f"Object storage initialized: {self.config.s3_bucket}")
        except Exception as e:
            logger.error(f"Object storage initialization failed: {e}")
            raise

    async def upload(self, key: str, data: bytes, metadata: Dict = None) -> bool:
        """Upload object"""
        try:
            async with self.session.create_client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                region_name=self.config.s3_region
            ) as client:
                await client.put_object(
                    Bucket=self.config.s3_bucket,
                    Key=key,
                    Body=data,
                    Metadata=metadata or {}
                )
                self.stats["uploads"] += 1
                return True
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False

    async def download(self, key: str) -> Optional[bytes]:
        """Download object"""
        try:
            async with self.session.create_client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                region_name=self.config.s3_region
            ) as client:
                response = await client.get_object(
                    Bucket=self.config.s3_bucket,
                    Key=key
                )
                data = await response['Body'].read()
                self.stats["downloads"] += 1
                return data
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    async def list_objects(self, prefix: str = "") -> List[str]:
        """List objects"""
        try:
            async with self.session.create_client(
                's3',
                endpoint_url=self.config.s3_endpoint,
                aws_access_key_id=self.config.s3_access_key,
                aws_secret_access_key=self.config.s3_secret_key,
                region_name=self.config.s3_region
            ) as client:
                response = await client.list_objects_v2(
                    Bucket=self.config.s3_bucket,
                    Prefix=prefix
                )
                return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"List objects error: {e}")
            return []


class KVAStorageManager:
    """Unified KVA storage manager"""

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.redis = RedisManager(self.config)
        self.postgres = PostgreSQLManager(self.config)
        self.clickhouse = ClickHouseManager(self.config)
        self.object_storage = ObjectStorageManager(self.config)

    async def initialize(self):
        """Initialize all storage backends"""
        await asyncio.gather(
            self.redis.initialize(),
            self.postgres.initialize(),
            self.clickhouse.initialize(),
            self.object_storage.initialize()
        )
        logger.info("KVA Storage Manager initialized")

    async def store(self, key: str, value: Any, storage_type: StorageType = StorageType.REDIS,
                   ttl: Optional[int] = None) -> bool:
        """Store data in specified backend"""
        if storage_type == StorageType.REDIS:
            return await self.redis.set(key, value, ttl)
        elif storage_type == StorageType.OBJECT_STORAGE:
            data = pickle.dumps(value)
            return await self.object_storage.upload(key, data)
        return False

    async def retrieve(self, key: str, storage_type: StorageType = StorageType.REDIS) -> Optional[Any]:
        """Retrieve data from specified backend"""
        if storage_type == StorageType.REDIS:
            return await self.redis.get(key)
        elif storage_type == StorageType.OBJECT_STORAGE:
            data = await self.object_storage.download(key)
            return pickle.loads(data) if data else None
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all backends"""
        return {
            "redis": self.redis.stats,
            "postgres": self.postgres.stats,
            "clickhouse": self.clickhouse.stats,
            "object_storage": self.object_storage.stats
        }

    async def close(self):
        """Close all connections"""
        await asyncio.gather(
            self.redis.close(),
            self.postgres.close(),
            self.clickhouse.close()
        )


# Global instance
_storage_manager = None

def get_storage_manager() -> KVAStorageManager:
    """Get global storage manager"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = KVAStorageManager()
    return _storage_manager
