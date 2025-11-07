"""
Geographic Optimization Engine

Optimizes routing and resource placement based on geographic location,
latency, and proximity to reduce response times and improve user experience.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class Continent(Enum):
    """Continent classification"""
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    EUROPE = "europe"
    ASIA = "asia"
    AFRICA = "africa"
    OCEANIA = "oceania"
    ANTARCTICA = "antarctica"


@dataclass
class GeoLocation:
    """Geographic location"""
    latitude: float
    longitude: float
    city: str
    region: str
    country: str
    continent: Continent
    timezone: str


@dataclass
class GeoEndpoint:
    """Geographic endpoint information"""
    id: str
    location: GeoLocation
    capacity: int
    current_load: int
    avg_latency_ms: float
    bandwidth_mbps: float
    health_score: float

    @property
    def utilization(self) -> float:
        """Calculate current utilization percentage"""
        return (self.current_load / self.capacity) * 100 if self.capacity > 0 else 0


@dataclass
class GeoRoutingDecision:
    """Geographic routing decision"""
    endpoint: GeoEndpoint
    distance_km: float
    estimated_latency_ms: float
    confidence: float
    reasoning: str
    backup_endpoints: List[GeoEndpoint]


@dataclass
class RegionLoadMetrics:
    """Load metrics per geographic region"""
    region: str
    total_requests: int
    avg_latency_ms: float
    error_rate: float
    bandwidth_mbps: float
    endpoint_count: int
    avg_utilization: float


class GeoOptimizer:
    """
    Geographic Optimization Engine

    Features:
    - Geolocation-based routing
    - Distance calculation and latency prediction
    - Multi-region load distribution
    - Geographic redundancy
    - Proximity-based endpoint selection
    - Continental traffic shaping
    """

    # Speed of light in fiber (roughly 2/3 speed in vacuum)
    LIGHT_SPEED_KM_MS = 200  # km per millisecond

    # Base latency overhead (processing, queuing, etc.)
    BASE_LATENCY_MS = 10

    def __init__(
        self,
        max_distance_km: float = 10000,
        prefer_same_continent: bool = True,
        min_backup_endpoints: int = 2,
    ):
        self.max_distance_km = max_distance_km
        self.prefer_same_continent = prefer_same_continent
        self.min_backup_endpoints = min_backup_endpoints

        self.endpoints: Dict[str, GeoEndpoint] = {}
        self.region_metrics: Dict[str, RegionLoadMetrics] = {}

        # Known major city coordinates (for development/testing)
        self.city_database = self._initialize_city_database()

        logger.info(f"Initialized GeoOptimizer (max_distance: {max_distance_km}km)")

    def _initialize_city_database(self) -> Dict[str, GeoLocation]:
        """Initialize database of major city locations"""
        return {
            # North America
            'new_york': GeoLocation(40.7128, -74.0060, "New York", "NY", "USA", Continent.NORTH_AMERICA, "America/New_York"),
            'san_francisco': GeoLocation(37.7749, -122.4194, "San Francisco", "CA", "USA", Continent.NORTH_AMERICA, "America/Los_Angeles"),
            'toronto': GeoLocation(43.6532, -79.3832, "Toronto", "ON", "Canada", Continent.NORTH_AMERICA, "America/Toronto"),
            'mexico_city': GeoLocation(19.4326, -99.1332, "Mexico City", "CDMX", "Mexico", Continent.NORTH_AMERICA, "America/Mexico_City"),

            # Europe
            'london': GeoLocation(51.5074, -0.1278, "London", "England", "UK", Continent.EUROPE, "Europe/London"),
            'paris': GeoLocation(48.8566, 2.3522, "Paris", "Île-de-France", "France", Continent.EUROPE, "Europe/Paris"),
            'frankfurt': GeoLocation(50.1109, 8.6821, "Frankfurt", "Hesse", "Germany", Continent.EUROPE, "Europe/Berlin"),
            'amsterdam': GeoLocation(52.3676, 4.9041, "Amsterdam", "North Holland", "Netherlands", Continent.EUROPE, "Europe/Amsterdam"),

            # Asia
            'tokyo': GeoLocation(35.6762, 139.6503, "Tokyo", "Kanto", "Japan", Continent.ASIA, "Asia/Tokyo"),
            'singapore': GeoLocation(1.3521, 103.8198, "Singapore", "Singapore", "Singapore", Continent.ASIA, "Asia/Singapore"),
            'mumbai': GeoLocation(19.0760, 72.8777, "Mumbai", "Maharashtra", "India", Continent.ASIA, "Asia/Kolkata"),
            'seoul': GeoLocation(37.5665, 126.9780, "Seoul", "Seoul", "South Korea", Continent.ASIA, "Asia/Seoul"),

            # South America
            'sao_paulo': GeoLocation(-23.5505, -46.6333, "São Paulo", "SP", "Brazil", Continent.SOUTH_AMERICA, "America/Sao_Paulo"),
            'buenos_aires': GeoLocation(-34.6037, -58.3816, "Buenos Aires", "Buenos Aires", "Argentina", Continent.SOUTH_AMERICA, "America/Argentina/Buenos_Aires"),

            # Oceania
            'sydney': GeoLocation(-33.8688, 151.2093, "Sydney", "NSW", "Australia", Continent.OCEANIA, "Australia/Sydney"),
            'auckland': GeoLocation(-36.8485, 174.7633, "Auckland", "Auckland", "New Zealand", Continent.OCEANIA, "Pacific/Auckland"),

            # Africa
            'cape_town': GeoLocation(-33.9249, 18.4241, "Cape Town", "Western Cape", "South Africa", Continent.AFRICA, "Africa/Johannesburg"),
            'lagos': GeoLocation(6.5244, 3.3792, "Lagos", "Lagos", "Nigeria", Continent.AFRICA, "Africa/Lagos"),
        }

    def register_endpoint(self, endpoint: GeoEndpoint) -> None:
        """Register a geographic endpoint"""
        self.endpoints[endpoint.id] = endpoint
        logger.info(f"Registered endpoint: {endpoint.id} in {endpoint.location.city}")

    def unregister_endpoint(self, endpoint_id: str) -> None:
        """Unregister a geographic endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered endpoint: {endpoint_id}")

    def calculate_distance(
        self,
        loc1: Tuple[float, float],
        loc2: Tuple[float, float],
    ) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula

        Args:
            loc1: (latitude, longitude) of first location
            loc2: (latitude, longitude) of second location

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = loc1
        lat2, lon2 = loc2

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        earth_radius_km = 6371

        distance = earth_radius_km * c
        return distance

    def estimate_latency(
        self,
        distance_km: float,
        endpoint: GeoEndpoint,
    ) -> float:
        """
        Estimate network latency based on distance and endpoint characteristics

        Args:
            distance_km: Distance to endpoint in km
            endpoint: Target endpoint

        Returns:
            Estimated latency in milliseconds
        """
        # Theoretical minimum (speed of light in fiber)
        light_latency = distance_km / self.LIGHT_SPEED_KM_MS

        # Add routing overhead (proportional to distance)
        routing_overhead = distance_km * 0.002  # ~0.002ms per km

        # Add endpoint processing latency
        processing_latency = endpoint.avg_latency_ms

        # Add base overhead
        total_latency = self.BASE_LATENCY_MS + light_latency + routing_overhead + processing_latency

        # Add jitter based on endpoint load
        jitter = total_latency * (endpoint.utilization / 100) * 0.1

        return total_latency + jitter

    def find_nearest_endpoints(
        self,
        client_location: Tuple[float, float],
        count: int = 3,
        same_continent_only: bool = False,
    ) -> List[Tuple[GeoEndpoint, float]]:
        """
        Find nearest endpoints to a client location

        Args:
            client_location: (latitude, longitude) of client
            count: Number of endpoints to return
            same_continent_only: Only consider endpoints on same continent

        Returns:
            List of (endpoint, distance_km) tuples, sorted by distance
        """
        if not self.endpoints:
            return []

        # Determine client continent (simplified - find nearest city)
        client_continent = None
        if same_continent_only:
            min_dist = float('inf')
            for city_loc in self.city_database.values():
                dist = self.calculate_distance(
                    client_location,
                    (city_loc.latitude, city_loc.longitude)
                )
                if dist < min_dist:
                    min_dist = dist
                    client_continent = city_loc.continent

        # Calculate distances to all endpoints
        endpoint_distances = []
        for endpoint in self.endpoints.values():
            # Skip if filtering by continent
            if same_continent_only and client_continent and endpoint.location.continent != client_continent:
                continue

            distance = self.calculate_distance(
                client_location,
                (endpoint.location.latitude, endpoint.location.longitude)
            )

            # Skip endpoints beyond max distance
            if distance > self.max_distance_km:
                continue

            # Skip unhealthy endpoints
            if endpoint.health_score < 0.5:
                continue

            endpoint_distances.append((endpoint, distance))

        # Sort by distance
        endpoint_distances.sort(key=lambda x: x[1])

        return endpoint_distances[:count]

    def route_request(
        self,
        client_location: Tuple[float, float],
        client_continent: Optional[Continent] = None,
    ) -> GeoRoutingDecision:
        """
        Route a request to the optimal geographic endpoint

        Args:
            client_location: (latitude, longitude) of client
            client_continent: Optional continent hint

        Returns:
            GeoRoutingDecision with chosen endpoint and reasoning
        """
        if not self.endpoints:
            raise ValueError("No endpoints available")

        # Find nearest endpoints
        same_continent = self.prefer_same_continent and client_continent is not None
        nearest = self.find_nearest_endpoints(
            client_location,
            count=self.min_backup_endpoints + 1,
            same_continent_only=same_continent,
        )

        # If same-continent filtering yielded no results, try globally
        if not nearest and same_continent:
            nearest = self.find_nearest_endpoints(
                client_location,
                count=self.min_backup_endpoints + 1,
                same_continent_only=False,
            )

        if not nearest:
            raise ValueError("No suitable endpoints found")

        # Primary endpoint
        primary_endpoint, distance = nearest[0]

        # Backup endpoints
        backup_endpoints = [ep for ep, _ in nearest[1:]]

        # Estimate latency
        estimated_latency = self.estimate_latency(distance, primary_endpoint)

        # Calculate confidence
        confidence = self._calculate_routing_confidence(
            primary_endpoint, distance, len(backup_endpoints)
        )

        # Generate reasoning
        reasoning = self._generate_geo_reasoning(
            primary_endpoint, distance, estimated_latency
        )

        return GeoRoutingDecision(
            endpoint=primary_endpoint,
            distance_km=distance,
            estimated_latency_ms=estimated_latency,
            confidence=confidence,
            reasoning=reasoning,
            backup_endpoints=backup_endpoints,
        )

    def _calculate_routing_confidence(
        self,
        endpoint: GeoEndpoint,
        distance: float,
        backup_count: int,
    ) -> float:
        """Calculate confidence in routing decision"""
        # Base confidence
        confidence = 0.7

        # Boost for nearby endpoints
        if distance < 1000:
            confidence += 0.2
        elif distance < 5000:
            confidence += 0.1

        # Boost for healthy endpoints
        confidence += endpoint.health_score * 0.1

        # Boost for available backups
        if backup_count >= self.min_backup_endpoints:
            confidence += 0.1

        # Penalize for high utilization
        if endpoint.utilization > 80:
            confidence -= 0.2

        return min(1.0, max(0.3, confidence))

    def _generate_geo_reasoning(
        self,
        endpoint: GeoEndpoint,
        distance: float,
        latency: float,
    ) -> str:
        """Generate human-readable reasoning for geographic routing"""
        reasons = []

        if distance < 500:
            reasons.append("very close proximity")
        elif distance < 2000:
            reasons.append("regional proximity")
        elif distance < 5000:
            reasons.append("continental proximity")

        if latency < 50:
            reasons.append("excellent latency")
        elif latency < 100:
            reasons.append("good latency")

        if endpoint.health_score > 0.9:
            reasons.append("excellent health")
        elif endpoint.health_score > 0.7:
            reasons.append("good health")

        if endpoint.utilization < 50:
            reasons.append("low utilization")

        return f"Selected {endpoint.location.city} due to {', '.join(reasons)} ({distance:.0f}km, ~{latency:.0f}ms)"

    def get_region_distribution(self) -> Dict[str, Dict]:
        """Get traffic distribution by region"""
        if not self.region_metrics:
            return {}

        distribution = {}
        total_requests = sum(m.total_requests for m in self.region_metrics.values())

        for region, metrics in self.region_metrics.items():
            distribution[region] = {
                'total_requests': metrics.total_requests,
                'percent': (metrics.total_requests / total_requests * 100) if total_requests > 0 else 0,
                'avg_latency_ms': metrics.avg_latency_ms,
                'error_rate': metrics.error_rate,
                'avg_utilization': metrics.avg_utilization,
                'endpoint_count': metrics.endpoint_count,
            }

        return distribution

    def optimize_placement(
        self,
        traffic_patterns: Dict[str, int],  # region -> request count
        current_endpoints: List[str],
    ) -> Dict:
        """
        Recommend optimal endpoint placement based on traffic patterns

        Args:
            traffic_patterns: Historical traffic by region
            current_endpoints: Current endpoint regions

        Returns:
            Optimization recommendations
        """
        total_traffic = sum(traffic_patterns.values())
        recommendations = []

        for region, requests in traffic_patterns.items():
            traffic_percent = (requests / total_traffic * 100) if total_traffic > 0 else 0

            # Recommend new endpoint if region has significant traffic without coverage
            if traffic_percent > 10 and region not in current_endpoints:
                recommendations.append({
                    'action': 'add_endpoint',
                    'region': region,
                    'reason': f"Region has {traffic_percent:.1f}% of traffic but no endpoint",
                    'priority': 'high' if traffic_percent > 20 else 'medium',
                })

            # Recommend additional capacity for high-traffic regions
            if traffic_percent > 30 and region in current_endpoints:
                recommendations.append({
                    'action': 'scale_up',
                    'region': region,
                    'reason': f"Region has {traffic_percent:.1f}% of traffic",
                    'priority': 'medium',
                })

        # Recommend removal of underutilized endpoints
        for region in current_endpoints:
            traffic_percent = (traffic_patterns.get(region, 0) / total_traffic * 100) if total_traffic > 0 else 0
            if traffic_percent < 2:
                recommendations.append({
                    'action': 'remove_endpoint',
                    'region': region,
                    'reason': f"Region has only {traffic_percent:.1f}% of traffic",
                    'priority': 'low',
                })

        return {
            'recommendations': recommendations,
            'traffic_distribution': traffic_patterns,
            'coverage_score': self._calculate_coverage_score(traffic_patterns, current_endpoints),
        }

    def _calculate_coverage_score(
        self,
        traffic_patterns: Dict[str, int],
        current_endpoints: List[str],
    ) -> float:
        """Calculate geographic coverage score (0-1)"""
        if not traffic_patterns:
            return 0.0

        total_traffic = sum(traffic_patterns.values())
        covered_traffic = sum(
            requests for region, requests in traffic_patterns.items()
            if region in current_endpoints
        )

        return (covered_traffic / total_traffic) if total_traffic > 0 else 0.0
