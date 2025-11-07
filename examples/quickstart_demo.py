"""
Prime Spark AI - Quickstart Demo

Demonstrates basic usage of all major components.
"""

import asyncio
import numpy as np
from datetime import datetime

# Import Prime Spark AI components
from prime_spark.intelligent_lb.router import IntelligentRouter
from prime_spark.security.encryption import EncryptionManager
from prime_spark.security.iam import IAMManager
from prime_spark.data_intelligence.quality_checker import DataQualityChecker
from prime_spark.data_intelligence.privacy_compliance import PrivacyComplianceChecker
from prime_spark.edge_ai.federated_learning import FederatedLearningClient
from prime_spark.edge_ai.model_compression import ModelCompressor
from prime_spark.edge_ai.offline_inference import OfflineInferenceEngine
from prime_spark.edge_ai.edge_cloud_sync import EdgeCloudSync


def demo_intelligent_load_balancing():
    """Demo: Intelligent Load Balancing"""
    print("\n" + "=" * 80)
    print("DEMO 1: Intelligent Load Balancing")
    print("=" * 80)

    # Initialize router with edge and cloud endpoints
    router = IntelligentRouter(
        edge_endpoints=["http://edge1:8000", "http://edge2:8000"],
        cloud_endpoints=["http://cloud1:8000", "http://cloud2:8000"]
    )

    # Route requests based on size and user location
    print("\n1. Routing small request from San Francisco:")
    endpoint = router.route_request(
        request_size_mb=0.5,
        priority="HIGH",
        user_location=(37.7749, -122.4194)  # San Francisco
    )
    print(f"   → Routed to: {endpoint}")

    print("\n2. Routing large request:")
    endpoint = router.route_request(
        request_size_mb=50.0,
        priority="MEDIUM"
    )
    print(f"   → Routed to: {endpoint}")

    print("\n3. Getting router statistics:")
    stats = router.get_statistics()
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Edge routing: {stats.get('edge_requests', 0)}")
    print(f"   Cloud routing: {stats.get('cloud_requests', 0)}")


def demo_security_framework():
    """Demo: Security Framework"""
    print("\n" + "=" * 80)
    print("DEMO 2: Security Framework")
    print("=" * 80)

    # Encryption
    print("\n1. Data Encryption:")
    em = EncryptionManager()

    key = em.generate_key()
    sensitive_data = b"User PII: SSN 123-45-6789"

    ciphertext = em.encrypt(sensitive_data, key)
    print(f"   Original: {sensitive_data.decode()}")
    print(f"   Encrypted: {ciphertext[:50]}... (truncated)")

    decrypted = em.decrypt(ciphertext, key)
    print(f"   Decrypted: {decrypted.decode()}")

    # IAM
    print("\n2. Identity and Access Management:")
    iam = IAMManager()

    user_id = iam.create_user("alice", "alice@example.com", roles=["user"])
    print(f"   Created user: alice (ID: {user_id})")

    has_read_permission = iam.check_permission(user_id, "data", "read")
    has_delete_permission = iam.check_permission(user_id, "data", "delete")

    print(f"   Can read data: {has_read_permission}")
    print(f"   Can delete data: {has_delete_permission}")


def demo_data_intelligence():
    """Demo: Data Intelligence"""
    print("\n" + "=" * 80)
    print("DEMO 3: Data Intelligence")
    print("=" * 80)

    # Data Quality Checking
    print("\n1. Data Quality Checking:")
    checker = DataQualityChecker()

    data = {
        "id": [1, 2, 3, 4, 5],
        "value": [10.5, 20.3, None, 40.1, 50.2],
        "category": ["A", "B", "A", "C", "B"],
        "timestamp": [datetime.now().isoformat()] * 5
    }

    report = checker.check_quality(data)
    print(f"   Completeness: {report['completeness'] * 100:.1f}%")
    print(f"   Validity: {report['validity'] * 100:.1f}%")
    print(f"   Issues: {len(report.get('issues', []))}")

    # Privacy Compliance
    print("\n2. Privacy Compliance (GDPR/CCPA):")
    privacy_checker = PrivacyComplianceChecker(regulations=["GDPR", "CCPA"])

    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-555-1234",
        "address": "123 Main St"
    }

    compliance_report = privacy_checker.check_compliance(user_data)
    print(f"   PII fields detected: {len(compliance_report['pii_detected'])}")
    print(f"   Fields: {', '.join(compliance_report['pii_detected'])}")

    # Anonymize
    anonymized = privacy_checker.anonymize_data(user_data)
    print(f"   Anonymized email: {anonymized.get('email', 'N/A')}")


def demo_federated_learning():
    """Demo: Federated Learning"""
    print("\n" + "=" * 80)
    print("DEMO 4: Federated Learning")
    print("=" * 80)

    print("\n1. Initializing 3 edge devices for federated learning:")

    # Create clients
    clients = []
    for i in range(3):
        client = FederatedLearningClient(
            client_id=f"device-{i+1}",
            enable_differential_privacy=True,
            privacy_epsilon=1.0
        )
        clients.append(client)
        print(f"   ✓ Device {i+1} initialized")

    # Initialize with same model
    print("\n2. Distributing initial model:")
    initial_weights = {
        "layer1": np.random.rand(10, 10),
        "layer2": np.random.rand(10, 5)
    }

    for client in clients:
        client.initialize_model(initial_weights)

    print("   ✓ All devices have initial model")

    # Local training
    print("\n3. Local training on each device:")
    updates = []

    for i, client in enumerate(clients):
        # Simulate local training data
        training_data = [
            {"x": np.random.rand(10), "y": i % 2}
            for _ in range(50)
        ]

        update = client.local_train(training_data, epochs=1)
        updates.append(update)

        print(f"   Device {i+1}: loss={update.loss:.4f}, accuracy={update.accuracy:.4f}")

    # Aggregate
    print("\n4. Aggregating model updates:")
    aggregated_weights = clients[0].aggregate_updates(updates)
    print(f"   ✓ Global model updated")

    # Get statistics
    for i, client in enumerate(clients):
        stats = client.get_client_statistics()
        print(f"   Device {i+1} privacy budget used: {stats['privacy_budget_used']:.2f}")


def demo_model_compression():
    """Demo: Model Compression"""
    print("\n" + "=" * 80)
    print("DEMO 5: Model Compression for Edge Deployment")
    print("=" * 80)

    compressor = ModelCompressor(
        target_platform="hailo-8",
        target_size_mb=10.0,
        min_accuracy=0.95
    )

    # Create sample model (25MB uncompressed)
    print("\n1. Creating model with 1M parameters:")
    model_weights = {
        "conv1": np.random.rand(64, 3, 7, 7).astype(np.float32),
        "conv2": np.random.rand(128, 64, 3, 3).astype(np.float32),
        "fc1": np.random.rand(1000, 4608).astype(np.float32),
        "fc2": np.random.rand(1000, 1000).astype(np.float32),
    }

    # Profile
    profile = compressor.profile_model(model_weights)
    print(f"   Parameters: {profile.total_params:,}")
    print(f"   Size: {profile.size_mb:.2f} MB")
    print(f"   FLOPs: {profile.flops / 1e9:.2f}G")

    # Compress
    print("\n2. Compressing model:")
    compressed, result = compressor.compress_pipeline(
        model_weights,
        techniques=[compressor.CompressionTechnique.PRUNING, compressor.CompressionTechnique.QUANTIZATION],
        original_accuracy=0.92
    )

    print(f"   Original size: {result.original_size_mb:.2f} MB")
    print(f"   Compressed size: {result.compressed_size_mb:.2f} MB")
    print(f"   Compression ratio: {result.compression_ratio:.2f}x")
    print(f"   Accuracy: {result.accuracy_original:.3f} → {result.accuracy_compressed:.3f}")
    print(f"   Inference speedup: {result.inference_speedup:.2f}x")


async def demo_offline_inference():
    """Demo: Offline Inference Engine"""
    print("\n" + "=" * 80)
    print("DEMO 6: Offline Inference on Edge Device")
    print("=" * 80)

    engine = OfflineInferenceEngine(
        cache_dir="/tmp/demo_models",
        enable_result_cache=True,
        preferred_backend=OfflineInferenceEngine.InferenceBackend.AUTO
    )

    print(f"\n1. Inference engine initialized")
    print(f"   Backend: {engine.active_backend.value}")
    print(f"   Hailo available: {engine.hailo_available}")

    # Create and load dummy model
    print("\n2. Loading model:")
    model_weights = {"layer1": np.random.rand(224, 224)}
    model_path = "/tmp/demo_model.npz"
    np.savez(model_path, **model_weights)

    loaded = engine.load_model(
        model_name="demo_classifier",
        model_path=model_path,
        input_shape=(1, 224, 224, 3),
        output_shape=(1, 1000)
    )

    if loaded:
        print("   ✓ Model loaded successfully")

        # Run inference
        print("\n3. Running inference:")
        input_data = np.random.rand(1, 224, 224, 3).astype(np.float32)

        result = await engine.infer("demo_classifier", input_data, priority=5)

        if result.status.value == "completed":
            print(f"   ✓ Inference completed")
            print(f"   Latency: {result.latency_ms:.2f} ms")
            print(f"   Backend used: {result.backend_used.value}")
            print(f"   Cached: {result.cached}")

        # Statistics
        print("\n4. Engine statistics:")
        stats = engine.get_statistics()
        print(f"   Total inferences: {stats['total_inferences']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate'] * 100:.1f}%")

    engine.cleanup()


async def demo_edge_cloud_sync():
    """Demo: Edge-Cloud Synchronization"""
    print("\n" + "=" * 80)
    print("DEMO 7: Edge-Cloud Synchronization")
    print("=" * 80)

    sync = EdgeCloudSync(
        device_id="demo-edge-device",
        edge_storage_path="/tmp/demo_edge_storage",
        cloud_endpoint="https://cloud.primespark.ai",
        sync_interval_seconds=300
    )

    # Check connectivity
    print("\n1. Checking cloud connectivity:")
    is_online = await sync.check_connectivity()
    print(f"   Status: {'Online' if is_online else 'Offline'}")

    # Sync model
    print("\n2. Syncing model to cloud:")
    model_path = "/tmp/demo_model.npz"
    operation = await sync.sync_model(
        model_id="classifier_v1",
        model_path=model_path,
        direction=sync.SyncDirection.EDGE_TO_CLOUD,
        priority=5
    )

    if operation:
        print(f"   ✓ Sync operation queued: {operation.operation_id}")
        print(f"   Status: {operation.status.value}")

    # Sync metrics
    print("\n3. Syncing device metrics:")
    metrics = {
        "cpu_usage": 45.2,
        "memory_usage": 60.1,
        "temperature": 55.0,
        "timestamp": datetime.now().isoformat()
    }

    await sync.sync_metrics(metrics)
    print("   ✓ Metrics queued for sync")

    # Statistics
    print("\n4. Sync statistics:")
    stats = sync.get_statistics()
    print(f"   Device: {stats['device_id']}")
    print(f"   Queue size: {stats['queue_size']}")
    print(f"   Total syncs: {stats['total_syncs']}")
    print(f"   Tracked resources: {stats['tracked_resources']}")

    sync.cleanup()


async def main():
    """Run all demos"""
    print("=" * 80)
    print("PRIME SPARK AI - COMPREHENSIVE QUICKSTART DEMO")
    print("=" * 80)
    print("\nThis demo showcases all major components of Prime Spark AI:")
    print("  1. Intelligent Load Balancing")
    print("  2. Security Framework")
    print("  3. Data Intelligence")
    print("  4. Federated Learning")
    print("  5. Model Compression")
    print("  6. Offline Inference")
    print("  7. Edge-Cloud Synchronization")

    input("\nPress Enter to start the demos...")

    # Run demos
    demo_intelligent_load_balancing()
    input("\nPress Enter to continue...")

    demo_security_framework()
    input("\nPress Enter to continue...")

    demo_data_intelligence()
    input("\nPress Enter to continue...")

    demo_federated_learning()
    input("\nPress Enter to continue...")

    demo_model_compression()
    input("\nPress Enter to continue...")

    await demo_offline_inference()
    input("\nPress Enter to continue...")

    await demo_edge_cloud_sync()

    print("\n" + "=" * 80)
    print("DEMOS COMPLETE")
    print("=" * 80)
    print("\nFor more information:")
    print("  - Documentation: /home/pironman5/prime-spark-ai/docs/")
    print("  - Examples: /home/pironman5/prime-spark-ai/examples/")
    print("  - Tests: /home/pironman5/prime-spark-ai/tests/")


if __name__ == "__main__":
    asyncio.run(main())
