"""
KVA Data Connectors
Homelab sensors, cloud services, third-party APIs, ETL pipelines
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
import aiohttp
import psutil

from kva.storage_manager import get_storage_manager

logger = logging.getLogger(__name__)


class DataConnector(ABC):
    """Base data connector"""

    @abstractmethod
    async def connect(self):
        """Establish connection"""
        pass

    @abstractmethod
    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch data from source"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection"""
        pass


# === Homelab Sensor Integration ===

class HomelabSensorConnector(DataConnector):
    """Connect to homelab sensors"""

    def __init__(self, sensor_config: Dict):
        self.config = sensor_config
        self.sensors = []

    async def connect(self):
        """Initialize sensor connections"""
        # CPU sensor
        self.sensors.append({
            "type": "cpu",
            "name": "system_cpu",
            "collector": lambda: psutil.cpu_percent()
        })

        # Memory sensor
        self.sensors.append({
            "type": "memory",
            "name": "system_memory",
            "collector": lambda: psutil.virtual_memory().percent
        })

        # Disk sensor
        self.sensors.append({
            "type": "disk",
            "name": "system_disk",
            "collector": lambda: psutil.disk_usage('/').percent
        })

        # Temperature sensor (Raspberry Pi)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                self.sensors.append({
                    "type": "temperature",
                    "name": "cpu_temperature",
                    "collector": lambda: float(open('/sys/class/thermal/thermal_zone0/temp').read().strip()) / 1000.0
                })
        except:
            pass

        logger.info(f"Connected {len(self.sensors)} homelab sensors")

    async def fetch_data(self) -> Dict[str, Any]:
        """Collect sensor data"""
        data = {}
        for sensor in self.sensors:
            try:
                value = sensor["collector"]()
                data[sensor["name"]] = {
                    "type": sensor["type"],
                    "value": value,
                    "timestamp": datetime.now().isoformat(),
                    "unit": self._get_unit(sensor["type"])
                }
            except Exception as e:
                logger.error(f"Sensor {sensor['name']} error: {e}")

        return data

    def _get_unit(self, sensor_type: str) -> str:
        """Get sensor unit"""
        units = {
            "cpu": "%",
            "memory": "%",
            "disk": "%",
            "temperature": "°C"
        }
        return units.get(sensor_type, "")

    async def disconnect(self):
        """Disconnect sensors"""
        logger.info("Homelab sensors disconnected")


# === Cloud Service Connectors ===

class AWSConnector(DataConnector):
    """AWS service connector"""

    def __init__(self, aws_config: Dict):
        self.config = aws_config
        self.session = None

    async def connect(self):
        """Connect to AWS"""
        # Initialize boto3 session
        logger.info("AWS connector initialized")

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch data from AWS services"""
        # Placeholder - would fetch from CloudWatch, S3, etc.
        return {
            "service": "aws",
            "data": {"status": "connected"},
            "timestamp": datetime.now().isoformat()
        }

    async def disconnect(self):
        """Disconnect from AWS"""
        logger.info("AWS connector disconnected")


class GCPConnector(DataConnector):
    """Google Cloud Platform connector"""

    def __init__(self, gcp_config: Dict):
        self.config = gcp_config

    async def connect(self):
        """Connect to GCP"""
        logger.info("GCP connector initialized")

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch data from GCP services"""
        return {
            "service": "gcp",
            "data": {"status": "connected"},
            "timestamp": datetime.now().isoformat()
        }

    async def disconnect(self):
        """Disconnect from GCP"""
        logger.info("GCP connector disconnected")


# === Third-Party API Integration ===

class APIConnector(DataConnector):
    """Generic REST API connector"""

    def __init__(self, api_config: Dict):
        self.config = api_config
        self.base_url = api_config.get("base_url")
        self.headers = api_config.get("headers", {})
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self):
        """Create HTTP session"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        logger.info(f"API connector initialized: {self.base_url}")

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch data from API"""
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "source": "api",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"API fetch error: {e}")

        return {}

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
        logger.info("API connector disconnected")


# === ETL Pipeline Automation ===

@dataclass
class ETLJob:
    """ETL job configuration"""
    job_id: str
    source_connector: DataConnector
    transform_func: Optional[Callable] = None
    destination: str = "storage"
    schedule_interval: int = 60  # seconds
    enabled: bool = True


class ETLPipeline:
    """ETL pipeline manager"""

    def __init__(self):
        self.jobs: Dict[str, ETLJob] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.stats = {"total_runs": 0, "successful_runs": 0, "failed_runs": 0}

    def register_job(self, job: ETLJob):
        """Register ETL job"""
        self.jobs[job.job_id] = job
        logger.info(f"Registered ETL job: {job.job_id}")

    async def start_job(self, job_id: str):
        """Start ETL job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        task = asyncio.create_task(self._run_job_loop(job))
        self.running_jobs[job_id] = task
        logger.info(f"Started ETL job: {job_id}")

    async def stop_job(self, job_id: str):
        """Stop ETL job"""
        if job_id in self.running_jobs:
            self.running_jobs[job_id].cancel()
            del self.running_jobs[job_id]
            logger.info(f"Stopped ETL job: {job_id}")

    async def _run_job_loop(self, job: ETLJob):
        """Run ETL job in loop"""
        await job.source_connector.connect()

        try:
            while True:
                if job.enabled:
                    await self._execute_job(job)
                await asyncio.sleep(job.schedule_interval)
        finally:
            await job.source_connector.disconnect()

    async def _execute_job(self, job: ETLJob):
        """Execute single ETL run"""
        try:
            self.stats["total_runs"] += 1

            # Extract
            data = await job.source_connector.fetch_data()

            # Transform
            if job.transform_func:
                data = job.transform_func(data)

            # Load
            storage = get_storage_manager()

            # Store in appropriate backend
            for key, value in data.items():
                # Store in Redis for quick access
                await storage.redis.set(f"sensor:{key}", value)

                # Store in ClickHouse for time-series analytics
                if isinstance(value, dict) and "value" in value:
                    await storage.clickhouse.insert_events([{
                        "timestamp": datetime.now(),
                        "event_type": "sensor_reading",
                        "metric_name": key,
                        "metric_value": value["value"],
                        "labels": {"source": "homelab"},
                        "source": "etl_pipeline"
                    }])

                # Store in PostgreSQL for relational queries
                await storage.postgres.insert_event(
                    event_type="sensor_data",
                    event_data={"sensor": key, **value},
                    source="etl_pipeline"
                )

            self.stats["successful_runs"] += 1
            logger.debug(f"ETL job {job.job_id} completed: {len(data)} items")

        except Exception as e:
            self.stats["failed_runs"] += 1
            logger.error(f"ETL job {job.job_id} failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get ETL statistics"""
        success_rate = (
            self.stats["successful_runs"] / self.stats["total_runs"]
            if self.stats["total_runs"] > 0 else 0
        )

        return {
            **self.stats,
            "success_rate": success_rate,
            "active_jobs": len(self.running_jobs),
            "registered_jobs": len(self.jobs)
        }


# === Data Connector Manager ===

class DataConnectorManager:
    """Manages all data connectors"""

    def __init__(self):
        self.connectors: Dict[str, DataConnector] = {}
        self.etl_pipeline = ETLPipeline()

    def register_connector(self, name: str, connector: DataConnector):
        """Register data connector"""
        self.connectors[name] = connector
        logger.info(f"Registered connector: {name}")

    async def initialize_homelab_sensors(self):
        """Initialize homelab sensor integration"""
        homelab = HomelabSensorConnector({})
        await homelab.connect()
        self.register_connector("homelab", homelab)

        # Create ETL job for sensors
        etl_job = ETLJob(
            job_id="homelab_sensors",
            source_connector=homelab,
            schedule_interval=30  # Collect every 30s
        )
        self.etl_pipeline.register_job(etl_job)
        await self.etl_pipeline.start_job("homelab_sensors")

        logger.info("Homelab sensors initialized")

    async def initialize_cloud_connectors(self, aws_config: Dict = None,
                                        gcp_config: Dict = None):
        """Initialize cloud service connectors"""
        if aws_config:
            aws = AWSConnector(aws_config)
            await aws.connect()
            self.register_connector("aws", aws)

        if gcp_config:
            gcp = GCPConnector(gcp_config)
            await gcp.connect()
            self.register_connector("gcp", gcp)

        logger.info("Cloud connectors initialized")

    async def initialize_api_connector(self, name: str, api_config: Dict):
        """Initialize third-party API connector"""
        api = APIConnector(api_config)
        await api.connect()
        self.register_connector(name, api)

        logger.info(f"API connector initialized: {name}")

    def get_connector(self, name: str) -> Optional[DataConnector]:
        """Get connector by name"""
        return self.connectors.get(name)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            "connectors": len(self.connectors),
            "etl_pipeline": self.etl_pipeline.get_stats()
        }

    async def shutdown(self):
        """Shutdown all connectors"""
        # Stop ETL jobs
        for job_id in list(self.etl_pipeline.running_jobs.keys()):
            await self.etl_pipeline.stop_job(job_id)

        # Disconnect connectors
        for connector in self.connectors.values():
            await connector.disconnect()

        logger.info("Data connectors shutdown")


# Global instance
_connector_manager = None

def get_connector_manager() -> DataConnectorManager:
    """Get global connector manager"""
    global _connector_manager
    if _connector_manager is None:
        _connector_manager = DataConnectorManager()
    return _connector_manager
