"""
Performance Benchmark Suite for Prime Spark AI

Comprehensive performance testing of all major components.
Target metrics:
- KVA storage: <10ms p95 latency
- Analytics queries: <100ms for basic queries
- Load balancing routing: <5ms
- Encryption/decryption: <50ms overhead
- Data quality checks: <100ms
- Edge AI inference: <50ms on Hailo-8
"""

import time
import asyncio
import numpy as np
from datetime import datetime
from typing import List, Dict
import statistics

# Import components to benchmark
from prime_spark.intelligent_lb.router import IntelligentRouter
from prime_spark.security.encryption import EncryptionManager
from prime_spark.data_intelligence.quality_checker import DataQualityChecker
from prime_spark.edge_ai.offline_inference import OfflineInferenceEngine
from prime_spark.edge_ai.model_compression import ModelCompressor


class BenchmarkResult:
    """Store benchmark results"""

    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.errors: List[str] = []

    def add_measurement(self, latency_ms: float):
        """Add latency measurement"""
        self.latencies.append(latency_ms)

    def add_error(self, error: str):
        """Add error"""
        self.errors.append(error)

    def get_statistics(self) -> Dict:
        """Calculate statistics"""
        if not self.latencies:
            return {
                "name": self.name,
                "count": 0,
                "errors": len(self.errors),
                "status": "FAILED"
            }

        return {
            "name": self.name,
            "count": len(self.latencies),
            "min_ms": min(self.latencies),
            "max_ms": max(self.latencies),
            "mean_ms": statistics.mean(self.latencies),
            "median_ms": statistics.median(self.latencies),
            "p95_ms": np.percentile(self.latencies, 95),
            "p99_ms": np.percentile(self.latencies, 99),
            "errors": len(self.errors),
            "status": "PASS" if len(self.errors) == 0 else "FAILED"
        }


class PerformanceBenchmarkSuite:
    """Performance benchmark suite"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def benchmark_load_balancing_routing(self, iterations: int = 1000):
        """Benchmark load balancing routing decisions (target: <5ms)"""
        print(f"\n=== Benchmarking Load Balancing Routing ({iterations} iterations) ===")

        result = BenchmarkResult("LoadBalancing-Routing")

        router = IntelligentRouter(
            edge_endpoints=["http://edge1:8000", "http://edge2:8000"],
            cloud_endpoints=["http://cloud1:8000", "http://cloud2:8000"]
        )

        for i in range(iterations):
            try:
                start = time.time()

                # Route decision
                endpoint = router.route_request(
                    request_size_mb=1.0,
                    priority="MEDIUM",
                    user_location=(37.7749, -122.4194)
                )

                latency_ms = (time.time() - start) * 1000
                result.add_measurement(latency_ms)

                if i % 100 == 0:
                    print(f"  Progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result.add_error(str(e))

        self.results.append(result)
        self._print_result(result, target_p95_ms=5.0)

    def benchmark_encryption_operations(self, iterations: int = 1000):
        """Benchmark encryption/decryption (target: <50ms overhead)"""
        print(f"\n=== Benchmarking Encryption Operations ({iterations} iterations) ===")

        em = EncryptionManager()
        key = em.generate_key()

        # Test data (1KB)
        data = b"x" * 1024

        # Benchmark encryption
        result_encrypt = BenchmarkResult("Encryption-1KB")

        for i in range(iterations):
            try:
                start = time.time()
                ciphertext = em.encrypt(data, key)
                latency_ms = (time.time() - start) * 1000
                result_encrypt.add_measurement(latency_ms)

                if i % 100 == 0:
                    print(f"  Encryption progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result_encrypt.add_error(str(e))

        self.results.append(result_encrypt)
        self._print_result(result_encrypt, target_p95_ms=50.0)

        # Benchmark decryption
        ciphertext = em.encrypt(data, key)
        result_decrypt = BenchmarkResult("Decryption-1KB")

        for i in range(iterations):
            try:
                start = time.time()
                plaintext = em.decrypt(ciphertext, key)
                latency_ms = (time.time() - start) * 1000
                result_decrypt.add_measurement(latency_ms)

                if i % 100 == 0:
                    print(f"  Decryption progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result_decrypt.add_error(str(e))

        self.results.append(result_decrypt)
        self._print_result(result_decrypt, target_p95_ms=50.0)

    def benchmark_data_quality_checks(self, iterations: int = 500):
        """Benchmark data quality checks (target: <100ms)"""
        print(f"\n=== Benchmarking Data Quality Checks ({iterations} iterations) ===")

        checker = DataQualityChecker()

        # Sample data (100 rows)
        data = {
            "id": list(range(100)),
            "value": [float(i) if i % 10 != 0 else None for i in range(100)],
            "category": ["A", "B", "C"] * 33 + ["A"],
            "timestamp": [datetime.now().isoformat()] * 100
        }

        result = BenchmarkResult("DataQuality-100rows")

        for i in range(iterations):
            try:
                start = time.time()
                report = checker.check_quality(data)
                latency_ms = (time.time() - start) * 1000
                result.add_measurement(latency_ms)

                if i % 50 == 0:
                    print(f"  Progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result.add_error(str(e))

        self.results.append(result)
        self._print_result(result, target_p95_ms=100.0)

    def benchmark_model_compression(self, iterations: int = 100):
        """Benchmark model compression operations"""
        print(f"\n=== Benchmarking Model Compression ({iterations} iterations) ===")

        compressor = ModelCompressor(target_platform="hailo-8")

        # Create model (1M parameters)
        model_weights = {
            "layer1": np.random.rand(500, 500).astype(np.float32),
            "layer2": np.random.rand(500, 500).astype(np.float32),
            "layer3": np.random.rand(500, 500).astype(np.float32),
            "layer4": np.random.rand(500, 500).astype(np.float32),
        }

        # Benchmark profiling
        result_profile = BenchmarkResult("ModelCompression-Profile")

        for i in range(iterations):
            try:
                start = time.time()
                profile = compressor.profile_model(model_weights)
                latency_ms = (time.time() - start) * 1000
                result_profile.add_measurement(latency_ms)

                if i % 10 == 0:
                    print(f"  Profile progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result_profile.add_error(str(e))

        self.results.append(result_profile)
        self._print_result(result_profile, target_p95_ms=500.0)

        # Benchmark quantization
        result_quant = BenchmarkResult("ModelCompression-Quantize")

        for i in range(iterations):
            try:
                start = time.time()
                quantized = compressor.quantize(model_weights)
                latency_ms = (time.time() - start) * 1000
                result_quant.add_measurement(latency_ms)

                if i % 10 == 0:
                    print(f"  Quantization progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result_quant.add_error(str(e))

        self.results.append(result_quant)
        self._print_result(result_quant, target_p95_ms=2000.0)

    async def benchmark_edge_inference(self, iterations: int = 100):
        """Benchmark edge AI inference (target: <50ms on Hailo-8)"""
        print(f"\n=== Benchmarking Edge AI Inference ({iterations} iterations) ===")

        engine = OfflineInferenceEngine(
            cache_dir="/tmp/bench_models",
            enable_result_cache=False  # Disable cache for accurate benchmarking
        )

        # Create and load dummy model
        model_weights = {"layer1": np.random.rand(224, 224)}
        model_path = "/tmp/bench_model.npz"
        np.savez(model_path, **model_weights)

        loaded = engine.load_model(
            model_name="bench_model",
            model_path=model_path,
            input_shape=(1, 224, 224, 3),
            output_shape=(1, 1000)
        )

        if not loaded:
            print("  ERROR: Failed to load model")
            return

        result = BenchmarkResult(f"EdgeInference-{engine.active_backend.value}")

        # Warm up
        for _ in range(10):
            input_data = np.random.rand(1, 224, 224, 3).astype(np.float32)
            await engine.infer("bench_model", input_data, priority=0)

        # Benchmark
        for i in range(iterations):
            try:
                input_data = np.random.rand(1, 224, 224, 3).astype(np.float32)

                start = time.time()
                inference_result = await engine.infer("bench_model", input_data, priority=0)
                latency_ms = (time.time() - start) * 1000

                if inference_result.status.value == "completed":
                    result.add_measurement(latency_ms)
                else:
                    result.add_error(f"Inference failed: {inference_result.error}")

                if i % 10 == 0:
                    print(f"  Progress: {i}/{iterations} (current: {latency_ms:.2f}ms)")

            except Exception as e:
                result.add_error(str(e))

        self.results.append(result)

        # Target depends on backend
        target_ms = 50.0 if engine.active_backend.value == "hailo-8" else 200.0
        self._print_result(result, target_p95_ms=target_ms)

        # Cleanup
        engine.cleanup()

    def benchmark_concurrent_operations(self, iterations: int = 100):
        """Benchmark concurrent operations"""
        print(f"\n=== Benchmarking Concurrent Operations ({iterations} concurrent requests) ===")

        result = BenchmarkResult("Concurrent-Operations")

        async def concurrent_work():
            tasks = []

            for i in range(iterations):
                # Simulate concurrent load balancing decisions
                router = IntelligentRouter(
                    edge_endpoints=["http://edge1:8000"],
                    cloud_endpoints=["http://cloud1:8000"]
                )

                async def route_task():
                    start = time.time()
                    endpoint = router.route_request(
                        request_size_mb=1.0,
                        priority="MEDIUM"
                    )
                    return (time.time() - start) * 1000

                tasks.append(route_task())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for latency in results:
                if isinstance(latency, Exception):
                    result.add_error(str(latency))
                else:
                    result.add_measurement(latency)

        asyncio.run(concurrent_work())

        self.results.append(result)
        self._print_result(result, target_p95_ms=50.0)

    def _print_result(self, result: BenchmarkResult, target_p95_ms: float):
        """Print benchmark result"""
        stats = result.get_statistics()

        print(f"\n  Results for {stats['name']}:")
        print(f"    Iterations: {stats['count']}")

        if stats['count'] > 0:
            print(f"    Min:    {stats['min_ms']:.2f} ms")
            print(f"    Mean:   {stats['mean_ms']:.2f} ms")
            print(f"    Median: {stats['median_ms']:.2f} ms")
            print(f"    P95:    {stats['p95_ms']:.2f} ms (target: {target_p95_ms:.2f} ms)")
            print(f"    P99:    {stats['p99_ms']:.2f} ms")
            print(f"    Max:    {stats['max_ms']:.2f} ms")

            # Check if target met
            if stats['p95_ms'] <= target_p95_ms:
                print(f"    Status: ✓ PASS (within target)")
            else:
                print(f"    Status: ✗ FAIL (exceeds target by {stats['p95_ms'] - target_p95_ms:.2f} ms)")

        if stats['errors'] > 0:
            print(f"    Errors: {stats['errors']}")

    def generate_report(self) -> Dict:
        """Generate comprehensive benchmark report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_benchmarks": len(self.results),
                "passed": sum(1 for r in self.results if r.get_statistics()["status"] == "PASS"),
                "failed": sum(1 for r in self.results if r.get_statistics()["status"] == "FAILED"),
            },
            "benchmarks": []
        }

        for result in self.results:
            report["benchmarks"].append(result.get_statistics())

        return report

    def print_summary(self):
        """Print summary of all benchmarks"""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        for result in self.results:
            stats = result.get_statistics()
            status_icon = "✓" if stats["status"] == "PASS" else "✗"
            print(f"{status_icon} {stats['name']}: P95={stats.get('p95_ms', 'N/A')} ms")

        report = self.generate_report()
        print(f"\nTotal: {report['summary']['total_benchmarks']} benchmarks")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")

        pass_rate = (report['summary']['passed'] / report['summary']['total_benchmarks']) * 100
        print(f"Pass Rate: {pass_rate:.1f}%")


async def run_all_benchmarks():
    """Run all performance benchmarks"""
    print("=" * 80)
    print("PRIME SPARK AI - PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)

    suite = PerformanceBenchmarkSuite()

    # Run benchmarks
    suite.benchmark_load_balancing_routing(iterations=1000)
    suite.benchmark_encryption_operations(iterations=1000)
    suite.benchmark_data_quality_checks(iterations=500)
    suite.benchmark_model_compression(iterations=100)
    await suite.benchmark_edge_inference(iterations=100)
    suite.benchmark_concurrent_operations(iterations=100)

    # Print summary
    suite.print_summary()

    # Generate and save report
    report = suite.generate_report()

    # Save to file
    import json
    report_path = "/home/pironman5/prime-spark-ai/completion_reports/performance_benchmarks.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_path}")

    return suite


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
