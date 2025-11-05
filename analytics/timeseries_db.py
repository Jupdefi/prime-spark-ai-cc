"""
TimescaleDB Analytics Storage
Stores time-series data and analytics with PostgreSQL + TimescaleDB
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncpg
from dataclasses import dataclass


@dataclass
class TimeSeriesData:
    """Time series data point"""
    timestamp: datetime
    metric_name: str
    value: float
    device_id: str
    tags: Dict[str, str]


class TimescaleDBManager:
    """
    Manages TimescaleDB for time-series analytics.

    Tables:
    - device_metrics: System metrics from edge devices
    - ai_inference_results: AI inference results
    - sensor_data: Sensor readings
    - analytics_events: Processed analytics events
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "prime_spark_analytics",
        user: str = "postgres",
        password: str = "postgres"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=5,
                max_size=20
            )

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

    async def initialize_schema(self):
        """Initialize database schema with TimescaleDB"""
        await self.connect()

        async with self.pool.acquire() as conn:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

            # Device metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS device_metrics (
                    time TIMESTAMPTZ NOT NULL,
                    device_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value DOUBLE PRECISION,
                    tags JSONB,
                    PRIMARY KEY (time, device_id, metric_name)
                );
            """)

            # Convert to hypertable
            try:
                await conn.execute("""
                    SELECT create_hypertable('device_metrics', 'time',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    );
                """)
            except Exception:
                pass  # Hypertable might already exist

            # AI inference results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_inference_results (
                    time TIMESTAMPTZ NOT NULL,
                    device_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    inference_time_ms DOUBLE PRECISION,
                    result JSONB,
                    accuracy DOUBLE PRECISION,
                    PRIMARY KEY (time, device_id, model_name)
                );
            """)

            try:
                await conn.execute("""
                    SELECT create_hypertable('ai_inference_results', 'time',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    );
                """)
            except Exception:
                pass

            # Sensor data table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    time TIMESTAMPTZ NOT NULL,
                    device_id TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    sensor_id TEXT,
                    value DOUBLE PRECISION,
                    unit TEXT,
                    data JSONB,
                    PRIMARY KEY (time, device_id, sensor_type)
                );
            """)

            try:
                await conn.execute("""
                    SELECT create_hypertable('sensor_data', 'time',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 hour'
                    );
                """)
            except Exception:
                pass

            # Analytics events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    time TIMESTAMPTZ NOT NULL,
                    event_type TEXT NOT NULL,
                    device_id TEXT,
                    event_data JSONB,
                    PRIMARY KEY (time, event_type, device_id)
                );
            """)

            try:
                await conn.execute("""
                    SELECT create_hypertable('analytics_events', 'time',
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    );
                """)
            except Exception:
                pass

            # Create indexes for common queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_device_metrics_device_time
                ON device_metrics (device_id, time DESC);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_inference_model_time
                ON ai_inference_results (model_name, time DESC);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_data_type_time
                ON sensor_data (sensor_type, time DESC);
            """)

            # Create continuous aggregates for common queries
            try:
                await conn.execute("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS device_metrics_hourly
                    WITH (timescaledb.continuous) AS
                    SELECT
                        time_bucket('1 hour', time) AS bucket,
                        device_id,
                        metric_name,
                        AVG(value) as avg_value,
                        MAX(value) as max_value,
                        MIN(value) as min_value,
                        COUNT(*) as count
                    FROM device_metrics
                    GROUP BY bucket, device_id, metric_name
                    WITH NO DATA;
                """)

                # Add refresh policy
                await conn.execute("""
                    SELECT add_continuous_aggregate_policy('device_metrics_hourly',
                        start_offset => INTERVAL '3 hours',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '1 hour',
                        if_not_exists => TRUE
                    );
                """)
            except Exception:
                pass

    async def insert_device_metric(
        self,
        device_id: str,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Insert device metric"""
        await self.connect()

        timestamp = timestamp or datetime.utcnow()
        tags = tags or {}

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO device_metrics (time, device_id, metric_name, value, tags)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (time, device_id, metric_name) DO UPDATE
                SET value = EXCLUDED.value, tags = EXCLUDED.tags;
            """, timestamp, device_id, metric_name, value, tags)

    async def insert_ai_inference(
        self,
        device_id: str,
        model_name: str,
        inference_time_ms: float,
        result: Dict[str, Any],
        accuracy: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ):
        """Insert AI inference result"""
        await self.connect()

        timestamp = timestamp or datetime.utcnow()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ai_inference_results
                (time, device_id, model_name, inference_time_ms, result, accuracy)
                VALUES ($1, $2, $3, $4, $5, $6);
            """, timestamp, device_id, model_name, inference_time_ms, result, accuracy)

    async def insert_sensor_data(
        self,
        device_id: str,
        sensor_type: str,
        value: float,
        sensor_id: Optional[str] = None,
        unit: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Insert sensor data"""
        await self.connect()

        timestamp = timestamp or datetime.utcnow()

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO sensor_data
                (time, device_id, sensor_type, sensor_id, value, unit, data)
                VALUES ($1, $2, $3, $4, $5, $6, $7);
            """, timestamp, device_id, sensor_type, sensor_id, value, unit, data)

    async def query_device_metrics(
        self,
        device_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Query device metrics for a time range"""
        await self.connect()

        end_time = end_time or datetime.utcnow()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT time, value, tags
                FROM device_metrics
                WHERE device_id = $1
                  AND metric_name = $2
                  AND time >= $3
                  AND time <= $4
                ORDER BY time DESC;
            """, device_id, metric_name, start_time, end_time)

            return [dict(row) for row in rows]

    async def get_device_metrics_stats(
        self,
        device_id: str,
        metric_name: str,
        hours: int = 24
    ) -> Dict[str, float]:
        """Get statistics for a device metric"""
        await self.connect()

        start_time = datetime.utcnow() - timedelta(hours=hours)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    AVG(value) as avg,
                    MAX(value) as max,
                    MIN(value) as min,
                    STDDEV(value) as stddev,
                    COUNT(*) as count
                FROM device_metrics
                WHERE device_id = $1
                  AND metric_name = $2
                  AND time >= $3;
            """, device_id, metric_name, start_time)

            return dict(row) if row else {}

    async def get_ai_inference_performance(
        self,
        model_name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get AI inference performance statistics"""
        await self.connect()

        start_time = datetime.utcnow() - timedelta(hours=hours)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    AVG(inference_time_ms) as avg_inference_time,
                    MAX(inference_time_ms) as max_inference_time,
                    MIN(inference_time_ms) as min_inference_time,
                    AVG(accuracy) as avg_accuracy,
                    COUNT(*) as total_inferences
                FROM ai_inference_results
                WHERE model_name = $1
                  AND time >= $2;
            """, model_name, start_time)

            return dict(row) if row else {}

    async def cleanup_old_data(self, retention_days: int = 90):
        """Cleanup data older than retention period"""
        await self.connect()

        cutoff_time = datetime.utcnow() - timedelta(days=retention_days)

        async with self.pool.acquire() as conn:
            # Use TimescaleDB's drop_chunks for efficient deletion
            await conn.execute("""
                SELECT drop_chunks('device_metrics', older_than => $1);
            """, cutoff_time)

            await conn.execute("""
                SELECT drop_chunks('ai_inference_results', older_than => $1);
            """, cutoff_time)

            await conn.execute("""
                SELECT drop_chunks('sensor_data', older_than => $1);
            """, cutoff_time)


# Global TimescaleDB manager instance
timescale_db = TimescaleDBManager()
