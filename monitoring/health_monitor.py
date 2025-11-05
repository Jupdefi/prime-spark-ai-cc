"""
Health Monitoring System
Monitors all system components and provides health metrics
"""
import asyncio
import psutil
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component"""
    name: str
    status: HealthStatus
    message: str
    last_check: datetime
    metrics: Dict[str, Any]


class HealthMonitor:
    """
    Monitors health of all system components.

    Components monitored:
    - System resources (CPU, memory, disk)
    - VPN connectivity
    - Memory tiers (Redis, NAS, Cloud)
    - Routing endpoints
    - Agent availability
    - Power status
    """

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start health monitoring"""
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop health monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.check_all_components()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")

    async def check_all_components(self):
        """Check health of all components"""
        await asyncio.gather(
            self.check_system_resources(),
            self.check_vpn(),
            self.check_memory_tiers(),
            self.check_routing(),
            self.check_agents(),
            self.check_power(),
            return_exceptions=True
        )

    async def check_system_resources(self) -> ComponentHealth:
        """Check system resource health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Determine health status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical resource usage"
            elif cpu_percent > 75 or memory.percent > 75 or disk.percent > 85:
                status = HealthStatus.DEGRADED
                message = "High resource usage"
            else:
                status = HealthStatus.HEALTHY
                message = "Normal resource usage"

            health = ComponentHealth(
                name="system_resources",
                status=status,
                message=message,
                last_check=datetime.now(),
                metrics={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
                }
            )

            self.components["system_resources"] = health
            return health

        except Exception as e:
            health = ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking resources: {e}",
                last_check=datetime.now(),
                metrics={}
            )
            self.components["system_resources"] = health
            return health

    async def check_vpn(self) -> ComponentHealth:
        """Check VPN connectivity health"""
        try:
            from vpn.manager import VPNManager

            vpn = VPNManager()
            status = await vpn.get_vpn_status()

            is_active = status.get("is_active", False)
            connected_peers = status.get("connected_peers", 0)
            total_peers = status.get("total_peers", 0)

            if is_active and connected_peers >= total_peers * 0.75:
                health_status = HealthStatus.HEALTHY
                message = f"{connected_peers}/{total_peers} peers connected"
            elif is_active and connected_peers > 0:
                health_status = HealthStatus.DEGRADED
                message = f"Only {connected_peers}/{total_peers} peers connected"
            elif is_active:
                health_status = HealthStatus.DEGRADED
                message = "VPN active but no peers connected"
            else:
                health_status = HealthStatus.UNHEALTHY
                message = "VPN not active"

            health = ComponentHealth(
                name="vpn",
                status=health_status,
                message=message,
                last_check=datetime.now(),
                metrics={
                    "is_active": is_active,
                    "connected_peers": connected_peers,
                    "total_peers": total_peers
                }
            )

            self.components["vpn"] = health
            return health

        except Exception as e:
            health = ComponentHealth(
                name="vpn",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking VPN: {e}",
                last_check=datetime.now(),
                metrics={}
            )
            self.components["vpn"] = health
            return health

    async def check_memory_tiers(self) -> ComponentHealth:
        """Check memory tier health"""
        try:
            from memory.memory_manager import memory

            stats = await memory.get_stats()

            # Simple health check: if we can get stats, it's healthy
            health = ComponentHealth(
                name="memory_tiers",
                status=HealthStatus.HEALTHY,
                message="All memory tiers operational",
                last_check=datetime.now(),
                metrics=stats
            )

            self.components["memory_tiers"] = health
            return health

        except Exception as e:
            health = ComponentHealth(
                name="memory_tiers",
                status=HealthStatus.UNHEALTHY,
                message=f"Error checking memory: {e}",
                last_check=datetime.now(),
                metrics={}
            )
            self.components["memory_tiers"] = health
            return health

    async def check_routing(self) -> ComponentHealth:
        """Check routing system health"""
        try:
            from routing.router import router

            stats = await router.get_routing_stats()
            endpoints = stats.get("endpoints", {})

            healthy_count = sum(1 for e in endpoints.values() if e.get("is_healthy"))
            total_count = len(endpoints)

            if healthy_count == total_count:
                health_status = HealthStatus.HEALTHY
                message = "All endpoints healthy"
            elif healthy_count > 0:
                health_status = HealthStatus.DEGRADED
                message = f"{healthy_count}/{total_count} endpoints healthy"
            else:
                health_status = HealthStatus.UNHEALTHY
                message = "No healthy endpoints"

            health = ComponentHealth(
                name="routing",
                status=health_status,
                message=message,
                last_check=datetime.now(),
                metrics={
                    "healthy_endpoints": healthy_count,
                    "total_endpoints": total_count,
                    "strategy": stats.get("strategy")
                }
            )

            self.components["routing"] = health
            return health

        except Exception as e:
            health = ComponentHealth(
                name="routing",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking routing: {e}",
                last_check=datetime.now(),
                metrics={}
            )
            self.components["routing"] = health
            return health

    async def check_agents(self) -> ComponentHealth:
        """Check agent coordinator health"""
        try:
            from agents.coordinator import coordinator

            status = await coordinator.get_coordinator_status()
            agents = status.get("agents", [])

            online_count = sum(1 for a in agents if a.get("is_online"))
            total_count = len(agents)

            if online_count == total_count:
                health_status = HealthStatus.HEALTHY
                message = "All agents online"
            elif online_count > 0:
                health_status = HealthStatus.DEGRADED
                message = f"{online_count}/{total_count} agents online"
            else:
                health_status = HealthStatus.UNHEALTHY
                message = "No agents online"

            health = ComponentHealth(
                name="agents",
                status=health_status,
                message=message,
                last_check=datetime.now(),
                metrics={
                    "online_agents": online_count,
                    "total_agents": total_count,
                    "tasks": status.get("tasks", {})
                }
            )

            self.components["agents"] = health
            return health

        except Exception as e:
            health = ComponentHealth(
                name="agents",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking agents: {e}",
                last_check=datetime.now(),
                metrics={}
            )
            self.components["agents"] = health
            return health

    async def check_power(self) -> ComponentHealth:
        """Check power system health"""
        try:
            from power.power_manager import power_manager

            stats = await power_manager.get_power_stats()
            battery_state = stats.get("battery_state")
            is_on_battery = stats.get("is_on_battery")

            if battery_state == "critical":
                health_status = HealthStatus.UNHEALTHY
                message = "Battery critical"
            elif battery_state == "low":
                health_status = HealthStatus.DEGRADED
                message = "Battery low"
            elif is_on_battery:
                health_status = HealthStatus.HEALTHY
                message = "Running on battery"
            else:
                health_status = HealthStatus.HEALTHY
                message = "Running on AC power"

            health = ComponentHealth(
                name="power",
                status=health_status,
                message=message,
                last_check=datetime.now(),
                metrics=stats
            )

            self.components["power"] = health
            return health

        except Exception as e:
            health = ComponentHealth(
                name="power",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking power: {e}",
                last_check=datetime.now(),
                metrics={}
            )
            self.components["power"] = health
            return health

    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        if not self.components:
            await self.check_all_components()

        # Determine overall status
        statuses = [c.status for c in self.components.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN

        return {
            "overall_status": overall_status.value,
            "components": {
                name: {
                    "status": comp.status.value,
                    "message": comp.message,
                    "last_check": comp.last_check.isoformat(),
                    "metrics": comp.metrics
                }
                for name, comp in self.components.items()
            }
        }


# Global health monitor instance
health_monitor = HealthMonitor()
