#!/usr/bin/env python3
"""
Pulse Agent - The Heartbeat of Prime Spark AI

Monitors health, status, and performance across all Prime Spark infrastructure:
- 4 PrimeCore VPS nodes
- Pi 5 edge infrastructure
- N8N workflows (140+)
- AI agents
- Network connectivity
- System resources

Architecture follows engineering team's design:
- FastAPI REST API
- Event-driven monitoring
- Redis caching
- Prometheus metrics
- Notion integration
"""

import os
import asyncio
import logging
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pironman5/prime-spark-ai/logs/pulse_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ===== DATA MODELS =====

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class NodeType(str, Enum):
    """Types of nodes in the infrastructure."""
    EDGE = "edge"
    PRIMECORE = "primecore"
    NAS = "nas"
    AGENT = "agent"


@dataclass
class NodeHealth:
    """Health status of a single node."""
    node_id: str
    node_type: NodeType
    status: HealthStatus
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: int
    last_check: datetime
    services: Dict[str, bool]
    errors: List[str]

    def to_dict(self):
        return {
            **asdict(self),
            'last_check': self.last_check.isoformat(),
            'node_type': self.node_type.value,
            'status': self.status.value
        }


@dataclass
class Alert:
    """System alert."""
    alert_id: str
    severity: str  # critical, warning, info
    node_id: str
    message: str
    timestamp: datetime
    resolved: bool

    def to_dict(self):
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


# ===== API MODELS =====

class HealthResponse(BaseModel):
    """Response model for health endpoints."""
    status: str
    timestamp: str
    nodes_total: int
    nodes_healthy: int
    nodes_degraded: int
    nodes_unhealthy: int


class MetricsResponse(BaseModel):
    """Response model for metrics endpoints."""
    node_id: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: int
    timestamp: str


class ServiceRestartRequest(BaseModel):
    """Request to restart a service."""
    node_id: str
    force: bool = False


# ===== PULSE AGENT CORE =====

class PulseAgent:
    """
    The Heartbeat Agent - monitors all Prime Spark infrastructure.
    """

    def __init__(self):
        """Initialize Pulse agent."""
        logger.info("🫀 Initializing Pulse Agent - The Heartbeat of Prime Spark")

        # Configuration
        self.check_interval = 30  # seconds
        self.alert_threshold = {
            'cpu': 90.0,
            'memory': 85.0,
            'disk': 90.0
        }

        # State
        self.nodes: Dict[str, NodeHealth] = {}
        self.alerts: List[Alert] = []
        self.metrics_history: Dict[str, List[Dict]] = {}

        # Redis cache (optional, falls back gracefully)
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️  Redis not available: {e}")
            self.redis_client = None
            self.cache_enabled = False

        # Load configuration
        self._load_config()

        # Initialize monitoring targets
        self._initialize_targets()

        logger.info("✅ Pulse Agent initialized successfully")

    def _load_config(self):
        """Load configuration from environment."""
        self.primecore_nodes = [
            {
                'id': 'primecore1',
                'ip': os.getenv('PRIMECORE1_IP', '141.136.35.51'),
                'port': int(os.getenv('PRIMECORE1_PORT', '443'))
            },
            {
                'id': 'primecore2',
                'ip': os.getenv('PRIMECORE2_IP', ''),
                'port': int(os.getenv('PRIMECORE2_PORT', '443'))
            },
            {
                'id': 'primecore3',
                'ip': os.getenv('PRIMECORE3_IP', ''),
                'port': int(os.getenv('PRIMECORE3_PORT', '443'))
            },
            {
                'id': 'primecore4',
                'ip': os.getenv('PRIMECORE4_IP', '69.62.123.97'),
                'port': int(os.getenv('PRIMECORE4_PORT', '443'))
            }
        ]

        self.edge_node = {
            'id': 'edge_pi5',
            'ip': 'localhost'
        }

    def _initialize_targets(self):
        """Initialize monitoring targets."""
        # Edge node (this Pi 5)
        self.nodes['edge_pi5'] = NodeHealth(
            node_id='edge_pi5',
            node_type=NodeType.EDGE,
            status=HealthStatus.UNKNOWN,
            cpu_percent=0.0,
            memory_percent=0.0,
            disk_percent=0.0,
            uptime_seconds=0,
            last_check=datetime.now(),
            services={},
            errors=[]
        )

        # PrimeCore nodes
        for node in self.primecore_nodes:
            if node['ip']:  # Only add if IP is configured
                self.nodes[node['id']] = NodeHealth(
                    node_id=node['id'],
                    node_type=NodeType.PRIMECORE,
                    status=HealthStatus.UNKNOWN,
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    disk_percent=0.0,
                    uptime_seconds=0,
                    last_check=datetime.now(),
                    services={},
                    errors=[]
                )

    async def check_edge_health(self) -> NodeHealth:
        """Check health of edge node (this Pi 5)."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            uptime = int((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds())

            # Check services
            services = {}
            try:
                # Check if pironman5 service is running
                import subprocess
                result = subprocess.run(
                    ['systemctl', 'is-active', 'pironman5.service'],
                    capture_output=True,
                    text=True
                )
                services['pironman5'] = result.returncode == 0

                # Check hailort service
                result = subprocess.run(
                    ['systemctl', 'is-active', 'hailort.service'],
                    capture_output=True,
                    text=True
                )
                services['hailort'] = result.returncode == 0

                # Check ollama service
                result = subprocess.run(
                    ['systemctl', 'is-active', 'ollama.service'],
                    capture_output=True,
                    text=True
                )
                services['ollama'] = result.returncode == 0

            except Exception as e:
                logger.error(f"Error checking services: {e}")

            # Determine status
            errors = []
            if cpu_percent > self.alert_threshold['cpu']:
                errors.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > self.alert_threshold['memory']:
                errors.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > self.alert_threshold['disk']:
                errors.append(f"High disk usage: {disk.percent:.1f}%")

            if not all(services.values()):
                errors.append("Some services are not running")

            if errors:
                status = HealthStatus.DEGRADED if len(errors) < 2 else HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.HEALTHY

            node_health = NodeHealth(
                node_id='edge_pi5',
                node_type=NodeType.EDGE,
                status=status,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                uptime_seconds=uptime,
                last_check=datetime.now(),
                services=services,
                errors=errors
            )

            self.nodes['edge_pi5'] = node_health
            return node_health

        except Exception as e:
            logger.error(f"Error checking edge health: {e}")
            return NodeHealth(
                node_id='edge_pi5',
                node_type=NodeType.EDGE,
                status=HealthStatus.UNKNOWN,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                uptime_seconds=0,
                last_check=datetime.now(),
                services={},
                errors=[str(e)]
            )

    async def check_primecore_health(self, node_id: str) -> NodeHealth:
        """Check health of a PrimeCore node."""
        node_config = next((n for n in self.primecore_nodes if n['id'] == node_id), None)
        if not node_config or not node_config['ip']:
            return NodeHealth(
                node_id=node_id,
                node_type=NodeType.PRIMECORE,
                status=HealthStatus.UNKNOWN,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                uptime_seconds=0,
                last_check=datetime.now(),
                services={},
                errors=['Node not configured']
            )

        try:
            # Try to reach the node
            # In production, this would check actual health endpoints
            # For now, we check basic connectivity
            response = requests.get(
                f"http://{node_config['ip']}:8000/health",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                node_health = NodeHealth(
                    node_id=node_id,
                    node_type=NodeType.PRIMECORE,
                    status=HealthStatus.HEALTHY,
                    cpu_percent=data.get('cpu_percent', 0.0),
                    memory_percent=data.get('memory_percent', 0.0),
                    disk_percent=data.get('disk_percent', 0.0),
                    uptime_seconds=data.get('uptime_seconds', 0),
                    last_check=datetime.now(),
                    services=data.get('services', {}),
                    errors=[]
                )
            else:
                node_health = NodeHealth(
                    node_id=node_id,
                    node_type=NodeType.PRIMECORE,
                    status=HealthStatus.DEGRADED,
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    disk_percent=0.0,
                    uptime_seconds=0,
                    last_check=datetime.now(),
                    services={},
                    errors=[f'HTTP {response.status_code}']
                )

            self.nodes[node_id] = node_health
            return node_health

        except requests.exceptions.Timeout:
            node_health = NodeHealth(
                node_id=node_id,
                node_type=NodeType.PRIMECORE,
                status=HealthStatus.UNHEALTHY,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                uptime_seconds=0,
                last_check=datetime.now(),
                services={},
                errors=['Connection timeout']
            )
            self.nodes[node_id] = node_health
            return node_health

        except Exception as e:
            logger.error(f"Error checking {node_id}: {e}")
            node_health = NodeHealth(
                node_id=node_id,
                node_type=NodeType.PRIMECORE,
                status=HealthStatus.UNKNOWN,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                uptime_seconds=0,
                last_check=datetime.now(),
                services={},
                errors=[str(e)]
            )
            self.nodes[node_id] = node_health
            return node_health

    async def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("🔄 Starting monitoring loop...")

        while True:
            try:
                # Check edge node
                await self.check_edge_health()

                # Check PrimeCore nodes
                for node in self.primecore_nodes:
                    if node['ip']:
                        await self.check_primecore_health(node['id'])

                # Check for alerts
                self._check_alerts()

                # Cache to Redis if available
                if self.cache_enabled:
                    self._cache_metrics()

                # Log status
                healthy = sum(1 for n in self.nodes.values() if n.status == HealthStatus.HEALTHY)
                degraded = sum(1 for n in self.nodes.values() if n.status == HealthStatus.DEGRADED)
                unhealthy = sum(1 for n in self.nodes.values() if n.status == HealthStatus.UNHEALTHY)

                logger.info(
                    f"🫀 Heartbeat: {healthy} healthy, {degraded} degraded, "
                    f"{unhealthy} unhealthy (total: {len(self.nodes)})"
                )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Sleep until next check
            await asyncio.sleep(self.check_interval)

    def _check_alerts(self):
        """Check for alert conditions."""
        for node_id, node in self.nodes.items():
            if node.errors:
                # Create alerts for errors
                for error in node.errors:
                    alert_id = f"{node_id}_{error[:20]}_{int(datetime.now().timestamp())}"
                    alert = Alert(
                        alert_id=alert_id,
                        severity='critical' if node.status == HealthStatus.UNHEALTHY else 'warning',
                        node_id=node_id,
                        message=error,
                        timestamp=datetime.now(),
                        resolved=False
                    )
                    self.alerts.append(alert)
                    logger.warning(f"⚠️  Alert: {node_id} - {error}")

    def _cache_metrics(self):
        """Cache current metrics to Redis."""
        if not self.cache_enabled:
            return

        try:
            # Store current metrics with 5 minute TTL
            for node_id, node in self.nodes.items():
                key = f"pulse:metrics:{node_id}"
                self.redis_client.setex(
                    key,
                    300,  # 5 minutes
                    str(node.to_dict())
                )
        except Exception as e:
            logger.error(f"Error caching metrics: {e}")

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        healthy = sum(1 for n in self.nodes.values() if n.status == HealthStatus.HEALTHY)
        degraded = sum(1 for n in self.nodes.values() if n.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for n in self.nodes.values() if n.status == HealthStatus.UNHEALTHY)
        unknown = sum(1 for n in self.nodes.values() if n.status == HealthStatus.UNKNOWN)

        overall_status = HealthStatus.HEALTHY
        if unhealthy > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_status = HealthStatus.DEGRADED
        elif unknown == len(self.nodes):
            overall_status = HealthStatus.UNKNOWN

        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'nodes_total': len(self.nodes),
            'nodes_healthy': healthy,
            'nodes_degraded': degraded,
            'nodes_unhealthy': unhealthy,
            'nodes_unknown': unknown,
            'alerts_active': len([a for a in self.alerts if not a.resolved])
        }


# ===== FASTAPI APPLICATION =====

app = FastAPI(
    title="Pulse Agent API",
    description="The Heartbeat of Prime Spark AI - System Health Monitor",
    version="1.0.0"
)

# Initialize Pulse agent
pulse = PulseAgent()


@app.on_event("startup")
async def startup_event():
    """Start monitoring loop on startup."""
    asyncio.create_task(pulse.monitor_loop())


@app.get("/pulse/health")
async def get_health():
    """Get overall system health."""
    return pulse.get_overall_health()


@app.get("/pulse/nodes")
async def get_all_nodes():
    """Get health status of all nodes."""
    return {
        'nodes': [node.to_dict() for node in pulse.nodes.values()],
        'timestamp': datetime.now().isoformat()
    }


@app.get("/pulse/nodes/{node_id}")
async def get_node_health(node_id: str):
    """Get health status of a specific node."""
    if node_id not in pulse.nodes:
        raise HTTPException(status_code=404, detail="Node not found")

    return pulse.nodes[node_id].to_dict()


@app.get("/pulse/alerts")
async def get_alerts(active_only: bool = True):
    """Get system alerts."""
    alerts = pulse.alerts
    if active_only:
        alerts = [a for a in alerts if not a.resolved]

    return {
        'alerts': [alert.to_dict() for alert in alerts],
        'count': len(alerts)
    }


@app.get("/pulse/metrics")
async def get_metrics():
    """Get prometheus-compatible metrics."""
    metrics = []

    for node_id, node in pulse.nodes.items():
        metrics.append(f"pulse_cpu_percent{{node=\"{node_id}\"}} {node.cpu_percent}")
        metrics.append(f"pulse_memory_percent{{node=\"{node_id}\"}} {node.memory_percent}")
        metrics.append(f"pulse_disk_percent{{node=\"{node_id}\"}} {node.disk_percent}")
        metrics.append(f"pulse_uptime_seconds{{node=\"{node_id}\"}} {node.uptime_seconds}")
        metrics.append(f"pulse_status{{node=\"{node_id}\",status=\"{node.status.value}\"}} 1")

    return "\n".join(metrics)


@app.post("/pulse/restart/{service_id}")
async def restart_service(service_id: str, request: ServiceRestartRequest):
    """Restart a service (auto-healing)."""
    # This would implement actual service restart logic
    # For now, return a placeholder response
    return {
        'service_id': service_id,
        'node_id': request.node_id,
        'status': 'restart_scheduled',
        'timestamp': datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint - basic info."""
    return {
        'agent': 'Pulse',
        'description': 'The Heartbeat of Prime Spark AI',
        'version': '1.0.0',
        'status': 'operational',
        'uptime': int((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds())
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Pulse Agent server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
