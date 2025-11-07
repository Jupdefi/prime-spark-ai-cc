"""
Cloud Compute Resource Manager
Scalable compute resource management with auto-scaling and load balancing
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import psutil
import numpy as np

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Compute resource types"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE = "storage"
    NETWORK = "network"


class WorkloadType(Enum):
    """Workload classification"""
    INFERENCE = "inference"
    TRAINING = "training"
    BATCH_PROCESSING = "batch"
    STREAMING = "streaming"
    GENERAL = "general"


class ScalingPolicy(Enum):
    """Auto-scaling policies"""
    TARGET_TRACKING = "target_tracking"  # Scale to maintain target metric
    STEP_SCALING = "step_scaling"        # Scale based on thresholds
    SCHEDULED = "scheduled"              # Scale on schedule
    PREDICTIVE = "predictive"            # Scale based on predictions


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_bytes: int
    disk_percent: float
    network_io: Dict[str, int] = field(default_factory=dict)
    gpu_percent: Optional[float] = None
    gpu_memory_percent: Optional[float] = None


@dataclass
class ComputeNode:
    """Compute node representation"""
    node_id: str
    node_type: str
    status: str
    cpu_cores: int
    memory_gb: float
    gpu_count: int = 0
    current_workloads: int = 0
    max_workloads: int = 10
    metrics: Optional[ResourceMetrics] = None
    labels: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Workload:
    """Workload representation"""
    workload_id: str
    workload_type: WorkloadType
    resource_requirements: Dict[ResourceType, float]
    priority: int = 5  # 1-10, higher is more important
    assigned_node: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingConfig:
    """Auto-scaling configuration"""
    policy: ScalingPolicy
    min_nodes: int = 1
    max_nodes: int = 10
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 80.0
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    cooldown_seconds: int = 300
    check_interval_seconds: int = 60


class ResourceMonitor:
    """Monitors resource utilization"""

    def __init__(self):
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history = 1000

    async def collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_bytes = memory.used

        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # Network I/O
        net_io = psutil.net_io_counters()
        network_io = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }

        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_bytes=memory_bytes,
            disk_percent=disk_percent,
            network_io=network_io
        )

        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)

        return metrics

    def get_average_metrics(self, window_seconds: int = 300) -> Dict[str, float]:
        """Get average metrics over time window"""
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {}

        return {
            "cpu_percent": np.mean([m.cpu_percent for m in recent_metrics]),
            "memory_percent": np.mean([m.memory_percent for m in recent_metrics]),
            "disk_percent": np.mean([m.disk_percent for m in recent_metrics])
        }


class LoadBalancer:
    """Load balancer for workload distribution"""

    def __init__(self):
        self.algorithm = "least_connections"  # Could be: round_robin, least_connections, weighted

    def select_node(self, nodes: List[ComputeNode],
                   workload: Workload) -> Optional[ComputeNode]:
        """Select best node for workload"""
        # Filter available nodes
        available_nodes = [
            node for node in nodes
            if node.status == "ready" and node.current_workloads < node.max_workloads
        ]

        if not available_nodes:
            return None

        # Check resource requirements
        suitable_nodes = []
        for node in available_nodes:
            if self._can_accommodate(node, workload):
                suitable_nodes.append(node)

        if not suitable_nodes:
            return None

        # Apply load balancing algorithm
        if self.algorithm == "least_connections":
            return min(suitable_nodes, key=lambda n: n.current_workloads)
        elif self.algorithm == "round_robin":
            return suitable_nodes[0]  # Simplified
        else:
            return suitable_nodes[0]

    def _can_accommodate(self, node: ComputeNode, workload: Workload) -> bool:
        """Check if node can accommodate workload"""
        # Check CPU requirement
        cpu_required = workload.resource_requirements.get(ResourceType.CPU, 0)
        if node.metrics:
            cpu_available = 100 - node.metrics.cpu_percent
            if cpu_required > cpu_available:
                return False

        # Check memory requirement
        memory_required = workload.resource_requirements.get(ResourceType.MEMORY, 0)
        if node.metrics:
            memory_available = 100 - node.metrics.memory_percent
            if memory_required > memory_available:
                return False

        # Check GPU requirement
        gpu_required = workload.resource_requirements.get(ResourceType.GPU, 0)
        if gpu_required > 0 and node.gpu_count == 0:
            return False

        return True


class AutoScaler:
    """Auto-scaling manager"""

    def __init__(self, config: ScalingConfig):
        self.config = config
        self.last_scale_time: Optional[datetime] = None
        self.current_nodes = config.min_nodes
        self.scaling_history: List[Dict[str, Any]] = []

    async def evaluate_scaling(self, metrics: Dict[str, float],
                              current_workloads: int) -> Optional[int]:
        """Evaluate if scaling is needed"""
        # Check cooldown
        if self.last_scale_time:
            elapsed = (datetime.now() - self.last_scale_time).total_seconds()
            if elapsed < self.config.cooldown_seconds:
                return None

        target_nodes = self.current_nodes

        if self.config.policy == ScalingPolicy.TARGET_TRACKING:
            target_nodes = self._target_tracking_scaling(metrics)
        elif self.config.policy == ScalingPolicy.STEP_SCALING:
            target_nodes = self._step_scaling(metrics)

        # Enforce limits
        target_nodes = max(self.config.min_nodes, min(target_nodes, self.config.max_nodes))

        if target_nodes != self.current_nodes:
            logger.info(f"Scaling from {self.current_nodes} to {target_nodes} nodes")
            self.last_scale_time = datetime.now()
            self.scaling_history.append({
                "timestamp": datetime.now(),
                "from_nodes": self.current_nodes,
                "to_nodes": target_nodes,
                "reason": "auto_scaling",
                "metrics": metrics
            })
            self.current_nodes = target_nodes
            return target_nodes

        return None

    def _target_tracking_scaling(self, metrics: Dict[str, float]) -> int:
        """Target tracking scaling logic"""
        cpu_percent = metrics.get("cpu_percent", 0)
        memory_percent = metrics.get("memory_percent", 0)

        # Calculate desired nodes based on target CPU
        if cpu_percent > 0:
            desired_nodes_cpu = int(np.ceil(
                self.current_nodes * cpu_percent / self.config.target_cpu_percent
            ))
        else:
            desired_nodes_cpu = self.current_nodes

        # Calculate desired nodes based on target memory
        if memory_percent > 0:
            desired_nodes_memory = int(np.ceil(
                self.current_nodes * memory_percent / self.config.target_memory_percent
            ))
        else:
            desired_nodes_memory = self.current_nodes

        # Use max of the two
        return max(desired_nodes_cpu, desired_nodes_memory)

    def _step_scaling(self, metrics: Dict[str, float]) -> int:
        """Step scaling logic"""
        cpu_percent = metrics.get("cpu_percent", 0)
        memory_percent = metrics.get("memory_percent", 0)
        max_utilization = max(cpu_percent, memory_percent)

        if max_utilization > self.config.scale_up_threshold:
            # Scale up
            return self.current_nodes + 1
        elif max_utilization < self.config.scale_down_threshold:
            # Scale down
            return self.current_nodes - 1

        return self.current_nodes


class ComputeManager:
    """Main compute resource manager"""

    def __init__(self, scaling_config: Optional[ScalingConfig] = None):
        self.scaling_config = scaling_config or ScalingConfig()
        self.nodes: Dict[str, ComputeNode] = {}
        self.workloads: Dict[str, Workload] = {}
        self.monitor = ResourceMonitor()
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler(self.scaling_config)
        self.running = False
        self.stats = {
            "total_nodes": 0,
            "active_nodes": 0,
            "total_workloads": 0,
            "completed_workloads": 0,
            "failed_workloads": 0,
            "total_scale_events": 0
        }

    async def initialize(self):
        """Initialize compute manager"""
        # Create initial nodes
        for i in range(self.scaling_config.min_nodes):
            await self.add_node(
                node_type="standard",
                cpu_cores=4,
                memory_gb=8.0
            )

        # Start monitoring
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._scaling_loop())

        self.running = True
        logger.info("Compute Manager initialized")

    async def add_node(self, node_type: str, cpu_cores: int,
                      memory_gb: float, gpu_count: int = 0,
                      labels: Optional[Dict[str, str]] = None) -> str:
        """Add compute node"""
        node_id = f"node-{datetime.now().timestamp()}"

        node = ComputeNode(
            node_id=node_id,
            node_type=node_type,
            status="ready",
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            gpu_count=gpu_count,
            labels=labels or {}
        )

        self.nodes[node_id] = node
        self.stats["total_nodes"] += 1
        self.stats["active_nodes"] += 1

        logger.info(f"Added compute node: {node_id}")
        return node_id

    async def remove_node(self, node_id: str):
        """Remove compute node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]

            # Check if node has workloads
            if node.current_workloads > 0:
                logger.warning(f"Node {node_id} has active workloads, draining...")
                # TODO: Implement graceful drainage

            del self.nodes[node_id]
            self.stats["active_nodes"] -= 1
            logger.info(f"Removed compute node: {node_id}")

    async def submit_workload(self, workload_type: WorkloadType,
                             resource_requirements: Dict[ResourceType, float],
                             priority: int = 5,
                             metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit workload for execution"""
        workload_id = f"workload-{datetime.now().timestamp()}"

        workload = Workload(
            workload_id=workload_id,
            workload_type=workload_type,
            resource_requirements=resource_requirements,
            priority=priority,
            metadata=metadata or {}
        )

        self.workloads[workload_id] = workload
        self.stats["total_workloads"] += 1

        # Try to schedule immediately
        await self._schedule_workload(workload)

        return workload_id

    async def _schedule_workload(self, workload: Workload):
        """Schedule workload to node"""
        # Select node using load balancer
        nodes = list(self.nodes.values())
        selected_node = self.load_balancer.select_node(nodes, workload)

        if selected_node:
            workload.assigned_node = selected_node.node_id
            workload.status = "running"
            workload.started_at = datetime.now()
            selected_node.current_workloads += 1

            logger.info(f"Scheduled workload {workload.workload_id} to {selected_node.node_id}")

            # Simulate workload execution
            asyncio.create_task(self._execute_workload(workload))
        else:
            logger.warning(f"No suitable node for workload {workload.workload_id}")

    async def _execute_workload(self, workload: Workload):
        """Execute workload (placeholder)"""
        # Simulate execution time
        execution_time = np.random.uniform(5, 30)
        await asyncio.sleep(execution_time)

        # Complete workload
        workload.status = "completed"
        workload.completed_at = datetime.now()
        self.stats["completed_workloads"] += 1

        # Release node
        if workload.assigned_node and workload.assigned_node in self.nodes:
            self.nodes[workload.assigned_node].current_workloads -= 1

        logger.info(f"Workload {workload.workload_id} completed")

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Collect metrics for all nodes
                for node in self.nodes.values():
                    if node.status == "ready":
                        metrics = await self.monitor.collect_metrics()
                        node.metrics = metrics

                await asyncio.sleep(10)  # Monitor every 10 seconds
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    async def _scaling_loop(self):
        """Background auto-scaling loop"""
        while self.running:
            try:
                # Get average metrics
                avg_metrics = self.monitor.get_average_metrics(
                    self.scaling_config.check_interval_seconds
                )

                if avg_metrics:
                    # Get current workload count
                    current_workloads = sum(
                        1 for w in self.workloads.values()
                        if w.status == "running"
                    )

                    # Evaluate scaling
                    target_nodes = await self.auto_scaler.evaluate_scaling(
                        avg_metrics,
                        current_workloads
                    )

                    if target_nodes:
                        current_count = len(self.nodes)

                        if target_nodes > current_count:
                            # Scale up
                            for _ in range(target_nodes - current_count):
                                await self.add_node("standard", 4, 8.0)
                                self.stats["total_scale_events"] += 1

                        elif target_nodes < current_count:
                            # Scale down
                            nodes_to_remove = list(self.nodes.keys())[:current_count - target_nodes]
                            for node_id in nodes_to_remove:
                                await self.remove_node(node_id)
                                self.stats["total_scale_events"] += 1

                await asyncio.sleep(self.scaling_config.check_interval_seconds)
            except Exception as e:
                logger.error(f"Scaling error: {e}")

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status"""
        total_cpu_cores = sum(n.cpu_cores for n in self.nodes.values())
        total_memory_gb = sum(n.memory_gb for n in self.nodes.values())
        total_gpus = sum(n.gpu_count for n in self.nodes.values())

        active_workloads = sum(1 for w in self.workloads.values() if w.status == "running")
        pending_workloads = sum(1 for w in self.workloads.values() if w.status == "pending")

        return {
            "nodes": {
                "total": len(self.nodes),
                "ready": sum(1 for n in self.nodes.values() if n.status == "ready"),
                "total_cpu_cores": total_cpu_cores,
                "total_memory_gb": total_memory_gb,
                "total_gpus": total_gpus
            },
            "workloads": {
                "active": active_workloads,
                "pending": pending_workloads,
                "total": len(self.workloads)
            },
            "scaling": {
                "min_nodes": self.scaling_config.min_nodes,
                "max_nodes": self.scaling_config.max_nodes,
                "target_cpu": self.scaling_config.target_cpu_percent,
                "target_memory": self.scaling_config.target_memory_percent
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get compute manager statistics"""
        completion_rate = (
            self.stats["completed_workloads"] / self.stats["total_workloads"]
            if self.stats["total_workloads"] > 0 else 0
        )

        return {
            **self.stats,
            "completion_rate": completion_rate,
            "cluster_status": self.get_cluster_status()
        }

    async def shutdown(self):
        """Shutdown compute manager"""
        self.running = False
        logger.info("Compute Manager shutdown")


# Global compute manager instance
_compute_manager = None

def get_compute_manager() -> ComputeManager:
    """Get global compute manager instance"""
    global _compute_manager
    if _compute_manager is None:
        _compute_manager = ComputeManager()
    return _compute_manager
