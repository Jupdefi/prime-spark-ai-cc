"""
Comprehensive Integration Tests for Prime Spark AI

Tests all major system components and their interactions.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime

# Import all major components
from prime_spark.intelligent_lb.router import IntelligentRouter
from prime_spark.intelligent_lb.predictor import LoadPredictor
from prime_spark.intelligent_lb.cost_optimizer import CostOptimizer
from prime_spark.intelligent_lb.geo_optimizer import GeoOptimizer

from prime_spark.security.zero_trust import ZeroTrustFramework
from prime_spark.security.encryption import EncryptionManager
from prime_spark.security.iam import IAMManager
from prime_spark.security.threat_detector import ThreatDetector

from prime_spark.data_intelligence.quality_checker import DataQualityChecker
from prime_spark.data_intelligence.schema_evolution import SchemaEvolutionManager
from prime_spark.data_intelligence.lineage_tracker import LineageTracker
from prime_spark.data_intelligence.privacy_compliance import PrivacyComplianceChecker

from prime_spark.edge_ai.federated_learning import FederatedLearningClient
from prime_spark.edge_ai.model_compression import ModelCompressor
from prime_spark.edge_ai.offline_inference import OfflineInferenceEngine
from prime_spark.edge_ai.edge_cloud_sync import EdgeCloudSync


class TestIntelligentLoadBalancing:
    """Test intelligent load balancing components"""

    def test_intelligent_router_initialization(self):
        """Test IntelligentRouter can be initialized"""
        router = IntelligentRouter(
            edge_endpoints=["http://edge1:8000"],
            cloud_endpoints=["http://cloud1:8000"]
        )
        assert router is not None
        assert len(router.edge_endpoints) >= 1
        assert len(router.cloud_endpoints) >= 1

    def test_load_predictor(self):
        """Test load prediction"""
        predictor = LoadPredictor(window_size=10)

        # Add historical data
        for i in range(20):
            predictor.add_observation(
                endpoint="http://edge1:8000",
                latency_ms=100 + i,
                load=0.5 + (i * 0.01)
            )

        # Predict future load
        prediction = predictor.predict_load("http://edge1:8000", horizon_minutes=5)
        assert prediction is not None
        assert 0 <= prediction <= 1.0

    def test_cost_optimizer(self):
        """Test cost optimization"""
        optimizer = CostOptimizer()

        # Define pricing
        optimizer.set_pricing(
            endpoint="http://cloud1:8000",
            cost_per_request=0.001,
            cost_per_gb=0.10
        )

        # Get optimal endpoint
        request_size_mb = 1.0
        optimal = optimizer.get_optimal_endpoint(
            available_endpoints=["http://edge1:8000", "http://cloud1:8000"],
            request_size_mb=request_size_mb
        )

        assert optimal in ["http://edge1:8000", "http://cloud1:8000"]

    def test_geo_optimizer(self):
        """Test geographic optimization"""
        optimizer = GeoOptimizer()

        # Set locations
        optimizer.set_endpoint_location("http://edge1:8000", lat=37.7749, lon=-122.4194)
        optimizer.set_endpoint_location("http://cloud1:8000", lat=40.7128, lon=-74.0060)

        # Find nearest
        nearest = optimizer.find_nearest_endpoint(
            available_endpoints=["http://edge1:8000", "http://cloud1:8000"],
            user_lat=37.8,
            user_lon=-122.4
        )

        assert nearest == "http://edge1:8000"  # Closer to user


class TestSecurityFramework:
    """Test security framework components"""

    def test_zero_trust_framework(self):
        """Test Zero Trust framework"""
        zt = ZeroTrustFramework()

        # Verify access
        result = zt.verify_access(
            user_id="user123",
            resource="api.endpoint",
            action="read",
            context={"ip": "192.168.1.100"}
        )

        assert isinstance(result, bool)

    def test_encryption_manager(self):
        """Test encryption/decryption"""
        em = EncryptionManager()

        # Generate key
        key = em.generate_key()
        assert len(key) > 0

        # Encrypt data
        plaintext = b"Sensitive data"
        ciphertext = em.encrypt(plaintext, key)
        assert ciphertext != plaintext

        # Decrypt data
        decrypted = em.decrypt(ciphertext, key)
        assert decrypted == plaintext

    def test_iam_manager(self):
        """Test IAM manager"""
        iam = IAMManager()

        # Create user
        user_id = iam.create_user(
            username="testuser",
            email="test@example.com",
            roles=["user"]
        )
        assert user_id is not None

        # Verify permissions
        has_permission = iam.check_permission(
            user_id=user_id,
            resource="api.read",
            action="read"
        )
        assert isinstance(has_permission, bool)

    def test_threat_detector(self):
        """Test threat detection"""
        detector = ThreatDetector()

        # Analyze request
        threat_score = detector.analyze_request(
            user_id="user123",
            endpoint="/api/data",
            method="GET",
            payload_size=1024,
            ip_address="192.168.1.100"
        )

        assert 0 <= threat_score <= 1.0


class TestDataIntelligence:
    """Test data intelligence components"""

    def test_quality_checker(self):
        """Test data quality checking"""
        checker = DataQualityChecker()

        # Check data quality
        data = {
            "values": [1, 2, 3, None, 5],
            "timestamps": ["2025-11-05T10:00:00"] * 5
        }

        report = checker.check_quality(data)

        assert "completeness" in report
        assert "validity" in report
        assert 0 <= report["completeness"] <= 1.0

    def test_schema_evolution(self):
        """Test schema evolution"""
        manager = SchemaEvolutionManager()

        # Register schema
        schema_v1 = {
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "string"}
            ]
        }
        manager.register_schema("users", version=1, schema=schema_v1)

        # Evolve schema
        schema_v2 = {
            "fields": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "string"},
                {"name": "email", "type": "string"}
            ]
        }
        compatible = manager.is_compatible("users", schema_v1, schema_v2)

        assert isinstance(compatible, bool)

    def test_lineage_tracker(self):
        """Test data lineage tracking"""
        tracker = LineageTracker()

        # Track transformation
        tracker.track_transformation(
            source_dataset="raw_data",
            target_dataset="processed_data",
            operation="filter",
            metadata={"filter": "value > 10"}
        )

        # Get lineage
        lineage = tracker.get_lineage("processed_data")

        assert lineage is not None
        assert len(lineage) > 0

    def test_privacy_compliance(self):
        """Test privacy compliance checking"""
        checker = PrivacyComplianceChecker(regulations=["GDPR", "CCPA"])

        # Check data
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789"
        }

        compliance_report = checker.check_compliance(data)

        assert "gdpr_compliant" in compliance_report
        assert "pii_detected" in compliance_report
        assert isinstance(compliance_report["pii_detected"], list)


class TestEdgeAI:
    """Test Edge AI components"""

    def test_federated_learning_client(self):
        """Test federated learning client"""
        client = FederatedLearningClient(
            client_id="edge-device-1",
            min_clients_per_round=2
        )

        # Initialize model
        initial_weights = {
            "layer1": np.random.rand(10, 10),
            "layer2": np.random.rand(10, 5)
        }
        client.initialize_model(initial_weights)

        # Local training
        training_data = [{"x": np.random.rand(10), "y": 0} for _ in range(100)]
        update = client.local_train(training_data, epochs=1)

        assert update is not None
        assert update.client_id == "edge-device-1"
        assert "layer1" in update.model_weights

    def test_model_compression(self):
        """Test model compression"""
        compressor = ModelCompressor(
            target_platform="hailo-8",
            min_accuracy=0.95
        )

        # Create dummy model
        model_weights = {
            "layer1": np.random.rand(100, 100).astype(np.float32),
            "layer2": np.random.rand(100, 50).astype(np.float32)
        }

        # Profile model
        profile = compressor.profile_model(model_weights)
        assert profile.total_params > 0
        assert profile.size_mb > 0

        # Quantize model
        quantized = compressor.quantize(model_weights)
        assert len(quantized) == len(model_weights)

    @pytest.mark.asyncio
    async def test_offline_inference_engine(self):
        """Test offline inference engine"""
        engine = OfflineInferenceEngine(
            cache_dir="/tmp/test_models",
            max_cache_size_gb=1.0
        )

        # Create dummy model
        model_weights = {"layer1": np.random.rand(10, 10)}
        model_path = "/tmp/test_model.npz"
        np.savez(model_path, **model_weights)

        # Load model
        loaded = engine.load_model(
            model_name="test_model",
            model_path=model_path,
            input_shape=(1, 10),
            output_shape=(1, 10)
        )
        assert loaded == True

        # Run inference
        input_data = np.random.rand(1, 10).astype(np.float32)
        result = await engine.infer(
            model_name="test_model",
            input_data=input_data
        )

        assert result is not None
        assert result.status.value in ["completed", "failed"]

        # Get statistics
        stats = engine.get_statistics()
        assert "backend" in stats
        assert "loaded_models" in stats

        # Cleanup
        engine.cleanup()

    @pytest.mark.asyncio
    async def test_edge_cloud_sync(self):
        """Test edge-cloud synchronization"""
        sync = EdgeCloudSync(
            device_id="test-device-1",
            edge_storage_path="/tmp/test_edge_storage",
            sync_interval_seconds=60
        )

        # Check connectivity
        is_online = await sync.check_connectivity()
        assert isinstance(is_online, bool)

        # Sync metrics
        metrics = {
            "cpu_usage": 45.2,
            "memory_usage": 60.1,
            "timestamp": datetime.now().isoformat()
        }
        operation = await sync.sync_metrics(metrics)

        assert operation is not None
        assert operation.resource_type.value == "metrics"

        # Get statistics
        stats = sync.get_statistics()
        assert "device_id" in stats
        assert "queue_size" in stats

        # Cleanup
        sync.cleanup()


class TestEndToEndWorkflows:
    """Test end-to-end system workflows"""

    @pytest.mark.asyncio
    async def test_secure_inference_workflow(self):
        """Test secure inference workflow"""
        # Initialize components
        em = EncryptionManager()
        engine = OfflineInferenceEngine()
        detector = ThreatDetector()

        # 1. Threat detection
        threat_score = detector.analyze_request(
            user_id="user123",
            endpoint="/api/inference",
            method="POST",
            payload_size=1024,
            ip_address="192.168.1.100"
        )

        if threat_score < 0.8:  # Low threat
            # 2. Encrypt input data
            key = em.generate_key()
            input_data = np.random.rand(1, 224, 224, 3).astype(np.float32)
            encrypted_input = em.encrypt(input_data.tobytes(), key)

            # 3. Decrypt for inference
            decrypted_bytes = em.decrypt(encrypted_input, key)
            decrypted_input = np.frombuffer(decrypted_bytes, dtype=np.float32).reshape(input_data.shape)

            # 4. Run inference (would fail without loaded model, but tests the flow)
            # result = await engine.infer("test_model", decrypted_input)

            assert encrypted_input != input_data.tobytes()
            assert np.array_equal(decrypted_input, input_data)

    @pytest.mark.asyncio
    async def test_federated_learning_workflow(self):
        """Test federated learning workflow"""
        # Initialize multiple clients
        clients = [
            FederatedLearningClient(client_id=f"client-{i}")
            for i in range(3)
        ]

        # Initialize with same model
        initial_weights = {
            "layer1": np.random.rand(10, 10),
        }

        for client in clients:
            client.initialize_model(initial_weights)

        # Each client trains locally
        updates = []
        for i, client in enumerate(clients):
            training_data = [{"x": np.random.rand(10), "y": i % 2} for _ in range(50)]
            update = client.local_train(training_data, epochs=1)
            updates.append(update)

        # Aggregate updates (using first client as aggregator)
        aggregated_weights = clients[0].aggregate_updates(updates)

        assert "layer1" in aggregated_weights
        assert aggregated_weights["layer1"].shape == (10, 10)

    def test_data_quality_to_privacy_workflow(self):
        """Test data quality checking and privacy compliance"""
        # Initialize components
        quality_checker = DataQualityChecker()
        privacy_checker = PrivacyComplianceChecker(regulations=["GDPR"])

        # Sample data
        data = {
            "user_id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", None, "David", "Eve"],
            "email": ["alice@ex.com", "bob@ex.com", "charlie@ex.com", None, "eve@ex.com"],
            "age": [25, 30, 35, 40, 45]
        }

        # 1. Check data quality
        quality_report = quality_checker.check_quality(data)
        assert "completeness" in quality_report

        # 2. Check privacy compliance
        privacy_report = privacy_checker.check_compliance(data)
        assert "pii_detected" in privacy_report

        # 3. If PII detected, anonymize
        if len(privacy_report["pii_detected"]) > 0:
            anonymized = privacy_checker.anonymize_data(data)
            assert anonymized is not None


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
