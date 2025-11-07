"""
Cloud Real-Time Aggregation Engine
Kafka-based streaming data aggregation with windowing support
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import numpy as np

logger = logging.getLogger(__name__)


class WindowType(Enum):
    """Windowing strategies for aggregation"""
    TUMBLING = "tumbling"  # Fixed, non-overlapping windows
    SLIDING = "sliding"    # Overlapping windows
    SESSION = "session"    # Event-driven windows with gaps


class AggregationFunction(Enum):
    """Supported aggregation functions"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    FIRST = "first"
    LAST = "last"
    RATE = "rate"  # Events per second


@dataclass
class WindowConfig:
    """Window configuration"""
    window_type: WindowType
    size_seconds: int
    slide_seconds: Optional[int] = None  # For sliding windows
    session_gap_seconds: Optional[int] = None  # For session windows


@dataclass
class AggregationRule:
    """Aggregation rule definition"""
    rule_id: str
    source_topic: str
    target_topic: str
    window_config: WindowConfig
    aggregation_function: AggregationFunction
    group_by: List[str]
    value_field: str
    filters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class WindowState:
    """State for a single aggregation window"""
    window_start: datetime
    window_end: datetime
    values: List[float] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: Dict[str, Any], value: float):
        """Add event to window"""
        self.events.append(event)
        self.values.append(value)
        self.count += 1

    def compute(self, agg_function: AggregationFunction) -> float:
        """Compute aggregation result"""
        if not self.values:
            return 0.0

        if agg_function == AggregationFunction.SUM:
            return sum(self.values)
        elif agg_function == AggregationFunction.AVG:
            return np.mean(self.values)
        elif agg_function == AggregationFunction.MIN:
            return min(self.values)
        elif agg_function == AggregationFunction.MAX:
            return max(self.values)
        elif agg_function == AggregationFunction.COUNT:
            return self.count
        elif agg_function == AggregationFunction.FIRST:
            return self.values[0] if self.values else 0.0
        elif agg_function == AggregationFunction.LAST:
            return self.values[-1] if self.values else 0.0
        elif agg_function == AggregationFunction.RATE:
            duration = (self.window_end - self.window_start).total_seconds()
            return self.count / duration if duration > 0 else 0.0

        return 0.0


class TumblingWindowManager:
    """Manages tumbling (fixed) windows"""

    def __init__(self, window_size: int):
        self.window_size = window_size  # seconds
        self.windows: Dict[str, WindowState] = {}

    def get_window_key(self, timestamp: datetime, group_key: str) -> str:
        """Get window key for timestamp and group"""
        window_start = timestamp.replace(
            second=timestamp.second - (timestamp.second % self.window_size),
            microsecond=0
        )
        return f"{group_key}:{window_start.isoformat()}"

    def get_or_create_window(self, timestamp: datetime, group_key: str) -> WindowState:
        """Get or create window for timestamp"""
        window_key = self.get_window_key(timestamp, group_key)

        if window_key not in self.windows:
            window_start = timestamp.replace(
                second=timestamp.second - (timestamp.second % self.window_size),
                microsecond=0
            )
            window_end = window_start + timedelta(seconds=self.window_size)

            self.windows[window_key] = WindowState(
                window_start=window_start,
                window_end=window_end
            )

        return self.windows[window_key]

    def get_completed_windows(self, current_time: datetime) -> List[Tuple[str, WindowState]]:
        """Get windows that have completed"""
        completed = []

        for key, window in list(self.windows.items()):
            if window.window_end <= current_time:
                completed.append((key, window))
                del self.windows[key]

        return completed


class SlidingWindowManager:
    """Manages sliding (overlapping) windows"""

    def __init__(self, window_size: int, slide_size: int):
        self.window_size = window_size  # seconds
        self.slide_size = slide_size  # seconds
        self.events: Dict[str, deque] = defaultdict(lambda: deque())

    def add_event(self, timestamp: datetime, group_key: str,
                 event: Dict[str, Any], value: float):
        """Add event to sliding buffer"""
        self.events[group_key].append({
            "timestamp": timestamp,
            "event": event,
            "value": value
        })

    def get_windows(self, current_time: datetime, group_key: str) -> List[WindowState]:
        """Get all active windows for group"""
        events = self.events.get(group_key, deque())
        if not events:
            return []

        # Clean old events
        cutoff_time = current_time - timedelta(seconds=self.window_size)
        while events and events[0]["timestamp"] < cutoff_time:
            events.popleft()

        # Generate sliding windows
        windows = []
        window_start = current_time - timedelta(seconds=self.window_size)

        while window_start < current_time:
            window_end = window_start + timedelta(seconds=self.window_size)
            window = WindowState(
                window_start=window_start,
                window_end=window_end
            )

            # Add events in window
            for item in events:
                if window_start <= item["timestamp"] < window_end:
                    window.add_event(item["event"], item["value"])

            if window.count > 0:
                windows.append(window)

            window_start += timedelta(seconds=self.slide_size)

        return windows


class StreamProcessor:
    """Processes streaming data for a single rule"""

    def __init__(self, rule: AggregationRule):
        self.rule = rule
        self.window_manager = self._create_window_manager()
        self.stats = {
            "events_processed": 0,
            "windows_completed": 0,
            "errors": 0
        }

    def _create_window_manager(self):
        """Create appropriate window manager"""
        window_config = self.rule.window_config

        if window_config.window_type == WindowType.TUMBLING:
            return TumblingWindowManager(window_config.size_seconds)
        elif window_config.window_type == WindowType.SLIDING:
            return SlidingWindowManager(
                window_config.size_seconds,
                window_config.slide_seconds or window_config.size_seconds // 2
            )
        else:
            raise ValueError(f"Unsupported window type: {window_config.window_type}")

    def process_event(self, event: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Process a single event"""
        try:
            # Apply filters
            if not self._matches_filters(event):
                return None

            # Extract timestamp
            timestamp = self._extract_timestamp(event)

            # Extract group key
            group_key = self._extract_group_key(event)

            # Extract value
            value = self._extract_value(event)

            # Add to window
            if isinstance(self.window_manager, TumblingWindowManager):
                window = self.window_manager.get_or_create_window(timestamp, group_key)
                window.add_event(event, value)

                # Check for completed windows
                completed = self.window_manager.get_completed_windows(datetime.now())
                results = []

                for window_key, window in completed:
                    result = self._create_result(window, group_key)
                    results.append(result)
                    self.stats["windows_completed"] += 1

                self.stats["events_processed"] += 1
                return results if results else None

            elif isinstance(self.window_manager, SlidingWindowManager):
                self.window_manager.add_event(timestamp, group_key, event, value)
                self.stats["events_processed"] += 1
                # Sliding windows emit on timer, not per-event
                return None

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            self.stats["errors"] += 1
            return None

    def _matches_filters(self, event: Dict[str, Any]) -> bool:
        """Check if event matches filters"""
        for key, expected_value in self.rule.filters.items():
            if event.get(key) != expected_value:
                return False
        return True

    def _extract_timestamp(self, event: Dict[str, Any]) -> datetime:
        """Extract timestamp from event"""
        if "timestamp" in event:
            if isinstance(event["timestamp"], datetime):
                return event["timestamp"]
            return datetime.fromisoformat(event["timestamp"])
        return datetime.now()

    def _extract_group_key(self, event: Dict[str, Any]) -> str:
        """Extract group key from event"""
        if not self.rule.group_by:
            return "all"

        key_parts = [str(event.get(field, "")) for field in self.rule.group_by]
        return ":".join(key_parts)

    def _extract_value(self, event: Dict[str, Any]) -> float:
        """Extract numeric value from event"""
        value = event.get(self.rule.value_field, 0)
        return float(value) if value is not None else 0.0

    def _create_result(self, window: WindowState, group_key: str) -> Dict[str, Any]:
        """Create aggregation result"""
        aggregated_value = window.compute(self.rule.aggregation_function)

        return {
            "rule_id": self.rule.rule_id,
            "window_start": window.window_start.isoformat(),
            "window_end": window.window_end.isoformat(),
            "group_key": group_key,
            "aggregation": self.rule.aggregation_function.value,
            "value": aggregated_value,
            "event_count": window.count,
            "timestamp": datetime.now().isoformat()
        }


class AggregationEngine:
    """Main real-time aggregation engine"""

    def __init__(self, kafka_bootstrap_servers: str):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.rules: Dict[str, AggregationRule] = {}
        self.processors: Dict[str, StreamProcessor] = {}
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False
        self.stats = {
            "total_events": 0,
            "total_aggregations": 0,
            "active_rules": 0
        }

    async def initialize(self):
        """Initialize Kafka connections"""
        try:
            # Create consumer
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id="aggregation-engine",
                enable_auto_commit=True,
                auto_offset_reset="latest",
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            # Create producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )

            await self.consumer.start()
            await self.producer.start()

            logger.info("Aggregation engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize aggregation engine: {e}")
            raise

    async def add_rule(self, rule: AggregationRule):
        """Add aggregation rule"""
        self.rules[rule.rule_id] = rule
        self.processors[rule.rule_id] = StreamProcessor(rule)

        # Subscribe to source topic
        self.consumer.subscribe([rule.source_topic])
        self.stats["active_rules"] = len(self.rules)

        logger.info(f"Added aggregation rule: {rule.rule_id}")

    async def remove_rule(self, rule_id: str):
        """Remove aggregation rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            del self.processors[rule_id]
            self.stats["active_rules"] = len(self.rules)
            logger.info(f"Removed aggregation rule: {rule_id}")

    async def start(self):
        """Start processing events"""
        self.running = True
        logger.info("Aggregation engine started")

        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                self.stats["total_events"] += 1

                # Process with relevant rules
                for rule_id, processor in self.processors.items():
                    rule = self.rules[rule_id]

                    if msg.topic == rule.source_topic and rule.enabled:
                        results = processor.process_event(msg.value)

                        if results:
                            # Publish aggregation results
                            for result in results:
                                await self.producer.send(
                                    rule.target_topic,
                                    value=result
                                )
                                self.stats["total_aggregations"] += 1

        except Exception as e:
            logger.error(f"Aggregation engine error: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop processing"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        logger.info("Aggregation engine stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregation engine statistics"""
        processor_stats = {
            rule_id: processor.stats
            for rule_id, processor in self.processors.items()
        }

        return {
            **self.stats,
            "processors": processor_stats
        }


# Global aggregation engine instance
_aggregation_engine = None

def get_aggregation_engine() -> AggregationEngine:
    """Get global aggregation engine instance"""
    global _aggregation_engine
    if _aggregation_engine is None:
        # TODO: Load from config
        kafka_servers = "localhost:9092"
        _aggregation_engine = AggregationEngine(kafka_servers)
    return _aggregation_engine
