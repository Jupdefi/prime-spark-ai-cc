"""
Intelligent Request Router
Routes requests to edge or cloud based on:
- Model availability
- Compute capacity
- Network latency
- Power state
- Load balancing
"""
import asyncio
import time
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum
import httpx
from config.settings import settings


class ComputeLocation(Enum):
    """Compute location options"""
    EDGE_LOCAL = "edge_local"
    EDGE_SPARK = "edge_spark"
    CLOUD_CORE1 = "cloud_core1"
    CLOUD_CORE4 = "cloud_core4"


@dataclass
class RouteDecision:
    """Routing decision result"""
    location: ComputeLocation
    endpoint: str
    reason: str
    latency_ms: Optional[float] = None


@dataclass
class EndpointHealth:
    """Health status of an endpoint"""
    location: ComputeLocation
    endpoint: str
    is_healthy: bool
    latency_ms: Optional[float]
    last_check: float
    error: Optional[str] = None


class RequestRouter:
    """
    Intelligent request router with edge-first strategy.

    Routing Strategy:
    1. Check power mode (off-grid = edge only)
    2. Check edge availability and capacity
    3. Fall back to cloud if edge unavailable or overloaded
    4. Cache routing decisions for performance
    """

    def __init__(self):
        self.strategy = settings.routing.strategy
        self.edge_timeout = settings.routing.edge_timeout_seconds
        self.cloud_fallback = settings.routing.cloud_fallback_enabled
        self.max_retries = settings.routing.max_retries

        # Endpoint configurations
        self.endpoints = {
            ComputeLocation.EDGE_LOCAL: f"{settings.ollama.edge_url}",
            ComputeLocation.CLOUD_CORE4: f"{settings.ollama.cloud_url}",
            # Add more endpoints as needed
        }

        # Health cache
        self.health_cache: Dict[ComputeLocation, EndpointHealth] = {}
        self.health_cache_ttl = 30  # seconds

    async def check_endpoint_health(
        self,
        location: ComputeLocation,
        endpoint: str
    ) -> EndpointHealth:
        """Check if endpoint is healthy and measure latency"""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{endpoint}/api/tags")
                latency_ms = (time.time() - start_time) * 1000

                is_healthy = response.status_code == 200

                return EndpointHealth(
                    location=location,
                    endpoint=endpoint,
                    is_healthy=is_healthy,
                    latency_ms=latency_ms if is_healthy else None,
                    last_check=time.time()
                )
        except Exception as e:
            return EndpointHealth(
                location=location,
                endpoint=endpoint,
                is_healthy=False,
                latency_ms=None,
                last_check=time.time(),
                error=str(e)
            )

    async def get_endpoint_health(
        self,
        location: ComputeLocation
    ) -> EndpointHealth:
        """Get endpoint health from cache or check fresh"""
        # Check cache
        if location in self.health_cache:
            cached = self.health_cache[location]
            age = time.time() - cached.last_check
            if age < self.health_cache_ttl:
                return cached

        # Check fresh
        endpoint = self.endpoints.get(location)
        if not endpoint:
            return EndpointHealth(
                location=location,
                endpoint="",
                is_healthy=False,
                latency_ms=None,
                last_check=time.time(),
                error="Endpoint not configured"
            )

        health = await self.check_endpoint_health(location, endpoint)
        self.health_cache[location] = health
        return health

    async def route_request(
        self,
        request_type: str,
        power_mode: Literal["on-grid", "off-grid"] = "on-grid",
        prefer_location: Optional[ComputeLocation] = None
    ) -> RouteDecision:
        """
        Route a request to the best available endpoint.

        Args:
            request_type: Type of request (e.g., "llm", "image", "voice")
            power_mode: Current power state
            prefer_location: Preferred location if available

        Returns:
            RouteDecision with selected endpoint
        """
        # Off-grid mode: Edge only
        if power_mode == "off-grid":
            edge_health = await self.get_endpoint_health(ComputeLocation.EDGE_LOCAL)
            if edge_health.is_healthy:
                return RouteDecision(
                    location=ComputeLocation.EDGE_LOCAL,
                    endpoint=edge_health.endpoint,
                    reason="Off-grid mode: using edge compute",
                    latency_ms=edge_health.latency_ms
                )
            else:
                return RouteDecision(
                    location=ComputeLocation.EDGE_LOCAL,
                    endpoint=edge_health.endpoint,
                    reason="Off-grid mode: edge unavailable but no cloud fallback",
                    latency_ms=None
                )

        # On-grid mode: Intelligent routing
        if self.strategy == "edge-first":
            return await self._route_edge_first(request_type, prefer_location)
        elif self.strategy == "cloud-first":
            return await self._route_cloud_first(request_type, prefer_location)
        else:  # balanced
            return await self._route_balanced(request_type, prefer_location)

    async def _route_edge_first(
        self,
        request_type: str,
        prefer_location: Optional[ComputeLocation]
    ) -> RouteDecision:
        """Edge-first routing strategy"""
        # Try edge first
        edge_health = await self.get_endpoint_health(ComputeLocation.EDGE_LOCAL)

        if edge_health.is_healthy:
            return RouteDecision(
                location=ComputeLocation.EDGE_LOCAL,
                endpoint=edge_health.endpoint,
                reason="Edge available and healthy",
                latency_ms=edge_health.latency_ms
            )

        # Fallback to cloud if enabled
        if self.cloud_fallback:
            cloud_health = await self.get_endpoint_health(ComputeLocation.CLOUD_CORE4)
            if cloud_health.is_healthy:
                return RouteDecision(
                    location=ComputeLocation.CLOUD_CORE4,
                    endpoint=cloud_health.endpoint,
                    reason="Edge unavailable, falling back to cloud",
                    latency_ms=cloud_health.latency_ms
                )

        # No healthy endpoints
        return RouteDecision(
            location=ComputeLocation.EDGE_LOCAL,
            endpoint=self.endpoints[ComputeLocation.EDGE_LOCAL],
            reason="No healthy endpoints available",
            latency_ms=None
        )

    async def _route_cloud_first(
        self,
        request_type: str,
        prefer_location: Optional[ComputeLocation]
    ) -> RouteDecision:
        """Cloud-first routing strategy"""
        # Try cloud first
        cloud_health = await self.get_endpoint_health(ComputeLocation.CLOUD_CORE4)

        if cloud_health.is_healthy:
            return RouteDecision(
                location=ComputeLocation.CLOUD_CORE4,
                endpoint=cloud_health.endpoint,
                reason="Cloud-first strategy",
                latency_ms=cloud_health.latency_ms
            )

        # Fallback to edge
        edge_health = await self.get_endpoint_health(ComputeLocation.EDGE_LOCAL)
        if edge_health.is_healthy:
            return RouteDecision(
                location=ComputeLocation.EDGE_LOCAL,
                endpoint=edge_health.endpoint,
                reason="Cloud unavailable, using edge",
                latency_ms=edge_health.latency_ms
            )

        # No healthy endpoints
        return RouteDecision(
            location=ComputeLocation.CLOUD_CORE4,
            endpoint=self.endpoints[ComputeLocation.CLOUD_CORE4],
            reason="No healthy endpoints available",
            latency_ms=None
        )

    async def _route_balanced(
        self,
        request_type: str,
        prefer_location: Optional[ComputeLocation]
    ) -> RouteDecision:
        """Balanced routing strategy - choose lowest latency"""
        # Check both edge and cloud
        edge_health, cloud_health = await asyncio.gather(
            self.get_endpoint_health(ComputeLocation.EDGE_LOCAL),
            self.get_endpoint_health(ComputeLocation.CLOUD_CORE4)
        )

        # Both healthy: choose lowest latency
        if edge_health.is_healthy and cloud_health.is_healthy:
            if edge_health.latency_ms <= cloud_health.latency_ms:
                return RouteDecision(
                    location=ComputeLocation.EDGE_LOCAL,
                    endpoint=edge_health.endpoint,
                    reason=f"Balanced: edge has lower latency ({edge_health.latency_ms:.1f}ms)",
                    latency_ms=edge_health.latency_ms
                )
            else:
                return RouteDecision(
                    location=ComputeLocation.CLOUD_CORE4,
                    endpoint=cloud_health.endpoint,
                    reason=f"Balanced: cloud has lower latency ({cloud_health.latency_ms:.1f}ms)",
                    latency_ms=cloud_health.latency_ms
                )

        # Only edge healthy
        if edge_health.is_healthy:
            return RouteDecision(
                location=ComputeLocation.EDGE_LOCAL,
                endpoint=edge_health.endpoint,
                reason="Balanced: only edge available",
                latency_ms=edge_health.latency_ms
            )

        # Only cloud healthy
        if cloud_health.is_healthy:
            return RouteDecision(
                location=ComputeLocation.CLOUD_CORE4,
                endpoint=cloud_health.endpoint,
                reason="Balanced: only cloud available",
                latency_ms=cloud_health.latency_ms
            )

        # Neither healthy
        return RouteDecision(
            location=ComputeLocation.EDGE_LOCAL,
            endpoint=self.endpoints[ComputeLocation.EDGE_LOCAL],
            reason="No healthy endpoints available",
            latency_ms=None
        )

    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        stats = {
            "strategy": self.strategy,
            "endpoints": {}
        }

        for location, endpoint in self.endpoints.items():
            health = await self.get_endpoint_health(location)
            stats["endpoints"][location.value] = {
                "endpoint": endpoint,
                "is_healthy": health.is_healthy,
                "latency_ms": health.latency_ms,
                "error": health.error
            }

        return stats


# Global router instance
router = RequestRouter()
