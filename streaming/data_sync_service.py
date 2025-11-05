"""
Data Synchronization Service
Syncs data between edge devices and cloud in real-time
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from streaming.kafka_manager import get_kafka_manager, StreamMessage
from analytics.timeseries_db import timescale_db
from memory.memory_manager import memory

logger = logging.getLogger(__name__)


class DataSyncService:
    """
    Synchronizes data between edge and cloud.

    Architecture:
    - Edge devices publish to Kafka topics
    - Service consumes from Kafka
    - Data is persisted to TimescaleDB
    - Critical data cached in memory tiers
    """

    def __init__(self):
        self.kafka = get_kafka_manager()
        self.running = False

    async def start(self):
        """Start data synchronization"""
        logger.info("Starting data sync service...")

        # Initialize database
        await timescale_db.initialize_schema()

        # Subscribe to edge topics
        self.kafka.subscribe_consumer(
            topics=['edge.telemetry', 'edge.ai.inference', 'edge.sensors'],
            group_id='data-sync-service',
            callback=self._process_message
        )

        self.running = True
        logger.info("Data sync service started successfully")

    def _process_message(self, message: StreamMessage):
        """Process incoming Kafka message"""
        try:
            # Route to appropriate handler based on topic
            if message.topic == 'edge.telemetry':
                asyncio.create_task(self._handle_telemetry(message))
            elif message.topic == 'edge.ai.inference':
                asyncio.create_task(self._handle_ai_inference(message))
            elif message.topic == 'edge.sensors':
                asyncio.create_task(self._handle_sensor_data(message))

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_telemetry(self, message: StreamMessage):
        """Handle telemetry data"""
        data = message.value
        device_id = data.get('device_id')
        metrics = data.get('metrics', {})

        # Store in TimescaleDB
        for metric_name, metric_value in metrics.items():
            await timescale_db.insert_device_metric(
                device_id=device_id,
                metric_name=metric_name,
                value=float(metric_value),
                tags={'source': message.source},
                timestamp=message.timestamp
            )

        # Cache critical metrics
        if metric_name in ['cpu_usage', 'memory_usage', 'battery_level']:
            cache_key = f"device:{device_id}:metric:{metric_name}"
            await memory.set(
                key=cache_key,
                value={'value': metric_value, 'timestamp': message.timestamp.isoformat()},
                persist_to_nas=False,  # Hot data only
                ttl=300  # 5 minutes
            )

        logger.debug(f"Processed telemetry for {device_id}")

    async def _handle_ai_inference(self, message: StreamMessage):
        """Handle AI inference results"""
        data = message.value
        device_id = data.get('device_id')
        model = data.get('model')
        result = data.get('result', {})
        inference_time = result.get('inference_time_ms', 0)

        # Store in TimescaleDB
        await timescale_db.insert_ai_inference(
            device_id=device_id,
            model_name=model,
            inference_time_ms=inference_time,
            result=result,
            accuracy=result.get('accuracy'),
            timestamp=message.timestamp
        )

        # Cache recent inference results
        cache_key = f"ai:inference:{device_id}:{model}:latest"
        await memory.set(
            key=cache_key,
            value=result,
            persist_to_nas=True,  # Save to NAS for analysis
            ttl=3600
        )

        logger.debug(f"Processed AI inference for {device_id}/{model}")

    async def _handle_sensor_data(self, message: StreamMessage):
        """Handle sensor data"""
        data = message.value
        device_id = data.get('device_id')
        sensor_type = data.get('sensor_type')
        sensor_data = data.get('data', {})
        value = sensor_data.get('value', 0)

        # Store in TimescaleDB
        await timescale_db.insert_sensor_data(
            device_id=device_id,
            sensor_type=sensor_type,
            value=float(value),
            sensor_id=sensor_data.get('sensor_id'),
            unit=sensor_data.get('unit'),
            data=sensor_data,
            timestamp=message.timestamp
        )

        logger.debug(f"Processed sensor data for {device_id}/{sensor_type}")

    async def publish_edge_metrics(self, device_id: str, metrics: Dict[str, Any]):
        """Publish edge metrics to Kafka"""
        await self.kafka.send_message(
            topic='edge.telemetry',
            message={
                'device_id': device_id,
                'type': 'system_metrics',
                'metrics': metrics
            },
            key=device_id,
            source='edge'
        )

    async def publish_ai_inference(
        self,
        device_id: str,
        model: str,
        result: Dict[str, Any]
    ):
        """Publish AI inference result"""
        await self.kafka.send_message(
            topic='edge.ai.inference',
            message={
                'device_id': device_id,
                'model': model,
                'result': result
            },
            key=device_id,
            source='edge'
        )

    async def stop(self):
        """Stop data synchronization"""
        self.running = False
        self.kafka.close()
        await timescale_db.disconnect()
        logger.info("Data sync service stopped")


# Global data sync service instance
data_sync_service = DataSyncService()
