"""
AI Model Deployment Pipeline
Manages model deployment from training to production
"""
import mlflow
import mlflow.pytorch
import mlflow.onnx
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import torch
import onnx

logger = logging.getLogger(__name__)


class ModelDeployer:
    """
    Manages AI model lifecycle with MLflow.

    Features:
    - Model versioning
    - Experiment tracking
    - Model registry
    - Deployment to edge/cloud
    - ONNX export for optimization
    """

    def __init__(
        self,
        mlflow_tracking_uri: str = "http://localhost:5000",
        experiment_name: str = "prime-spark-ai"
    ):
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.experiment_name = experiment_name

        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)

    def log_model(
        self,
        model: Any,
        model_name: str,
        framework: str = "pytorch",
        artifacts: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, float]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log model to MLflow.

        Args:
            model: Model object
            model_name: Name for the model
            framework: Framework type (pytorch, tensorflow, onnx)
            artifacts: Additional artifacts to log
            metrics: Metrics to log
            params: Parameters to log

        Returns:
            Run ID
        """
        with mlflow.start_run(run_name=model_name) as run:
            # Log parameters
            if params:
                mlflow.log_params(params)

            # Log metrics
            if metrics:
                mlflow.log_metrics(metrics)

            # Log artifacts
            if artifacts:
                for name, path in artifacts.items():
                    mlflow.log_artifact(path, artifact_path=name)

            # Log model based on framework
            if framework == "pytorch":
                mlflow.pytorch.log_model(
                    model,
                    artifact_path=model_name,
                    registered_model_name=model_name
                )
            elif framework == "onnx":
                mlflow.onnx.log_model(
                    model,
                    artifact_path=model_name,
                    registered_model_name=model_name
                )

            logger.info(f"Logged model {model_name} to MLflow (run_id: {run.info.run_id})")
            return run.info.run_id

    def convert_to_onnx(
        self,
        pytorch_model: torch.nn.Module,
        input_shape: tuple,
        output_path: Path,
        opset_version: int = 14
    ) -> Path:
        """
        Convert PyTorch model to ONNX for edge deployment.

        Args:
            pytorch_model: PyTorch model
            input_shape: Input tensor shape
            output_path: Path to save ONNX model
            opset_version: ONNX opset version

        Returns:
            Path to ONNX model
        """
        pytorch_model.eval()

        # Create dummy input
        dummy_input = torch.randn(*input_shape)

        # Export to ONNX
        torch.onnx.export(
            pytorch_model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )

        logger.info(f"Converted model to ONNX: {output_path}")
        return output_path

    def register_model_version(
        self,
        model_name: str,
        run_id: str,
        stage: str = "Staging"
    ):
        """
        Register a model version.

        Args:
            model_name: Model name
            run_id: MLflow run ID
            stage: Model stage (Staging, Production)
        """
        client = mlflow.tracking.MlflowClient()

        # Get model version
        model_uri = f"runs:/{run_id}/{model_name}"
        model_details = mlflow.register_model(model_uri, model_name)

        # Transition to stage
        client.transition_model_version_stage(
            name=model_name,
            version=model_details.version,
            stage=stage
        )

        logger.info(
            f"Registered {model_name} version {model_details.version} "
            f"to {stage} stage"
        )

    def deploy_to_edge(
        self,
        model_name: str,
        version: Optional[int] = None,
        device_ids: Optional[list] = None
    ):
        """
        Deploy model to edge devices.

        Args:
            model_name: Model name
            version: Model version (None for latest)
            device_ids: Target device IDs
        """
        client = mlflow.tracking.MlflowClient()

        # Get model version
        if version is None:
            versions = client.get_latest_versions(model_name, stages=["Production"])
            if not versions:
                raise ValueError(f"No production version found for {model_name}")
            model_version = versions[0]
        else:
            model_version = client.get_model_version(model_name, version)

        # Download model artifact
        model_uri = f"models:/{model_name}/{model_version.version}"
        model_path = mlflow.artifacts.download_artifacts(model_uri)

        # Deploy to edge devices
        device_ids = device_ids or ["control-pc-1", "spark-agent-1"]

        for device_id in device_ids:
            logger.info(f"Deploying {model_name} v{model_version.version} to {device_id}")

            # In production, this would:
            # 1. Copy model to NAS
            # 2. Notify edge device via Kafka
            # 3. Edge device downloads and loads model
            # 4. Verify deployment

        logger.info(f"Model {model_name} deployed to {len(device_ids)} devices")

    def compare_models(
        self,
        model_name: str,
        metric_name: str = "accuracy"
    ) -> Dict[str, Any]:
        """
        Compare model versions.

        Args:
            model_name: Model name
            metric_name: Metric to compare

        Returns:
            Comparison results
        """
        client = mlflow.tracking.MlflowClient()

        # Get all versions
        versions = client.search_model_versions(f"name='{model_name}'")

        comparison = []
        for version in versions:
            run = client.get_run(version.run_id)
            metrics = run.data.metrics

            comparison.append({
                'version': version.version,
                'stage': version.current_stage,
                'run_id': version.run_id,
                metric_name: metrics.get(metric_name, 0),
                'created_at': version.creation_timestamp
            })

        # Sort by metric
        comparison.sort(key=lambda x: x[metric_name], reverse=True)

        return {
            'model_name': model_name,
            'metric': metric_name,
            'versions': comparison
        }


# Global model deployer instance
model_deployer = ModelDeployer()
