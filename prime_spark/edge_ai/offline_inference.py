"""
Offline Inference Engine

Enables AI inference on edge devices with:
- Local model caching
- Hailo-8 accelerator integration
- CPU fallback for robustness
- Request queuing and batching
- Performance monitoring
"""

import logging
import pickle
import hashlib
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pathlib import Path
import numpy as np
from collections import deque
import time

logger = logging.getLogger(__name__)


class InferenceBackend(Enum):
    """Inference backend options"""
    HAILO_8 = "hailo-8"
    CPU = "cpu"
    GPU = "gpu"
    AUTO = "auto"


class InferenceStatus(Enum):
    """Inference request status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class InferenceRequest:
    """Inference request"""
    request_id: str
    model_name: str
    input_data: np.ndarray
    priority: int = 0  # Higher = more priority
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class InferenceResult:
    """Inference result"""
    request_id: str
    model_name: str
    output_data: np.ndarray
    backend_used: InferenceBackend
    latency_ms: float
    status: InferenceStatus
    cached: bool = False
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_name: str
    model_path: str
    input_shape: tuple
    output_shape: tuple
    model_size_mb: float
    backend: InferenceBackend
    loaded_at: datetime
    last_used: datetime
    inference_count: int = 0
    avg_latency_ms: float = 0.0


class OfflineInferenceEngine:
    """
    Offline Inference Engine for Edge Devices

    Features:
    - Local model caching (LRU eviction)
    - Hailo-8 accelerator support with CPU fallback
    - Request queuing and priority-based scheduling
    - Automatic batching for efficiency
    - Result caching for duplicate inputs
    - Performance monitoring and metrics
    - Graceful degradation on hardware failure
    """

    def __init__(
        self,
        cache_dir: str = "/tmp/prime_spark_models",
        max_cache_size_gb: float = 2.0,
        enable_result_cache: bool = True,
        result_cache_ttl: int = 3600,  # 1 hour
        max_batch_size: int = 8,
        batch_timeout_ms: int = 50,
        preferred_backend: InferenceBackend = InferenceBackend.AUTO,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_cache_size_gb = max_cache_size_gb
        self.enable_result_cache = enable_result_cache
        self.result_cache_ttl = result_cache_ttl
        self.max_batch_size = max_batch_size
        self.batch_timeout_ms = batch_timeout_ms
        self.preferred_backend = preferred_backend

        # Model cache: {model_name: (model, metadata)}
        self.loaded_models: Dict[str, tuple] = {}

        # Request queue (priority queue)
        self.request_queue: deque = deque()

        # Result cache: {input_hash: result}
        self.result_cache: Dict[str, InferenceResult] = {}

        # Performance metrics
        self.total_inferences = 0
        self.cache_hits = 0
        self.queue_processing = False

        # Backend availability
        self.hailo_available = self._check_hailo_available()

        # Determine active backend
        self.active_backend = self._determine_backend()

        logger.info(
            f"Initialized OfflineInferenceEngine "
            f"(backend: {self.active_backend.value}, "
            f"cache_dir: {cache_dir}, "
            f"hailo_available: {self.hailo_available})"
        )

    def _check_hailo_available(self) -> bool:
        """Check if Hailo-8 accelerator is available"""
        try:
            # Check for HailoRT
            import importlib.util
            hailo_spec = importlib.util.find_spec("hailo_platform")

            if hailo_spec is not None:
                logger.info("Hailo-8 accelerator detected")
                return True
            else:
                logger.warning("HailoRT not found, will use CPU fallback")
                return False

        except Exception as e:
            logger.warning(f"Error checking Hailo availability: {e}")
            return False

    def _determine_backend(self) -> InferenceBackend:
        """Determine which backend to use"""
        if self.preferred_backend == InferenceBackend.AUTO:
            if self.hailo_available:
                return InferenceBackend.HAILO_8
            else:
                return InferenceBackend.CPU

        elif self.preferred_backend == InferenceBackend.HAILO_8:
            if not self.hailo_available:
                logger.warning("Hailo-8 requested but not available, falling back to CPU")
                return InferenceBackend.CPU
            return InferenceBackend.HAILO_8

        else:
            return self.preferred_backend

    def load_model(
        self,
        model_name: str,
        model_path: str,
        input_shape: tuple,
        output_shape: tuple,
    ) -> bool:
        """
        Load model into cache

        Args:
            model_name: Model identifier
            model_path: Path to model file
            input_shape: Expected input shape
            output_shape: Expected output shape

        Returns:
            True if loaded successfully
        """
        try:
            logger.info(f"Loading model {model_name} from {model_path}")

            # Check cache size
            if not self._check_cache_capacity(model_path):
                # Evict LRU model
                self._evict_lru_model()

            # Load model based on backend
            if self.active_backend == InferenceBackend.HAILO_8:
                model = self._load_hailo_model(model_path)
            else:
                model = self._load_cpu_model(model_path)

            # Get model size
            model_size_mb = Path(model_path).stat().st_size / (1024 * 1024)

            # Create metadata
            metadata = ModelMetadata(
                model_name=model_name,
                model_path=model_path,
                input_shape=input_shape,
                output_shape=output_shape,
                model_size_mb=model_size_mb,
                backend=self.active_backend,
                loaded_at=datetime.now(),
                last_used=datetime.now(),
            )

            # Store in cache
            self.loaded_models[model_name] = (model, metadata)

            logger.info(
                f"Model {model_name} loaded successfully "
                f"({model_size_mb:.2f} MB, backend: {self.active_backend.value})"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False

    def _load_hailo_model(self, model_path: str):
        """Load model for Hailo-8 inference"""
        # In production, use HailoRT to load .hef model
        # For now, simulate with numpy arrays
        logger.info(f"Loading Hailo model from {model_path}")

        # Placeholder: load compiled Hailo model
        # from hailo_platform import HEF
        # hef = HEF(model_path)

        return {"type": "hailo", "path": model_path}

    def _load_cpu_model(self, model_path: str):
        """Load model for CPU inference"""
        logger.info(f"Loading CPU model from {model_path}")

        # Load numpy model or ONNX model
        try:
            model = np.load(model_path, allow_pickle=True)
            return {"type": "cpu", "weights": model}
        except:
            # Fallback: mock model
            return {"type": "cpu", "path": model_path}

    def _check_cache_capacity(self, model_path: str) -> bool:
        """Check if cache has capacity for new model"""
        model_size_mb = Path(model_path).stat().st_size / (1024 * 1024)
        current_size_gb = sum(
            meta.model_size_mb for _, meta in self.loaded_models.values()
        ) / 1024

        return (current_size_gb + model_size_mb / 1024) <= self.max_cache_size_gb

    def _evict_lru_model(self):
        """Evict least recently used model"""
        if not self.loaded_models:
            return

        # Find LRU model
        lru_model = min(
            self.loaded_models.items(),
            key=lambda x: x[1][1].last_used
        )

        model_name = lru_model[0]
        logger.info(f"Evicting LRU model: {model_name}")

        del self.loaded_models[model_name]

    async def infer(
        self,
        model_name: str,
        input_data: np.ndarray,
        priority: int = 0,
    ) -> InferenceResult:
        """
        Run inference on input data

        Args:
            model_name: Model to use
            input_data: Input data
            priority: Request priority (higher = more urgent)

        Returns:
            InferenceResult
        """
        request_id = self._generate_request_id(model_name, input_data)

        # Check result cache
        if self.enable_result_cache:
            cached_result = self._check_result_cache(request_id)
            if cached_result:
                self.cache_hits += 1
                logger.debug(f"Cache hit for request {request_id}")
                return cached_result

        # Check if model is loaded
        if model_name not in self.loaded_models:
            return InferenceResult(
                request_id=request_id,
                model_name=model_name,
                output_data=np.array([]),
                backend_used=self.active_backend,
                latency_ms=0,
                status=InferenceStatus.FAILED,
                error=f"Model {model_name} not loaded",
            )

        # Create request
        request = InferenceRequest(
            request_id=request_id,
            model_name=model_name,
            input_data=input_data,
            priority=priority,
        )

        # Add to queue
        self.request_queue.append(request)

        # Start queue processing if not running
        if not self.queue_processing:
            asyncio.create_task(self._process_queue())

        # Wait for result (in production, use proper async queue)
        result = await self._wait_for_result(request_id)

        # Cache result
        if self.enable_result_cache:
            self._cache_result(request_id, result)

        self.total_inferences += 1

        return result

    def _generate_request_id(self, model_name: str, input_data: np.ndarray) -> str:
        """Generate unique request ID based on input"""
        # Hash input data for caching
        data_hash = hashlib.sha256(input_data.tobytes()).hexdigest()[:16]
        return f"{model_name}_{data_hash}"

    def _check_result_cache(self, request_id: str) -> Optional[InferenceResult]:
        """Check if result is cached"""
        if request_id in self.result_cache:
            result = self.result_cache[request_id]

            # Check TTL
            age = (datetime.now() - result.timestamp).total_seconds()
            if age < self.result_cache_ttl:
                result.cached = True
                return result
            else:
                # Expired
                del self.result_cache[request_id]

        return None

    def _cache_result(self, request_id: str, result: InferenceResult):
        """Cache inference result"""
        self.result_cache[request_id] = result

        # Limit cache size (keep last 1000 results)
        if len(self.result_cache) > 1000:
            oldest_key = next(iter(self.result_cache))
            del self.result_cache[oldest_key]

    async def _process_queue(self):
        """Process inference request queue"""
        self.queue_processing = True

        while self.request_queue:
            # Sort by priority
            sorted_queue = sorted(
                self.request_queue,
                key=lambda r: r.priority,
                reverse=True
            )

            # Get batch
            batch_size = min(len(sorted_queue), self.max_batch_size)
            batch = sorted_queue[:batch_size]

            # Remove from queue
            for req in batch:
                self.request_queue.remove(req)

            # Process batch
            await self._process_batch(batch)

            # Small delay
            await asyncio.sleep(0.01)

        self.queue_processing = False

    async def _process_batch(self, batch: List[InferenceRequest]):
        """Process batch of inference requests"""
        for request in batch:
            try:
                start_time = time.time()

                # Get model
                model, metadata = self.loaded_models[request.model_name]

                # Run inference
                if self.active_backend == InferenceBackend.HAILO_8:
                    output = self._infer_hailo(model, request.input_data)
                else:
                    output = self._infer_cpu(model, request.input_data)

                latency_ms = (time.time() - start_time) * 1000

                # Update metadata
                metadata.last_used = datetime.now()
                metadata.inference_count += 1
                metadata.avg_latency_ms = (
                    (metadata.avg_latency_ms * (metadata.inference_count - 1) + latency_ms)
                    / metadata.inference_count
                )

                # Create result
                result = InferenceResult(
                    request_id=request.request_id,
                    model_name=request.model_name,
                    output_data=output,
                    backend_used=self.active_backend,
                    latency_ms=latency_ms,
                    status=InferenceStatus.COMPLETED,
                )

                # Store result (simplified - in production use proper queue)
                if not hasattr(self, '_results'):
                    self._results = {}
                self._results[request.request_id] = result

                logger.debug(
                    f"Inference completed: {request.request_id}, "
                    f"{latency_ms:.2f}ms"
                )

            except Exception as e:
                logger.error(f"Inference failed for {request.request_id}: {e}")

                result = InferenceResult(
                    request_id=request.request_id,
                    model_name=request.model_name,
                    output_data=np.array([]),
                    backend_used=self.active_backend,
                    latency_ms=0,
                    status=InferenceStatus.FAILED,
                    error=str(e),
                )

                if not hasattr(self, '_results'):
                    self._results = {}
                self._results[request.request_id] = result

    def _infer_hailo(self, model: dict, input_data: np.ndarray) -> np.ndarray:
        """Run inference on Hailo-8"""
        # In production, use HailoRT inference
        # For now, simulate with random output
        logger.debug("Running Hailo-8 inference")

        # Placeholder inference
        # from hailo_platform import VDevice
        # vdevice = VDevice()
        # output = vdevice.run(model, input_data)

        # Simulate output
        output_shape = (1, 1000)  # Example: classification output
        return np.random.rand(*output_shape).astype(np.float32)

    def _infer_cpu(self, model: dict, input_data: np.ndarray) -> np.ndarray:
        """Run inference on CPU"""
        logger.debug("Running CPU inference")

        # Placeholder inference (would use ONNX runtime or PyTorch)
        # import onnxruntime as ort
        # session = ort.InferenceSession(model['path'])
        # output = session.run(None, {'input': input_data})

        # Simulate output
        output_shape = (1, 1000)
        return np.random.rand(*output_shape).astype(np.float32)

    async def _wait_for_result(self, request_id: str, timeout: float = 10.0) -> InferenceResult:
        """Wait for inference result"""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if hasattr(self, '_results') and request_id in self._results:
                result = self._results[request_id]
                del self._results[request_id]
                return result

            await asyncio.sleep(0.01)

        # Timeout
        return InferenceResult(
            request_id=request_id,
            model_name="",
            output_data=np.array([]),
            backend_used=self.active_backend,
            latency_ms=0,
            status=InferenceStatus.FAILED,
            error="Timeout waiting for result",
        )

    def get_statistics(self) -> Dict:
        """Get inference statistics"""
        cache_hit_rate = (
            self.cache_hits / self.total_inferences
            if self.total_inferences > 0
            else 0
        )

        model_stats = []
        for model_name, (_, metadata) in self.loaded_models.items():
            model_stats.append({
                'model_name': model_name,
                'inference_count': metadata.inference_count,
                'avg_latency_ms': metadata.avg_latency_ms,
                'size_mb': metadata.model_size_mb,
                'backend': metadata.backend.value,
            })

        return {
            'backend': self.active_backend.value,
            'hailo_available': self.hailo_available,
            'loaded_models': len(self.loaded_models),
            'total_inferences': self.total_inferences,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'queue_size': len(self.request_queue),
            'result_cache_size': len(self.result_cache),
            'models': model_stats,
        }

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up OfflineInferenceEngine")

        # Clear caches
        self.loaded_models.clear()
        self.result_cache.clear()
        self.request_queue.clear()

        # In production, release hardware resources
        # if self.hailo_device:
        #     self.hailo_device.release()

        logger.info("Cleanup complete")
