"""
Kafka Streaming Manager
Handles real-time data streaming between edge and cloud
"""
import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
import logging

logger = logging.getLogger(__name__)


@dataclass
class StreamMessage:
    """Message for streaming"""
    topic: str
    key: str
    value: Dict[str, Any]
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]


class KafkaManager:
    """
    Manages Kafka streaming for Prime Spark AI.

    Topics:
    - edge.telemetry: System telemetry from edge devices
    - edge.ai.inference: AI inference results from edge
    - edge.sensors: Sensor data from edge devices
    - cloud.commands: Commands from cloud to edge
    - analytics.events: Processed analytics events
    """

    def __init__(
        self,
        bootstrap_servers: List[str] = ["localhost:9092"],
        client_id: str = "prime-spark-ai"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.producer: Optional[KafkaProducer] = None
        self.consumers: Dict[str, KafkaConsumer] = {}
        self.admin_client: Optional[KafkaAdminClient] = None

    def _get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer"""
        if not self.producer:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}-producer",
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
        return self.producer

    def _get_admin_client(self) -> KafkaAdminClient:
        """Get or create Kafka admin client"""
        if not self.admin_client:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"{self.client_id}-admin"
            )
        return self.admin_client

    def create_topics(self, topics: List[str], num_partitions: int = 3, replication_factor: int = 1):
        """Create Kafka topics"""
        admin = self._get_admin_client()

        topic_list = [
            NewTopic(
                name=topic,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            for topic in topics
        ]

        try:
            admin.create_topics(new_topics=topic_list, validate_only=False)
            logger.info(f"Created topics: {topics}")
        except TopicAlreadyExistsError:
            logger.info(f"Topics already exist: {topics}")

    async def send_message(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None,
        source: str = "edge"
    ) -> bool:
        """
        Send message to Kafka topic.

        Args:
            topic: Topic name
            message: Message payload
            key: Message key for partitioning
            source: Source identifier (edge/cloud)

        Returns:
            Success boolean
        """
        try:
            producer = self._get_producer()

            # Wrap message with metadata
            wrapped_message = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": source,
                "data": message
            }

            future = producer.send(
                topic=topic,
                value=wrapped_message,
                key=key
            )

            # Wait for send confirmation
            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Sent message to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            return False

    def subscribe_consumer(
        self,
        topics: List[str],
        group_id: str,
        callback: Callable[[StreamMessage], None]
    ):
        """
        Subscribe to Kafka topics with a callback.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            callback: Function to call for each message
        """
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            client_id=f"{self.client_id}-{group_id}",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest',
            enable_auto_commit=True
        )

        self.consumers[group_id] = consumer

        # Start consuming in background
        async def consume():
            loop = asyncio.get_event_loop()

            for message in consumer:
                try:
                    stream_msg = StreamMessage(
                        topic=message.topic,
                        key=message.key,
                        value=message.value.get('data', {}),
                        timestamp=datetime.fromisoformat(message.value.get('timestamp')),
                        source=message.value.get('source', 'unknown'),
                        metadata={
                            'partition': message.partition,
                            'offset': message.offset
                        }
                    )

                    # Call callback in executor to avoid blocking
                    await loop.run_in_executor(None, callback, stream_msg)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        asyncio.create_task(consume())

    def close(self):
        """Close all Kafka connections"""
        if self.producer:
            self.producer.close()

        for consumer in self.consumers.values():
            consumer.close()

        if self.admin_client:
            self.admin_client.close()


class EdgeTelemetryStreamer:
    """Streams edge device telemetry to Kafka"""

    def __init__(self, kafka_manager: KafkaManager, device_id: str):
        self.kafka = kafka_manager
        self.device_id = device_id
        self.topic = "edge.telemetry"

    async def stream_system_metrics(self, metrics: Dict[str, Any]):
        """Stream system resource metrics"""
        await self.kafka.send_message(
            topic=self.topic,
            message={
                "device_id": self.device_id,
                "type": "system_metrics",
                "metrics": metrics
            },
            key=self.device_id
        )

    async def stream_ai_inference(self, model: str, result: Dict[str, Any]):
        """Stream AI inference results"""
        await self.kafka.send_message(
            topic="edge.ai.inference",
            message={
                "device_id": self.device_id,
                "model": model,
                "result": result
            },
            key=self.device_id
        )

    async def stream_sensor_data(self, sensor_type: str, data: Dict[str, Any]):
        """Stream sensor data"""
        await self.kafka.send_message(
            topic="edge.sensors",
            message={
                "device_id": self.device_id,
                "sensor_type": sensor_type,
                "data": data
            },
            key=self.device_id
        )


# Initialize default topics
DEFAULT_TOPICS = [
    "edge.telemetry",
    "edge.ai.inference",
    "edge.sensors",
    "cloud.commands",
    "analytics.events",
    "system.health",
    "models.updates"
]


def initialize_kafka_infrastructure(bootstrap_servers: List[str] = ["localhost:9092"]):
    """Initialize Kafka infrastructure with default topics"""
    kafka_manager = KafkaManager(bootstrap_servers=bootstrap_servers)
    kafka_manager.create_topics(DEFAULT_TOPICS)
    return kafka_manager


# Global Kafka manager instance
kafka_manager = None


def get_kafka_manager(bootstrap_servers: List[str] = ["localhost:9092"]) -> KafkaManager:
    """Get or create global Kafka manager"""
    global kafka_manager
    if kafka_manager is None:
        kafka_manager = initialize_kafka_infrastructure(bootstrap_servers)
    return kafka_manager
