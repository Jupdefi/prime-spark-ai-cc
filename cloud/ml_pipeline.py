"""
Cloud ML Pipeline Manager
MLflow-based machine learning pipeline orchestration
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """ML pipeline stages"""
    DATA_INGESTION = "data_ingestion"
    DATA_VALIDATION = "data_validation"
    PREPROCESSING = "preprocessing"
    FEATURE_ENGINEERING = "feature_engineering"
    TRAINING = "training"
    EVALUATION = "evaluation"
    MODEL_VALIDATION = "model_validation"
    DEPLOYMENT = "deployment"


class ModelStatus(Enum):
    """Model lifecycle status"""
    TRAINING = "training"
    VALIDATION = "validation"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class DeploymentTarget(Enum):
    """Model deployment targets"""
    EDGE = "edge"
    CLOUD = "cloud"
    HYBRID = "hybrid"


@dataclass
class PipelineConfig:
    """ML pipeline configuration"""
    pipeline_id: str
    pipeline_name: str
    model_type: str
    stages: List[PipelineStage]
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)
    target_metric: str = "accuracy"
    metric_threshold: float = 0.8
    deployment_target: DeploymentTarget = DeploymentTarget.CLOUD
    auto_deploy: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineRun:
    """ML pipeline run record"""
    run_id: str
    pipeline_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_name: str
    model_version: str
    run_id: str
    status: ModelStatus
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    deployment_target: DeploymentTarget
    created_at: datetime
    deployed_at: Optional[datetime] = None


class MLflowManager:
    """MLflow tracking and registry manager"""

    def __init__(self, tracking_uri: str, registry_uri: Optional[str] = None):
        self.tracking_uri = tracking_uri
        self.registry_uri = registry_uri or tracking_uri
        self.client: Optional[MlflowClient] = None

    def initialize(self):
        """Initialize MLflow client"""
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_registry_uri(self.registry_uri)
        self.client = MlflowClient()
        logger.info(f"MLflow initialized: {self.tracking_uri}")

    def create_experiment(self, experiment_name: str) -> str:
        """Create or get experiment"""
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
            logger.info(f"Created experiment: {experiment_name}")
        else:
            experiment_id = experiment.experiment_id

        return experiment_id

    def start_run(self, experiment_id: str, run_name: str) -> str:
        """Start MLflow run"""
        run = mlflow.start_run(
            experiment_id=experiment_id,
            run_name=run_name
        )
        return run.info.run_id

    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics"""
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, artifact_path: str):
        """Log artifact"""
        mlflow.log_artifact(artifact_path)

    def end_run(self):
        """End MLflow run"""
        mlflow.end_run()

    def register_model(self, model_uri: str, model_name: str) -> str:
        """Register model to registry"""
        result = mlflow.register_model(model_uri, model_name)
        logger.info(f"Registered model: {model_name} v{result.version}")
        return result.version

    def transition_model_stage(self, model_name: str, version: str,
                              stage: str):
        """Transition model to stage (Staging/Production/Archived)"""
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=True
        )
        logger.info(f"Transitioned {model_name} v{version} to {stage}")

    def get_latest_model_version(self, model_name: str,
                                 stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get latest model version"""
        filter_string = f"name='{model_name}'"
        if stage:
            filter_string += f" and tags.stage='{stage}'"

        versions = self.client.search_model_versions(filter_string)
        if versions:
            latest = max(versions, key=lambda v: int(v.version))
            return {
                "name": latest.name,
                "version": latest.version,
                "run_id": latest.run_id,
                "stage": latest.current_stage,
                "source": latest.source
            }
        return None

    def search_runs(self, experiment_id: str, filter_string: str = "",
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """Search runs"""
        runs = self.client.search_runs(
            experiment_ids=[experiment_id],
            filter_string=filter_string,
            run_view_type=ViewType.ALL,
            max_results=max_results,
            order_by=["start_time DESC"]
        )

        return [
            {
                "run_id": run.info.run_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags
            }
            for run in runs
        ]


class PipelineStageExecutor:
    """Base class for pipeline stage execution"""

    def __init__(self, stage: PipelineStage):
        self.stage = stage

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline stage"""
        raise NotImplementedError


class DataIngestionStage(PipelineStageExecutor):
    """Data ingestion stage"""

    def __init__(self):
        super().__init__(PipelineStage.DATA_INGESTION)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest data from sources"""
        data_sources = context.get("data_sources", [])
        logger.info(f"Ingesting data from {len(data_sources)} sources")

        # TODO: Implement actual data ingestion
        # For now, return mock data
        data = pd.DataFrame({
            "feature1": np.random.randn(1000),
            "feature2": np.random.randn(1000),
            "target": np.random.randint(0, 2, 1000)
        })

        return {"data": data, "row_count": len(data)}


class TrainingStage(PipelineStageExecutor):
    """Model training stage"""

    def __init__(self):
        super().__init__(PipelineStage.TRAINING)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Train model"""
        logger.info("Training model")

        # Get data and hyperparameters
        data = context.get("data")
        hyperparameters = context.get("hyperparameters", {})

        # TODO: Implement actual training
        # For now, simulate training
        await asyncio.sleep(2)

        # Mock metrics
        metrics = {
            "accuracy": 0.85 + np.random.random() * 0.1,
            "precision": 0.82 + np.random.random() * 0.1,
            "recall": 0.80 + np.random.random() * 0.1,
            "f1_score": 0.81 + np.random.random() * 0.1
        }

        return {
            "model": "mock_model",  # Would be actual model object
            "metrics": metrics
        }


class MLPipelineManager:
    """Main ML pipeline manager"""

    def __init__(self, mlflow_uri: str):
        self.mlflow = MLflowManager(mlflow_uri)
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.runs: Dict[str, PipelineRun] = {}
        self.stage_executors: Dict[PipelineStage, PipelineStageExecutor] = {
            PipelineStage.DATA_INGESTION: DataIngestionStage(),
            PipelineStage.TRAINING: TrainingStage(),
            # Add more stages as needed
        }
        self.stats = {
            "total_pipelines": 0,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "models_deployed": 0
        }

    def initialize(self):
        """Initialize ML pipeline manager"""
        self.mlflow.initialize()
        logger.info("ML Pipeline Manager initialized")

    def register_pipeline(self, config: PipelineConfig):
        """Register ML pipeline"""
        self.pipelines[config.pipeline_id] = config
        self.stats["total_pipelines"] += 1

        # Create MLflow experiment
        self.mlflow.create_experiment(config.pipeline_name)

        logger.info(f"Registered pipeline: {config.pipeline_name}")

    async def run_pipeline(self, pipeline_id: str,
                          context: Optional[Dict[str, Any]] = None) -> PipelineRun:
        """Execute ML pipeline"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        config = self.pipelines[pipeline_id]
        context = context or {}

        # Initialize context
        context.update({
            "pipeline_id": pipeline_id,
            "hyperparameters": config.hyperparameters,
            "data_sources": config.data_sources,
            "deployment_target": config.deployment_target
        })

        # Create run record
        run_id = f"{pipeline_id}_{datetime.now().timestamp()}"
        pipeline_run = PipelineRun(
            run_id=run_id,
            pipeline_id=pipeline_id,
            status="running",
            started_at=datetime.now()
        )
        self.runs[run_id] = pipeline_run
        self.stats["total_runs"] += 1

        # Start MLflow run
        experiment_id = self.mlflow.create_experiment(config.pipeline_name)
        mlflow_run_id = self.mlflow.start_run(experiment_id, run_id)

        try:
            # Log pipeline config
            self.mlflow.log_params({
                "pipeline_id": pipeline_id,
                "model_type": config.model_type,
                **config.hyperparameters
            })

            # Execute stages
            for stage in config.stages:
                logger.info(f"Executing stage: {stage.value}")

                executor = self.stage_executors.get(stage)
                if not executor:
                    logger.warning(f"No executor for stage: {stage.value}")
                    continue

                result = await executor.execute(context)
                context.update(result)

                # Log stage completion
                if "metrics" in result:
                    self.mlflow.log_metrics(result["metrics"])
                    pipeline_run.metrics.update(result["metrics"])

            # Check if model should be deployed
            target_metric = pipeline_run.metrics.get(config.target_metric, 0)
            if target_metric >= config.metric_threshold:
                logger.info(f"Model meets threshold: {target_metric} >= {config.metric_threshold}")

                if config.auto_deploy:
                    await self._deploy_model(config, mlflow_run_id, pipeline_run)

            # Mark success
            pipeline_run.status = "completed"
            pipeline_run.completed_at = datetime.now()
            self.stats["successful_runs"] += 1

        except Exception as e:
            logger.error(f"Pipeline run failed: {e}")
            pipeline_run.status = "failed"
            pipeline_run.error_message = str(e)
            pipeline_run.completed_at = datetime.now()
            self.stats["failed_runs"] += 1

        finally:
            self.mlflow.end_run()

        return pipeline_run

    async def _deploy_model(self, config: PipelineConfig,
                           mlflow_run_id: str, pipeline_run: PipelineRun):
        """Deploy model to target"""
        logger.info(f"Deploying model to {config.deployment_target.value}")

        # Register model
        model_uri = f"runs:/{mlflow_run_id}/model"
        version = self.mlflow.register_model(model_uri, config.pipeline_name)

        # Transition to production
        self.mlflow.transition_model_stage(
            config.pipeline_name,
            version,
            "Production"
        )

        self.stats["models_deployed"] += 1
        logger.info(f"Model deployed: {config.pipeline_name} v{version}")

    def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get pipeline status"""
        if pipeline_id not in self.pipelines:
            return {"error": "Pipeline not found"}

        config = self.pipelines[pipeline_id]
        runs = [r for r in self.runs.values() if r.pipeline_id == pipeline_id]

        return {
            "pipeline_id": pipeline_id,
            "pipeline_name": config.pipeline_name,
            "total_runs": len(runs),
            "latest_run": runs[-1] if runs else None,
            "config": {
                "model_type": config.model_type,
                "stages": [s.value for s in config.stages],
                "deployment_target": config.deployment_target.value,
                "auto_deploy": config.auto_deploy
            }
        }

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get deployed model information"""
        return self.mlflow.get_latest_model_version(model_name, stage="Production")

    def get_stats(self) -> Dict[str, Any]:
        """Get ML pipeline statistics"""
        success_rate = (
            self.stats["successful_runs"] / self.stats["total_runs"]
            if self.stats["total_runs"] > 0 else 0
        )

        return {
            **self.stats,
            "success_rate": success_rate,
            "active_pipelines": len(self.pipelines)
        }


# Global ML pipeline manager instance
_ml_pipeline_manager = None

def get_ml_pipeline_manager() -> MLPipelineManager:
    """Get global ML pipeline manager instance"""
    global _ml_pipeline_manager
    if _ml_pipeline_manager is None:
        # TODO: Load from config
        mlflow_uri = "http://localhost:5001"
        _ml_pipeline_manager = MLPipelineManager(mlflow_uri)
    return _ml_pipeline_manager
