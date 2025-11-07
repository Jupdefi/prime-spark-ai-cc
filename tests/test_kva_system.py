"""
Comprehensive KVA System Test Suite
Unit tests, integration tests, and validation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json

from kva.storage_manager import KVAStorageManager, StorageConfig, StorageType
from kva.analytics_engine import KVAAnalyticsEngine
from kva.data_connectors import DataConnectorManager, HomelabSensorConnector


# === Fixtures ===

@pytest.fixture
async def storage_manager():
    """Storage manager fixture"""
    config = StorageConfig()
    manager = KVAStorageManager(config)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
async def analytics_engine():
    """Analytics engine fixture"""
    engine = KVAAnalyticsEngine()
    await engine.initialize()
    return engine


@pytest.fixture
async def connector_manager():
    """Connector manager fixture"""
    manager = DataConnectorManager()
    yield manager
    await manager.shutdown()


# === Storage Layer Tests ===

class TestStorageLayer:
    """Test storage layer functionality"""

    @pytest.mark.asyncio
    async def test_redis_operations(self, storage_manager):
        """Test Redis get/set operations"""
        # Set value
        key = "test_key"
        value = {"data": "test_value", "timestamp": datetime.now().isoformat()}

        success = await storage_manager.redis.set(key, value)
        assert success, "Redis SET should succeed"

        # Get value
        retrieved = await storage_manager.redis.get(key)
        assert retrieved is not None, "Redis GET should return value"
        assert retrieved["data"] == value["data"], "Retrieved data should match"

        # Delete value
        deleted = await storage_manager.redis.delete(key)
        assert deleted, "Redis DELETE should succeed"

        # Verify deletion
        retrieved = await storage_manager.redis.get(key)
        assert retrieved is None, "Deleted key should not exist"

    @pytest.mark.asyncio
    async def test_redis_ttl(self, storage_manager):
        """Test Redis TTL functionality"""
        key = "ttl_test"
        value = "expires_soon"
        ttl = 2  # 2 seconds

        await storage_manager.redis.set(key, value, ttl=ttl)
        retrieved = await storage_manager.redis.get(key)
        assert retrieved == value, "Value should exist immediately"

        # Wait for expiration
        await asyncio.sleep(3)
        retrieved = await storage_manager.redis.get(key)
        assert retrieved is None, "Value should expire after TTL"

    @pytest.mark.asyncio
    async def test_postgres_insert_event(self, storage_manager):
        """Test PostgreSQL event insertion"""
        event_data = {"action": "test", "value": 123}
        await storage_manager.postgres.insert_event(
            event_type="test_event",
            event_data=event_data,
            source="test_suite"
        )

        # Query events
        events = await storage_manager.postgres.fetch(
            "SELECT * FROM events WHERE event_type = $1 ORDER BY id DESC LIMIT 1",
            "test_event"
        )

        assert len(events) > 0, "Event should be inserted"
        assert events[0]["event_type"] == "test_event"

    @pytest.mark.asyncio
    async def test_clickhouse_batch_insert(self, storage_manager):
        """Test ClickHouse batch insertion"""
        events = [
            {
                "timestamp": datetime.now(),
                "event_type": "metric",
                "metric_name": "cpu_usage",
                "metric_value": 75.5,
                "labels": {"host": "test"},
                "source": "test"
            }
            for _ in range(10)
        ]

        await storage_manager.clickhouse.insert_events(events)

        # Query
        results = await storage_manager.clickhouse.query(
            "SELECT count() FROM time_series_events WHERE metric_name = 'cpu_usage'"
        )

        assert len(results) > 0, "Events should be inserted"

    @pytest.mark.asyncio
    async def test_unified_storage(self, storage_manager):
        """Test unified storage interface"""
        key = "unified_test"
        value = {"test": "data"}

        # Store in Redis
        success = await storage_manager.store(key, value, StorageType.REDIS)
        assert success, "Unified store should succeed"

        # Retrieve from Redis
        retrieved = await storage_manager.retrieve(key, StorageType.REDIS)
        assert retrieved["test"] == value["test"], "Retrieved value should match"


# === Analytics Engine Tests ===

class TestAnalyticsEngine:
    """Test analytics engine functionality"""

    @pytest.mark.asyncio
    async def test_batch_aggregation(self, analytics_engine, storage_manager):
        """Test batch aggregation"""
        # Insert test data
        events = [
            {
                "timestamp": datetime.now() - timedelta(minutes=i),
                "event_type": "metric",
                "metric_name": "test_metric",
                "metric_value": 50.0 + i,
                "labels": {},
                "source": "test"
            }
            for i in range(60)
        ]

        await storage_manager.clickhouse.insert_events(events)

        # Run aggregation
        result = await analytics_engine.batch_analytics.run_aggregation(
            "test_metric",
            (datetime.now() - timedelta(hours=2), datetime.now())
        )

        assert result["metric"] == "test_metric", "Metric name should match"
        assert len(result["data"]) > 0, "Should return aggregated data"

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, analytics_engine, storage_manager):
        """Test anomaly detection"""
        # Insert normal data with anomaly
        events = [
            {
                "timestamp": datetime.now() - timedelta(minutes=i),
                "event_type": "metric",
                "metric_name": "anomaly_test",
                "metric_value": 50.0 if i != 5 else 200.0,  # Anomaly at i=5
                "labels": {},
                "source": "test"
            }
            for i in range(20)
        ]

        await storage_manager.clickhouse.insert_events(events)

        # Detect anomalies
        anomalies = await analytics_engine.predictive.detect_anomalies("anomaly_test")

        assert len(anomalies) > 0, "Should detect anomalies"
        assert anomalies[0]["severity"] in ["medium", "high"], "Anomaly should have severity"

    @pytest.mark.asyncio
    async def test_ml_pipeline(self, analytics_engine):
        """Test ML pipeline"""
        import pandas as pd

        # Create training data
        training_data = pd.DataFrame({
            "feature1": [1, 2, 3, 4, 5],
            "feature2": [2, 4, 6, 8, 10],
            "target": [3, 6, 9, 12, 15]
        })

        # Train model
        result = await analytics_engine.ml_pipeline.train_model(
            "test_model",
            training_data,
            "regression"
        )

        assert result["type"] == "regression", "Model type should match"
        assert "trained_at" in result, "Should have training timestamp"

        # Predict
        prediction = await analytics_engine.ml_pipeline.predict(
            "test_model",
            {"feature1": 6, "feature2": 12}
        )

        assert "prediction" in prediction, "Should return prediction"
        assert "confidence" in prediction, "Should return confidence"


# === Data Connectors Tests ===

class TestDataConnectors:
    """Test data connector functionality"""

    @pytest.mark.asyncio
    async def test_homelab_sensor_connector(self, connector_manager):
        """Test homelab sensor connector"""
        homelab = HomelabSensorConnector({})
        await homelab.connect()

        # Fetch data
        data = await homelab.fetch_data()

        assert len(data) > 0, "Should collect sensor data"
        assert "system_cpu" in data, "Should have CPU sensor"
        assert "system_memory" in data, "Should have memory sensor"

        # Validate data structure
        cpu_data = data["system_cpu"]
        assert "value" in cpu_data, "Sensor data should have value"
        assert "timestamp" in cpu_data, "Sensor data should have timestamp"
        assert "unit" in cpu_data, "Sensor data should have unit"

        await homelab.disconnect()

    @pytest.mark.asyncio
    async def test_etl_pipeline(self, connector_manager, storage_manager):
        """Test ETL pipeline"""
        from kva.data_connectors import ETLJob

        # Create sensor connector
        homelab = HomelabSensorConnector({})

        # Register ETL job
        etl_job = ETLJob(
            job_id="test_etl",
            source_connector=homelab,
            schedule_interval=1  # 1 second for testing
        )

        connector_manager.etl_pipeline.register_job(etl_job)

        # Start job
        await connector_manager.etl_pipeline.start_job("test_etl")

        # Wait for execution
        await asyncio.sleep(2)

        # Stop job
        await connector_manager.etl_pipeline.stop_job("test_etl")

        # Check stats
        stats = connector_manager.etl_pipeline.get_stats()
        assert stats["total_runs"] > 0, "ETL job should have run"

        # Verify data in storage
        value = await storage_manager.redis.get("sensor:system_cpu")
        assert value is not None, "Sensor data should be stored"


# === Integration Tests ===

class TestKVAIntegration:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_data_pipeline(self, storage_manager, analytics_engine, connector_manager):
        """Test complete data pipeline: collect → store → analyze"""

        # 1. Collect data via connector
        homelab = HomelabSensorConnector({})
        await homelab.connect()
        sensor_data = await homelab.fetch_data()

        # 2. Store in all backends
        for sensor_name, sensor_value in sensor_data.items():
            # Redis for hot data
            await storage_manager.redis.set(f"sensor:{sensor_name}", sensor_value)

            # ClickHouse for time-series
            await storage_manager.clickhouse.insert_events([{
                "timestamp": datetime.now(),
                "event_type": "sensor",
                "metric_name": sensor_name,
                "metric_value": sensor_value.get("value", 0),
                "labels": {"type": sensor_value.get("type", "")},
                "source": "integration_test"
            }])

            # PostgreSQL for relational
            await storage_manager.postgres.insert_metric(
                metric_name=sensor_name,
                value=sensor_value.get("value", 0),
                labels={"type": sensor_value.get("type", "")}
            )

        # 3. Run analytics
        result = await analytics_engine.batch_analytics.run_aggregation(
            "system_cpu",
            (datetime.now() - timedelta(hours=1), datetime.now())
        )

        # Verify
        assert result["metric"] == "system_cpu"

        await homelab.disconnect()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage_manager):
        """Test concurrent storage operations"""
        # Create multiple concurrent operations
        tasks = []

        for i in range(100):
            tasks.append(storage_manager.redis.set(f"concurrent_{i}", {"value": i}))

        # Execute concurrently
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        assert all(results), "All concurrent operations should succeed"

        # Verify data
        for i in range(100):
            value = await storage_manager.redis.get(f"concurrent_{i}")
            assert value["value"] == i, f"Concurrent operation {i} should have correct value"


# === Performance Tests ===

class TestPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    async def test_redis_throughput(self, storage_manager):
        """Test Redis throughput"""
        import time

        count = 1000
        start_time = time.time()

        for i in range(count):
            await storage_manager.redis.set(f"perf_test_{i}", {"value": i})

        duration = time.time() - start_time
        ops_per_second = count / duration

        print(f"\nRedis throughput: {ops_per_second:.0f} ops/sec")
        assert ops_per_second > 500, "Redis should handle >500 ops/sec"

    @pytest.mark.asyncio
    async def test_batch_insert_performance(self, storage_manager):
        """Test batch insert performance"""
        import time

        count = 10000
        batch_size = 100

        events = [
            {
                "timestamp": datetime.now(),
                "event_type": "perf_test",
                "metric_name": "test_metric",
                "metric_value": float(i),
                "labels": {},
                "source": "perf_test"
            }
            for i in range(count)
        ]

        start_time = time.time()

        # Batch insert
        for i in range(0, count, batch_size):
            batch = events[i:i + batch_size]
            await storage_manager.clickhouse.insert_events(batch)

        duration = time.time() - start_time
        events_per_second = count / duration

        print(f"\nClickHouse batch insert: {events_per_second:.0f} events/sec")
        assert events_per_second > 1000, "Should handle >1000 events/sec"


# === Validation Framework ===

class TestValidation:
    """Data validation tests"""

    def test_schema_validation(self):
        """Test data schema validation"""
        from pydantic import BaseModel, ValidationError

        class SensorData(BaseModel):
            value: float
            timestamp: str
            unit: str

        # Valid data
        valid_data = {
            "value": 75.5,
            "timestamp": datetime.now().isoformat(),
            "unit": "%"
        }

        sensor = SensorData(**valid_data)
        assert sensor.value == 75.5

        # Invalid data
        invalid_data = {"value": "not_a_number"}

        with pytest.raises(ValidationError):
            SensorData(**invalid_data)

    @pytest.mark.asyncio
    async def test_data_consistency(self, storage_manager):
        """Test data consistency across backends"""
        key = "consistency_test"
        value = {"test": "data", "timestamp": datetime.now().isoformat()}

        # Store in Redis
        await storage_manager.redis.set(key, value)

        # Store in PostgreSQL
        await storage_manager.postgres.insert_event(
            event_type="consistency_test",
            event_data=value,
            source="validation"
        )

        # Retrieve from both
        redis_value = await storage_manager.redis.get(key)
        pg_events = await storage_manager.postgres.fetch(
            "SELECT * FROM events WHERE event_type = $1 ORDER BY id DESC LIMIT 1",
            "consistency_test"
        )

        # Verify consistency
        assert redis_value["test"] == value["test"]
        assert json.loads(pg_events[0]["event_data"])["test"] == value["test"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
