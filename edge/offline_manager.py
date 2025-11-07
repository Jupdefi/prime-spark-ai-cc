"""
Edge Offline Capability Manager
Handles offline operation, request queuing, and sync when connectivity restored
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import aiohttp
from collections import deque

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Network connection status"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class OperationType(Enum):
    """Types of operations that can be queued"""
    INFERENCE = "inference"
    DATA_SYNC = "data_sync"
    MODEL_UPDATE = "model_update"
    TELEMETRY = "telemetry"
    CONFIG_UPDATE = "config_update"


class Priority(Enum):
    """Operation priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class QueuedOperation:
    """Queued operation for offline execution"""
    operation_id: str
    operation_type: OperationType
    priority: Priority
    payload: Dict[str, Any]
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedOperation':
        """Create from dictionary"""
        return cls(
            operation_id=data["operation_id"],
            operation_type=OperationType(data["operation_type"]),
            priority=Priority(data["priority"]),
            payload=data["payload"],
            created_at=datetime.fromisoformat(data["created_at"]),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {})
        )


@dataclass
class OfflineConfig:
    """Offline capability configuration"""
    # Connectivity monitoring
    cloud_endpoints: List[str] = field(default_factory=lambda: [
        "http://cloud-api:8000/health",
        "http://8.8.8.8",  # Google DNS as fallback
    ])
    check_interval: int = 30  # seconds
    timeout: int = 5  # seconds

    # Queue management
    queue_path: str = "/var/lib/prime-spark/offline_queue"
    max_queue_size: int = 10000
    persist_queue: bool = True

    # Sync strategy
    sync_batch_size: int = 50
    sync_interval: int = 60  # seconds when online
    retry_backoff: int = 2  # exponential backoff multiplier

    # Offline mode behavior
    enable_local_fallback: bool = True
    cache_inference_results: bool = True
    queue_telemetry: bool = True


class ConnectivityMonitor:
    """Monitors network connectivity to cloud services"""

    def __init__(self, config: OfflineConfig):
        self.config = config
        self.status = ConnectionStatus.UNKNOWN
        self.last_check: Optional[datetime] = None
        self.consecutive_failures = 0
        self.connectivity_history: deque = deque(maxlen=100)

    async def check_connectivity(self) -> ConnectionStatus:
        """Check connectivity to cloud endpoints"""
        self.last_check = datetime.now()

        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[
                self._check_endpoint(session, endpoint)
                for endpoint in self.config.cloud_endpoints
            ], return_exceptions=True)

        # Determine status based on results
        successful = sum(1 for r in results if r is True)
        total = len(results)

        if successful == total:
            self.status = ConnectionStatus.ONLINE
            self.consecutive_failures = 0
        elif successful > 0:
            self.status = ConnectionStatus.DEGRADED
            self.consecutive_failures += 1
        else:
            self.status = ConnectionStatus.OFFLINE
            self.consecutive_failures += 1

        # Track history
        self.connectivity_history.append({
            "timestamp": self.last_check,
            "status": self.status.value,
            "successful_endpoints": successful,
            "total_endpoints": total
        })

        logger.info(f"Connectivity status: {self.status.value} "
                   f"({successful}/{total} endpoints reachable)")

        return self.status

    async def _check_endpoint(self, session: aiohttp.ClientSession,
                             endpoint: str) -> bool:
        """Check single endpoint"""
        try:
            async with session.get(endpoint, timeout=self.config.timeout) as response:
                return response.status < 500
        except Exception as e:
            logger.debug(f"Endpoint {endpoint} unreachable: {e}")
            return False

    def is_online(self) -> bool:
        """Check if currently online"""
        return self.status == ConnectionStatus.ONLINE

    def is_degraded(self) -> bool:
        """Check if connection is degraded"""
        return self.status == ConnectionStatus.DEGRADED

    def is_offline(self) -> bool:
        """Check if offline"""
        return self.status == ConnectionStatus.OFFLINE


class OperationQueue:
    """Queue for offline operations"""

    def __init__(self, config: OfflineConfig):
        self.config = config
        self.queue: List[QueuedOperation] = []
        self.queue_path = Path(config.queue_path)
        self.processing = False

    async def initialize(self):
        """Initialize queue and load persisted operations"""
        self.queue_path.mkdir(parents=True, exist_ok=True)

        if self.config.persist_queue:
            await self._load_queue()

        logger.info(f"Operation queue initialized with {len(self.queue)} items")

    async def enqueue(self, operation: QueuedOperation) -> bool:
        """Add operation to queue"""
        if len(self.queue) >= self.config.max_queue_size:
            logger.warning(f"Queue full ({self.config.max_queue_size}), dropping operation")
            return False

        # Insert based on priority
        insert_index = 0
        for i, queued_op in enumerate(self.queue):
            if operation.priority.value < queued_op.priority.value:
                insert_index = i
                break
            insert_index = i + 1

        self.queue.insert(insert_index, operation)

        if self.config.persist_queue:
            await self._persist_queue()

        logger.debug(f"Enqueued operation {operation.operation_id} "
                    f"(priority: {operation.priority.value})")
        return True

    def dequeue(self, count: int = 1) -> List[QueuedOperation]:
        """Remove and return operations from queue"""
        operations = self.queue[:count]
        self.queue = self.queue[count:]
        return operations

    def peek(self, count: int = 1) -> List[QueuedOperation]:
        """View operations without removing"""
        return self.queue[:count]

    def size(self) -> int:
        """Get queue size"""
        return len(self.queue)

    async def _load_queue(self):
        """Load queue from disk"""
        queue_file = self.queue_path / "queue.json"
        if not queue_file.exists():
            return

        try:
            async with aiofiles.open(queue_file, 'r') as f:
                data = await f.read()
                queue_data = json.loads(data)

            self.queue = [
                QueuedOperation.from_dict(op_data)
                for op_data in queue_data
            ]
            logger.info(f"Loaded {len(self.queue)} operations from disk")
        except Exception as e:
            logger.error(f"Failed to load queue from disk: {e}")

    async def _persist_queue(self):
        """Save queue to disk"""
        queue_file = self.queue_path / "queue.json"

        try:
            queue_data = [op.to_dict() for op in self.queue]
            async with aiofiles.open(queue_file, 'w') as f:
                await f.write(json.dumps(queue_data, indent=2))
        except Exception as e:
            logger.error(f"Failed to persist queue to disk: {e}")

    async def clear(self):
        """Clear all operations"""
        self.queue.clear()
        if self.config.persist_queue:
            await self._persist_queue()


class OfflineManager:
    """Main offline capability manager"""

    def __init__(self, config: Optional[OfflineConfig] = None):
        self.config = config or OfflineConfig()
        self.connectivity_monitor = ConnectivityMonitor(self.config)
        self.operation_queue = OperationQueue(self.config)
        self.handlers: Dict[OperationType, Callable] = {}
        self.stats = {
            "total_queued": 0,
            "total_synced": 0,
            "failed_syncs": 0,
            "offline_duration_seconds": 0,
            "last_online": None,
            "last_offline": None
        }
        self._monitoring_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._offline_since: Optional[datetime] = None

    async def initialize(self):
        """Initialize offline manager"""
        await self.operation_queue.initialize()

        # Start monitoring
        self._monitoring_task = asyncio.create_task(self._monitor_connectivity())
        self._sync_task = asyncio.create_task(self._sync_operations())

        logger.info("Offline manager initialized")

    async def shutdown(self):
        """Shutdown offline manager"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._sync_task:
            self._sync_task.cancel()

        # Persist remaining queue
        if self.config.persist_queue:
            await self.operation_queue._persist_queue()

        logger.info("Offline manager shutdown")

    def register_handler(self, operation_type: OperationType,
                        handler: Callable) -> None:
        """Register handler for operation type"""
        self.handlers[operation_type] = handler
        logger.info(f"Registered handler for {operation_type.value}")

    async def queue_operation(self, operation_type: OperationType,
                             payload: Dict[str, Any],
                             priority: Priority = Priority.NORMAL) -> str:
        """Queue an operation for execution"""
        operation = QueuedOperation(
            operation_id=f"{operation_type.value}_{datetime.now().timestamp()}",
            operation_type=operation_type,
            priority=priority,
            payload=payload,
            created_at=datetime.now()
        )

        success = await self.operation_queue.enqueue(operation)
        if success:
            self.stats["total_queued"] += 1

        return operation.operation_id

    async def execute_operation(self, operation: QueuedOperation) -> bool:
        """Execute a queued operation"""
        handler = self.handlers.get(operation.operation_type)
        if not handler:
            logger.warning(f"No handler for {operation.operation_type.value}")
            return False

        try:
            result = await handler(operation.payload)
            logger.info(f"Executed operation {operation.operation_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to execute operation {operation.operation_id}: {e}")
            return False

    async def _monitor_connectivity(self):
        """Background task to monitor connectivity"""
        while True:
            try:
                old_status = self.connectivity_monitor.status
                new_status = await self.connectivity_monitor.check_connectivity()

                # Detect status changes
                if old_status == ConnectionStatus.OFFLINE and new_status == ConnectionStatus.ONLINE:
                    logger.info("Connection restored - triggering sync")
                    self.stats["last_online"] = datetime.now()

                    if self._offline_since:
                        offline_duration = (datetime.now() - self._offline_since).total_seconds()
                        self.stats["offline_duration_seconds"] += offline_duration
                        self._offline_since = None

                elif old_status == ConnectionStatus.ONLINE and new_status == ConnectionStatus.OFFLINE:
                    logger.warning("Connection lost - entering offline mode")
                    self.stats["last_offline"] = datetime.now()
                    self._offline_since = datetime.now()

                await asyncio.sleep(self.config.check_interval)
            except Exception as e:
                logger.error(f"Connectivity monitoring error: {e}")
                await asyncio.sleep(self.config.check_interval)

    async def _sync_operations(self):
        """Background task to sync queued operations"""
        while True:
            try:
                # Only sync when online
                if self.connectivity_monitor.is_online():
                    queue_size = self.operation_queue.size()

                    if queue_size > 0:
                        logger.info(f"Syncing {queue_size} queued operations")

                        # Process in batches
                        batch = self.operation_queue.dequeue(self.config.sync_batch_size)

                        for operation in batch:
                            success = await self.execute_operation(operation)

                            if success:
                                self.stats["total_synced"] += 1
                            else:
                                # Retry logic
                                operation.retry_count += 1
                                if operation.retry_count < operation.max_retries:
                                    # Re-queue with exponential backoff
                                    await asyncio.sleep(
                                        self.config.retry_backoff ** operation.retry_count
                                    )
                                    await self.operation_queue.enqueue(operation)
                                else:
                                    logger.error(f"Operation {operation.operation_id} "
                                               f"failed after {operation.max_retries} retries")
                                    self.stats["failed_syncs"] += 1

                        # Persist queue state
                        if self.config.persist_queue:
                            await self.operation_queue._persist_queue()

                await asyncio.sleep(self.config.sync_interval)
            except Exception as e:
                logger.error(f"Sync task error: {e}")
                await asyncio.sleep(self.config.sync_interval)

    def is_online(self) -> bool:
        """Check if currently online"""
        return self.connectivity_monitor.is_online()

    def get_status(self) -> Dict[str, Any]:
        """Get offline manager status"""
        return {
            "connectivity": self.connectivity_monitor.status.value,
            "queue_size": self.operation_queue.size(),
            "consecutive_failures": self.connectivity_monitor.consecutive_failures,
            "last_check": (
                self.connectivity_monitor.last_check.isoformat()
                if self.connectivity_monitor.last_check else None
            ),
            **self.stats
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed statistics"""
        sync_success_rate = (
            self.stats["total_synced"] /
            (self.stats["total_synced"] + self.stats["failed_syncs"])
            if (self.stats["total_synced"] + self.stats["failed_syncs"]) > 0 else 0
        )

        return {
            **self.get_status(),
            "sync_success_rate": sync_success_rate,
            "connectivity_history": list(self.connectivity_monitor.connectivity_history)[-10:]
        }


# Global offline manager instance
_offline_manager = None

def get_offline_manager() -> OfflineManager:
    """Get global offline manager instance"""
    global _offline_manager
    if _offline_manager is None:
        _offline_manager = OfflineManager()
    return _offline_manager
