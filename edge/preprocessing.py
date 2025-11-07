"""
Edge Data Preprocessing Pipeline
Handles data preprocessing before inference or cloud sync
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Supported data types"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    SENSOR = "sensor"
    TELEMETRY = "telemetry"


@dataclass
class PreprocessingConfig:
    """Preprocessing configuration"""
    resize_dims: Optional[tuple] = None
    normalize: bool = True
    augment: bool = False
    compress: bool = True
    quality: int = 85
    batch_size: int = 32


class ImagePreprocessor:
    """Image preprocessing pipeline"""

    @staticmethod
    async def preprocess(data: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Preprocess image data"""
        # Resize if specified
        if config.resize_dims:
            # TODO: Implement actual resize (OpenCV)
            pass

        # Normalize
        if config.normalize:
            data = data.astype(np.float32) / 255.0

        return data

    @staticmethod
    async def batch_preprocess(data_list: List[np.ndarray],
                               config: PreprocessingConfig) -> List[np.ndarray]:
        """Batch preprocess images"""
        results = []
        for i in range(0, len(data_list), config.batch_size):
            batch = data_list[i:i + config.batch_size]
            processed = await asyncio.gather(*[
                ImagePreprocessor.preprocess(d, config) for d in batch
            ])
            results.extend(processed)
        return results


class AudioPreprocessor:
    """Audio preprocessing pipeline"""

    @staticmethod
    async def preprocess(data: np.ndarray, config: PreprocessingConfig) -> np.ndarray:
        """Preprocess audio data"""
        # Apply noise reduction
        # TODO: Implement actual audio preprocessing

        # Normalize audio
        if config.normalize:
            data = data / np.max(np.abs(data))

        return data

    @staticmethod
    async def extract_features(data: np.ndarray) -> Dict[str, Any]:
        """Extract audio features (MFCC, spectral, etc.)"""
        # TODO: Implement feature extraction
        return {
            "mfcc": [],
            "spectral_centroid": 0.0,
            "zero_crossing_rate": 0.0
        }


class SensorPreprocessor:
    """Sensor data preprocessing"""

    @staticmethod
    async def preprocess(data: Dict[str, Any], config: PreprocessingConfig) -> Dict[str, Any]:
        """Preprocess sensor data"""
        processed = {}

        for key, value in data.items():
            if isinstance(value, (int, float)):
                # Normalize numeric values
                if config.normalize:
                    processed[key] = value  # TODO: Implement normalization
                else:
                    processed[key] = value
            else:
                processed[key] = value

        return processed

    @staticmethod
    async def aggregate(data_points: List[Dict[str, Any]],
                       window_size: int = 10) -> Dict[str, Any]:
        """Aggregate sensor readings over time window"""
        if not data_points:
            return {}

        aggregated = {}
        numeric_keys = [k for k, v in data_points[0].items()
                       if isinstance(v, (int, float))]

        for key in numeric_keys:
            values = [d[key] for d in data_points if key in d]
            aggregated[key] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "count": len(values)
            }

        return aggregated


class EdgePreprocessingPipeline:
    """Main preprocessing pipeline manager"""

    def __init__(self):
        self.image_processor = ImagePreprocessor()
        self.audio_processor = AudioPreprocessor()
        self.sensor_processor = SensorPreprocessor()
        self.stats = {
            "total_processed": 0,
            "by_type": {},
            "total_latency_ms": 0
        }

    async def preprocess(self, data: Any, data_type: DataType,
                        config: Optional[PreprocessingConfig] = None) -> Any:
        """Preprocess data based on type"""
        start_time = datetime.now()

        if config is None:
            config = PreprocessingConfig()

        # Route to appropriate processor
        if data_type == DataType.IMAGE:
            result = await self.image_processor.preprocess(data, config)
        elif data_type == DataType.AUDIO:
            result = await self.audio_processor.preprocess(data, config)
        elif data_type == DataType.SENSOR:
            result = await self.sensor_processor.preprocess(data, config)
        else:
            result = data  # Pass through

        # Update stats
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        self._update_stats(data_type, latency_ms)

        return result

    async def batch_preprocess(self, data_list: List[Any], data_type: DataType,
                              config: Optional[PreprocessingConfig] = None) -> List[Any]:
        """Batch preprocess multiple items"""
        if config is None:
            config = PreprocessingConfig()

        if data_type == DataType.IMAGE:
            return await self.image_processor.batch_preprocess(data_list, config)
        else:
            # Process individually for other types
            return await asyncio.gather(*[
                self.preprocess(d, data_type, config) for d in data_list
            ])

    def _update_stats(self, data_type: DataType, latency_ms: float):
        """Update preprocessing statistics"""
        self.stats["total_processed"] += 1
        self.stats["total_latency_ms"] += latency_ms

        type_key = data_type.value
        if type_key not in self.stats["by_type"]:
            self.stats["by_type"][type_key] = {"count": 0, "total_latency_ms": 0}

        self.stats["by_type"][type_key]["count"] += 1
        self.stats["by_type"][type_key]["total_latency_ms"] += latency_ms

    def get_stats(self) -> Dict[str, Any]:
        """Get preprocessing statistics"""
        stats = {
            **self.stats,
            "average_latency_ms": (
                self.stats["total_latency_ms"] / self.stats["total_processed"]
                if self.stats["total_processed"] > 0 else 0
            )
        }

        # Add per-type averages
        for type_key, type_stats in self.stats["by_type"].items():
            type_stats["average_latency_ms"] = (
                type_stats["total_latency_ms"] / type_stats["count"]
            )

        return stats


# Global preprocessing pipeline
_preprocessing_pipeline = None

def get_preprocessing_pipeline() -> EdgePreprocessingPipeline:
    """Get global preprocessing pipeline instance"""
    global _preprocessing_pipeline
    if _preprocessing_pipeline is None:
        _preprocessing_pipeline = EdgePreprocessingPipeline()
    return _preprocessing_pipeline
