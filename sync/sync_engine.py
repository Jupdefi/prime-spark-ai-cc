"""
Synchronization Engine
Bidirectional data sync between edge and cloud with conflict resolution
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Sync direction"""
    EDGE_TO_CLOUD = "edge_to_cloud"
    CLOUD_TO_EDGE = "cloud_to_edge"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    LATEST_WINS = "latest_wins"
    CLOUD_WINS = "cloud_wins"
    EDGE_WINS = "edge_wins"
    MERGE = "merge"
    MANUAL = "manual"


class SyncStatus(Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class DataType(Enum):
    """Data types for sync"""
    METRICS = "metrics"
    MODELS = "models"
    CONFIGURATIONS = "configurations"
    ARTIFACTS = "artifacts"
    TELEMETRY = "telemetry"


@dataclass
class SyncRecord:
    """Sync record metadata"""
    record_id: str
    data_type: DataType
    source: str  # edge or cloud
    destination: str
    data_hash: str
    version: int
    timestamp: datetime
    size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncOperation:
    """Sync operation"""
    operation_id: str
    direction: SyncDirection
    data_type: DataType
    records: List[SyncRecord]
    status: SyncStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    bytes_transferred: int = 0
    error_message: Optional[str] = None


@dataclass
class ConflictRecord:
    """Conflict record"""
    conflict_id: str
    record_id: str
    edge_version: SyncRecord
    cloud_version: SyncRecord
    detected_at: datetime
    resolution_strategy: ConflictResolutionStrategy
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution: Optional[SyncRecord] = None


@dataclass
class SyncConfig:
    """Synchronization configuration"""
    sync_interval: int = 300  # seconds
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    compression_enabled: bool = True
    encryption_enabled: bool = False
    conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LATEST_WINS
    bandwidth_limit_mbps: Optional[float] = None
    priority_data_types: List[DataType] = field(default_factory=list)


class VersionTracker:
    """Tracks versions of synced data"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.versions: Dict[str, SyncRecord] = {}

    async def initialize(self):
        """Initialize version tracker"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        await self._load_versions()
        logger.info("Version tracker initialized")

    async def _load_versions(self):
        """Load versions from disk"""
        version_file = self.storage_path / "versions.json"
        if version_file.exists():
            try:
                async with aiofiles.open(version_file, 'r') as f:
                    data = await f.read()
                    version_data = json.loads(data)

                for record_id, record_dict in version_data.items():
                    self.versions[record_id] = SyncRecord(
                        record_id=record_dict["record_id"],
                        data_type=DataType(record_dict["data_type"]),
                        source=record_dict["source"],
                        destination=record_dict["destination"],
                        data_hash=record_dict["data_hash"],
                        version=record_dict["version"],
                        timestamp=datetime.fromisoformat(record_dict["timestamp"]),
                        size_bytes=record_dict["size_bytes"],
                        metadata=record_dict.get("metadata", {})
                    )
            except Exception as e:
                logger.error(f"Failed to load versions: {e}")

    async def _save_versions(self):
        """Save versions to disk"""
        version_file = self.storage_path / "versions.json"
        try:
            version_data = {
                record_id: {
                    "record_id": record.record_id,
                    "data_type": record.data_type.value,
                    "source": record.source,
                    "destination": record.destination,
                    "data_hash": record.data_hash,
                    "version": record.version,
                    "timestamp": record.timestamp.isoformat(),
                    "size_bytes": record.size_bytes,
                    "metadata": record.metadata
                }
                for record_id, record in self.versions.items()
            }

            async with aiofiles.open(version_file, 'w') as f:
                await f.write(json.dumps(version_data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save versions: {e}")

    def get_version(self, record_id: str) -> Optional[SyncRecord]:
        """Get version for record"""
        return self.versions.get(record_id)

    async def update_version(self, record: SyncRecord):
        """Update version for record"""
        self.versions[record.record_id] = record
        await self._save_versions()

    def has_conflict(self, edge_record: SyncRecord,
                    cloud_record: SyncRecord) -> bool:
        """Check if records have conflict"""
        # Same version, no conflict
        if edge_record.version == cloud_record.version:
            return False

        # Same hash, no conflict (identical data)
        if edge_record.data_hash == cloud_record.data_hash:
            return False

        # Different versions and different data = conflict
        return True


class ConflictResolver:
    """Resolves sync conflicts"""

    def __init__(self, strategy: ConflictResolutionStrategy):
        self.strategy = strategy
        self.conflicts: Dict[str, ConflictRecord] = {}

    def detect_conflict(self, edge_record: SyncRecord,
                       cloud_record: SyncRecord) -> Optional[ConflictRecord]:
        """Detect conflict between versions"""
        # Check if versions differ
        if edge_record.data_hash == cloud_record.data_hash:
            return None  # No conflict, identical data

        # Create conflict record
        conflict_id = f"conflict-{edge_record.record_id}-{datetime.now().timestamp()}"
        conflict = ConflictRecord(
            conflict_id=conflict_id,
            record_id=edge_record.record_id,
            edge_version=edge_record,
            cloud_version=cloud_record,
            detected_at=datetime.now(),
            resolution_strategy=self.strategy
        )

        self.conflicts[conflict_id] = conflict
        logger.warning(f"Conflict detected: {conflict_id}")

        return conflict

    async def resolve_conflict(self, conflict: ConflictRecord) -> SyncRecord:
        """Resolve conflict based on strategy"""
        if conflict.resolution_strategy == ConflictResolutionStrategy.LATEST_WINS:
            return self._resolve_latest_wins(conflict)
        elif conflict.resolution_strategy == ConflictResolutionStrategy.CLOUD_WINS:
            return conflict.cloud_version
        elif conflict.resolution_strategy == ConflictResolutionStrategy.EDGE_WINS:
            return conflict.edge_version
        elif conflict.resolution_strategy == ConflictResolutionStrategy.MERGE:
            return await self._resolve_merge(conflict)
        else:
            # MANUAL - requires human intervention
            logger.error(f"Manual resolution required for conflict: {conflict.conflict_id}")
            raise ValueError("Manual conflict resolution required")

    def _resolve_latest_wins(self, conflict: ConflictRecord) -> SyncRecord:
        """Resolve using latest timestamp"""
        if conflict.edge_version.timestamp > conflict.cloud_version.timestamp:
            logger.info(f"Conflict resolved: edge wins (latest)")
            return conflict.edge_version
        else:
            logger.info(f"Conflict resolved: cloud wins (latest)")
            return conflict.cloud_version

    async def _resolve_merge(self, conflict: ConflictRecord) -> SyncRecord:
        """Attempt to merge conflicting versions"""
        # TODO: Implement intelligent merge logic
        # For now, fallback to latest wins
        logger.warning("Merge strategy not fully implemented, using latest wins")
        return self._resolve_latest_wins(conflict)


class BandwidthOptimizer:
    """Optimizes data transfer bandwidth"""

    def __init__(self, bandwidth_limit_mbps: Optional[float] = None):
        self.bandwidth_limit_mbps = bandwidth_limit_mbps
        self.transfer_history: List[Dict[str, Any]] = []
        self.current_transfer_rate = 0.0

    async def throttle(self, bytes_to_transfer: int):
        """Throttle transfer based on bandwidth limit"""
        if not self.bandwidth_limit_mbps:
            return  # No throttling

        # Calculate delay needed
        max_bytes_per_second = (self.bandwidth_limit_mbps * 1024 * 1024) / 8
        transfer_time = bytes_to_transfer / max_bytes_per_second

        if transfer_time > 0.1:  # Only throttle for transfers > 100ms
            await asyncio.sleep(transfer_time)

    def should_compress(self, size_bytes: int, data_type: DataType) -> bool:
        """Determine if data should be compressed"""
        # Compress if size > 1MB and not already compressed format
        if size_bytes > 1024 * 1024:
            # Don't compress already compressed formats
            if data_type in [DataType.MODELS]:  # Models may already be compressed
                return False
            return True
        return False

    def calculate_priority_score(self, record: SyncRecord,
                                 priority_types: List[DataType]) -> float:
        """Calculate priority score for record"""
        base_score = 1.0

        # Higher priority for configured types
        if record.data_type in priority_types:
            base_score *= 2.0

        # Lower priority for large files (bandwidth conservation)
        if record.size_bytes > 10 * 1024 * 1024:  # > 10MB
            base_score *= 0.5

        # Higher priority for recent data
        age_hours = (datetime.now() - record.timestamp).total_seconds() / 3600
        if age_hours < 1:
            base_score *= 1.5

        return base_score


class SyncEngine:
    """Main synchronization engine"""

    def __init__(self, config: Optional[SyncConfig] = None,
                storage_path: str = "/var/lib/prime-spark/sync"):
        self.config = config or SyncConfig()
        self.storage_path = Path(storage_path)
        self.version_tracker = VersionTracker(str(self.storage_path / "versions"))
        self.conflict_resolver = ConflictResolver(self.config.conflict_strategy)
        self.bandwidth_optimizer = BandwidthOptimizer(self.config.bandwidth_limit_mbps)
        self.operations: Dict[str, SyncOperation] = {}
        self.running = False
        self.stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "bytes_transferred": 0
        }

    async def initialize(self):
        """Initialize sync engine"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        await self.version_tracker.initialize()

        # Start background sync loop
        asyncio.create_task(self._sync_loop())

        self.running = True
        logger.info("Sync engine initialized")

    async def sync_data(self, records: List[SyncRecord],
                       direction: SyncDirection) -> SyncOperation:
        """Synchronize data records"""
        operation_id = f"sync-{datetime.now().timestamp()}"

        operation = SyncOperation(
            operation_id=operation_id,
            direction=direction,
            data_type=records[0].data_type if records else DataType.METRICS,
            records=records,
            status=SyncStatus.PENDING,
            created_at=datetime.now()
        )

        self.operations[operation_id] = operation
        self.stats["total_syncs"] += 1

        # Process sync asynchronously
        asyncio.create_task(self._process_sync(operation))

        return operation

    async def _process_sync(self, operation: SyncOperation):
        """Process sync operation"""
        operation.status = SyncStatus.IN_PROGRESS
        operation.started_at = datetime.now()

        try:
            # Sort records by priority
            sorted_records = self._prioritize_records(operation.records)

            # Process records in batches
            for i in range(0, len(sorted_records), self.config.batch_size):
                batch = sorted_records[i:i + self.config.batch_size]

                for record in batch:
                    # Check for conflicts
                    existing_version = self.version_tracker.get_version(record.record_id)

                    if existing_version:
                        # Detect conflicts
                        if operation.direction == SyncDirection.EDGE_TO_CLOUD:
                            cloud_version = existing_version
                            edge_version = record
                        else:
                            edge_version = existing_version
                            cloud_version = record

                        if self.version_tracker.has_conflict(edge_version, cloud_version):
                            # Conflict detected
                            conflict = self.conflict_resolver.detect_conflict(
                                edge_version, cloud_version
                            )
                            self.stats["conflicts_detected"] += 1

                            # Resolve conflict
                            resolved_record = await self.conflict_resolver.resolve_conflict(conflict)
                            self.stats["conflicts_resolved"] += 1
                            record = resolved_record

                    # Transfer data with bandwidth throttling
                    await self.bandwidth_optimizer.throttle(record.size_bytes)

                    # Update version
                    await self.version_tracker.update_version(record)

                    operation.bytes_transferred += record.size_bytes
                    self.stats["bytes_transferred"] += record.size_bytes

            # Mark success
            operation.status = SyncStatus.COMPLETED
            operation.completed_at = datetime.now()
            self.stats["successful_syncs"] += 1

            logger.info(f"Sync operation {operation.operation_id} completed successfully")

        except Exception as e:
            operation.status = SyncStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()
            self.stats["failed_syncs"] += 1

            logger.error(f"Sync operation {operation.operation_id} failed: {e}")

    def _prioritize_records(self, records: List[SyncRecord]) -> List[SyncRecord]:
        """Prioritize records for sync"""
        # Calculate priority scores
        scored_records = [
            (record, self.bandwidth_optimizer.calculate_priority_score(
                record, self.config.priority_data_types
            ))
            for record in records
        ]

        # Sort by priority (higher first)
        scored_records.sort(key=lambda x: x[1], reverse=True)

        return [record for record, _ in scored_records]

    async def _sync_loop(self):
        """Background sync loop"""
        while self.running:
            try:
                # Auto-sync logic would go here
                # For now, just sleep
                await asyncio.sleep(self.config.sync_interval)

                # Check for pending syncs
                # TODO: Implement auto-sync discovery

            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(self.config.sync_interval)

    def get_sync_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get sync operation status"""
        operation = self.operations.get(operation_id)
        if not operation:
            return None

        return {
            "operation_id": operation.operation_id,
            "status": operation.status.value,
            "direction": operation.direction.value,
            "records_count": len(operation.records),
            "bytes_transferred": operation.bytes_transferred,
            "started_at": operation.started_at.isoformat() if operation.started_at else None,
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "error": operation.error_message
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get sync engine statistics"""
        success_rate = (
            self.stats["successful_syncs"] / self.stats["total_syncs"]
            if self.stats["total_syncs"] > 0 else 0
        )

        conflict_resolution_rate = (
            self.stats["conflicts_resolved"] / self.stats["conflicts_detected"]
            if self.stats["conflicts_detected"] > 0 else 0
        )

        return {
            **self.stats,
            "success_rate": success_rate,
            "conflict_resolution_rate": conflict_resolution_rate,
            "pending_conflicts": len([c for c in self.conflict_resolver.conflicts.values() if not c.resolved]),
            "active_operations": sum(1 for op in self.operations.values() if op.status == SyncStatus.IN_PROGRESS)
        }

    async def shutdown(self):
        """Shutdown sync engine"""
        self.running = False
        await self.version_tracker._save_versions()
        logger.info("Sync engine shutdown")


# Global sync engine instance
_sync_engine = None

def get_sync_engine() -> SyncEngine:
    """Get global sync engine instance"""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = SyncEngine()
    return _sync_engine
