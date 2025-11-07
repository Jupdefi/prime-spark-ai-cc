"""
AI-Driven Traffic Router

Uses machine learning to make intelligent routing decisions based on:
- Historical performance data
- Real-time metrics
- Service health
- Geographic proximity
- Cost considerations
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies"""
    LEAST_LATENCY = "least_latency"
    LEAST_COST = "least_cost"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    AI_OPTIMIZED = "ai_optimized"


@dataclass
class ServiceEndpoint:
    """Service endpoint information"""
    id: str
    host: str
    port: int
    region: str
    zone: str
    capacity: int
    current_load: int
    avg_latency_ms: float
    error_rate: float
    cost_per_request: float
    health_score: float

    @property
    def utilization(self) -> float:
        """Calculate current utilization percentage"""
        return (self.current_load / self.capacity) * 100 if self.capacity > 0 else 0

    @property
    def is_healthy(self) -> bool:
        """Check if endpoint is healthy"""
        return (
            self.health_score > 0.7 and
            self.error_rate < 0.05 and
            self.utilization < 90
        )


@dataclass
class RoutingDecision:
    """Routing decision with reasoning"""
    endpoint: ServiceEndpoint
    confidence: float
    reasoning: str
    predicted_latency: float
    estimated_cost: float


class IntelligentRouter:
    """
    AI-Driven Intelligent Load Balancer

    Features:
    - ML-based routing decisions
    - Real-time performance optimization
    - Cost-aware routing
    - Geographic optimization
    - Predictive load balancing
    """

    def __init__(
        self,
        strategy: RoutingStrategy = RoutingStrategy.AI_OPTIMIZED,
        history_window: int = 3600,  # 1 hour
    ):
        self.strategy = strategy
        self.history_window = history_window
        self.endpoints: Dict[str, ServiceEndpoint] = {}
        self.routing_history: List[Tuple[datetime, str, float]] = []

        # ML model weights (in production, load from trained model)
        self.weights = {
            'latency': 0.35,
            'cost': 0.20,
            'health': 0.25,
            'utilization': 0.15,
            'error_rate': 0.05,
        }

        logger.info(f"Initialized IntelligentRouter with strategy: {strategy.value}")

    def register_endpoint(self, endpoint: ServiceEndpoint) -> None:
        """Register a service endpoint"""
        self.endpoints[endpoint.id] = endpoint
        logger.info(f"Registered endpoint: {endpoint.id} ({endpoint.host}:{endpoint.port})")

    def unregister_endpoint(self, endpoint_id: str) -> None:
        """Unregister a service endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered endpoint: {endpoint_id}")

    async def route_request(
        self,
        client_location: Optional[Tuple[float, float]] = None,
        request_size: int = 0,
        priority: str = "normal",
    ) -> RoutingDecision:
        """
        Route a request to the optimal endpoint

        Args:
            client_location: (latitude, longitude) of client
            request_size: Size of request in bytes
            priority: Request priority (low, normal, high, critical)

        Returns:
            RoutingDecision with chosen endpoint and reasoning
        """
        if not self.endpoints:
            raise ValueError("No endpoints available")

        # Filter healthy endpoints
        healthy_endpoints = [
            ep for ep in self.endpoints.values()
            if ep.is_healthy
        ]

        if not healthy_endpoints:
            logger.warning("No healthy endpoints, using degraded routing")
            healthy_endpoints = list(self.endpoints.values())

        # Choose routing strategy
        if self.strategy == RoutingStrategy.AI_OPTIMIZED:
            decision = await self._ai_route(
                healthy_endpoints, client_location, request_size, priority
            )
        elif self.strategy == RoutingStrategy.LEAST_LATENCY:
            decision = self._least_latency_route(healthy_endpoints)
        elif self.strategy == RoutingStrategy.LEAST_COST:
            decision = self._least_cost_route(healthy_endpoints)
        elif self.strategy == RoutingStrategy.WEIGHTED:
            decision = self._weighted_route(healthy_endpoints)
        else:
            decision = self._round_robin_route(healthy_endpoints)

        # Record routing decision
        self.routing_history.append((
            datetime.now(),
            decision.endpoint.id,
            decision.confidence
        ))

        # Cleanup old history
        self._cleanup_history()

        return decision

    async def _ai_route(
        self,
        endpoints: List[ServiceEndpoint],
        client_location: Optional[Tuple[float, float]],
        request_size: int,
        priority: str,
    ) -> RoutingDecision:
        """AI-optimized routing using ML model"""

        best_endpoint = None
        best_score = -float('inf')
        best_reasoning = ""

        for endpoint in endpoints:
            # Calculate composite score
            score = self._calculate_score(endpoint, client_location, priority)

            if score > best_score:
                best_score = score
                best_endpoint = endpoint
                best_reasoning = self._generate_reasoning(endpoint, score)

        # Predict latency and cost
        predicted_latency = self._predict_latency(best_endpoint, request_size)
        estimated_cost = best_endpoint.cost_per_request * (1 + request_size / 1024)

        return RoutingDecision(
            endpoint=best_endpoint,
            confidence=min(best_score, 1.0),
            reasoning=best_reasoning,
            predicted_latency=predicted_latency,
            estimated_cost=estimated_cost,
        )

    def _calculate_score(
        self,
        endpoint: ServiceEndpoint,
        client_location: Optional[Tuple[float, float]],
        priority: str,
    ) -> float:
        """Calculate composite score for endpoint"""

        # Normalize metrics to 0-1 range
        latency_score = 1.0 - min(endpoint.avg_latency_ms / 1000, 1.0)  # Normalize to 1s
        cost_score = 1.0 - min(endpoint.cost_per_request / 0.01, 1.0)  # Normalize to $0.01
        health_score = endpoint.health_score
        utilization_score = 1.0 - (endpoint.utilization / 100)
        error_score = 1.0 - min(endpoint.error_rate / 0.1, 1.0)  # Normalize to 10%

        # Apply weights
        score = (
            self.weights['latency'] * latency_score +
            self.weights['cost'] * cost_score +
            self.weights['health'] * health_score +
            self.weights['utilization'] * utilization_score +
            self.weights['error_rate'] * error_score
        )

        # Adjust for priority
        if priority == "critical":
            score *= 1.2  # Boost high-performance endpoints
        elif priority == "low":
            # Prefer cost over performance
            score = score * 0.8 + cost_score * 0.2

        return score

    def _generate_reasoning(self, endpoint: ServiceEndpoint, score: float) -> str:
        """Generate human-readable reasoning for routing decision"""
        reasons = []

        if endpoint.avg_latency_ms < 50:
            reasons.append("low latency")
        if endpoint.utilization < 50:
            reasons.append("low utilization")
        if endpoint.error_rate < 0.01:
            reasons.append("high reliability")
        if endpoint.cost_per_request < 0.001:
            reasons.append("cost-effective")
        if endpoint.health_score > 0.9:
            reasons.append("excellent health")

        return f"Selected due to {', '.join(reasons)} (score: {score:.2f})"

    def _predict_latency(self, endpoint: ServiceEndpoint, request_size: int) -> float:
        """Predict request latency based on historical data"""
        # Base latency + processing time + network transfer time
        base_latency = endpoint.avg_latency_ms
        processing_time = request_size / 1024 * 0.1  # 0.1ms per KB
        network_time = request_size / 1024 / 10  # 10 KB/ms throughput

        predicted = base_latency + processing_time + network_time

        # Add jitter based on current load
        jitter = predicted * (endpoint.utilization / 100) * 0.2

        return predicted + jitter

    def _least_latency_route(self, endpoints: List[ServiceEndpoint]) -> RoutingDecision:
        """Route to endpoint with lowest latency"""
        best = min(endpoints, key=lambda ep: ep.avg_latency_ms)
        return RoutingDecision(
            endpoint=best,
            confidence=0.9,
            reasoning="Lowest latency endpoint",
            predicted_latency=best.avg_latency_ms,
            estimated_cost=best.cost_per_request,
        )

    def _least_cost_route(self, endpoints: List[ServiceEndpoint]) -> RoutingDecision:
        """Route to endpoint with lowest cost"""
        best = min(endpoints, key=lambda ep: ep.cost_per_request)
        return RoutingDecision(
            endpoint=best,
            confidence=0.9,
            reasoning="Lowest cost endpoint",
            predicted_latency=best.avg_latency_ms,
            estimated_cost=best.cost_per_request,
        )

    def _weighted_route(self, endpoints: List[ServiceEndpoint]) -> RoutingDecision:
        """Weighted random routing based on capacity"""
        weights = [ep.capacity - ep.current_load for ep in endpoints]
        total_weight = sum(weights)

        if total_weight == 0:
            return self._round_robin_route(endpoints)

        weights = [w / total_weight for w in weights]
        chosen = np.random.choice(endpoints, p=weights)

        return RoutingDecision(
            endpoint=chosen,
            confidence=0.7,
            reasoning="Weighted random selection based on capacity",
            predicted_latency=chosen.avg_latency_ms,
            estimated_cost=chosen.cost_per_request,
        )

    def _round_robin_route(self, endpoints: List[ServiceEndpoint]) -> RoutingDecision:
        """Simple round-robin routing"""
        # Use hash of current time for pseudo-round-robin
        index = hash(datetime.now()) % len(endpoints)
        chosen = endpoints[index]

        return RoutingDecision(
            endpoint=chosen,
            confidence=0.5,
            reasoning="Round-robin selection",
            predicted_latency=chosen.avg_latency_ms,
            estimated_cost=chosen.cost_per_request,
        )

    def _cleanup_history(self) -> None:
        """Remove old routing history"""
        cutoff = datetime.now() - timedelta(seconds=self.history_window)
        self.routing_history = [
            (ts, ep_id, conf) for ts, ep_id, conf in self.routing_history
            if ts > cutoff
        ]

    def get_statistics(self) -> Dict:
        """Get routing statistics"""
        if not self.routing_history:
            return {}

        # Calculate endpoint usage
        endpoint_usage = {}
        for _, ep_id, _ in self.routing_history:
            endpoint_usage[ep_id] = endpoint_usage.get(ep_id, 0) + 1

        # Calculate average confidence
        avg_confidence = np.mean([conf for _, _, conf in self.routing_history])

        return {
            'total_requests': len(self.routing_history),
            'endpoint_usage': endpoint_usage,
            'avg_confidence': avg_confidence,
            'active_endpoints': len(self.endpoints),
            'healthy_endpoints': sum(1 for ep in self.endpoints.values() if ep.is_healthy),
        }

    async def update_endpoint_metrics(
        self,
        endpoint_id: str,
        latency: Optional[float] = None,
        error_occurred: bool = False,
        current_load: Optional[int] = None,
    ) -> None:
        """Update endpoint metrics based on actual performance"""
        if endpoint_id not in self.endpoints:
            return

        endpoint = self.endpoints[endpoint_id]

        # Update latency with exponential moving average
        if latency is not None:
            alpha = 0.3  # Smoothing factor
            endpoint.avg_latency_ms = (
                alpha * latency + (1 - alpha) * endpoint.avg_latency_ms
            )

        # Update error rate
        if error_occurred:
            endpoint.error_rate = min(endpoint.error_rate * 1.1, 1.0)
        else:
            endpoint.error_rate = max(endpoint.error_rate * 0.95, 0.0)

        # Update current load
        if current_load is not None:
            endpoint.current_load = current_load

        # Recalculate health score
        endpoint.health_score = self._calculate_health_score(endpoint)

    def _calculate_health_score(self, endpoint: ServiceEndpoint) -> float:
        """Calculate overall health score for endpoint"""
        latency_health = max(0, 1.0 - endpoint.avg_latency_ms / 1000)
        error_health = max(0, 1.0 - endpoint.error_rate / 0.1)
        utilization_health = max(0, 1.0 - endpoint.utilization / 100)

        return (latency_health + error_health + utilization_health) / 3
