"""
Prime Spark AI - Edge AI Capabilities

Edge AI framework optimized for Raspberry Pi 5 with Hailo-8 accelerator,
featuring federated learning, model compression, offline inference, and edge-cloud sync.
"""

from .federated_learning import FederatedLearningClient
from .model_compression import ModelCompressor
from .offline_inference import OfflineInferenceEngine
from .edge_cloud_sync import EdgeCloudSync

__all__ = [
    'FederatedLearningClient',
    'ModelCompressor',
    'OfflineInferenceEngine',
    'EdgeCloudSync',
]
