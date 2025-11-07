"""
Cost-Aware Resource Allocation Engine

Optimizes infrastructure costs through intelligent resource allocation,
multi-cloud comparison, and budget-aware scaling decisions.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Cloud provider types"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"


class InstanceType(Enum):
    """Instance purchase types"""
    ON_DEMAND = "on_demand"
    RESERVED = "reserved"
    SPOT = "spot"
    PREEMPTIBLE = "preemptible"


@dataclass
class PricingModel:
    """Cloud resource pricing model"""
    provider: CloudProvider
    region: str
    instance_type: str
    purchase_type: InstanceType
    hourly_rate: float
    monthly_commitment: float
    spot_discount: float
    reserved_discount: float
    network_egress_per_gb: float
    storage_per_gb_month: float


@dataclass
class CostMetrics:
    """Cost tracking metrics"""
    timestamp: datetime
    total_cost: float
    compute_cost: float
    storage_cost: float
    network_cost: float
    data_transfer_cost: float
    instance_hours: float
    storage_gb_hours: float
    egress_gb: float


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation"""
    action: str  # switch_provider, use_spot, use_reserved, scale_down, consolidate
    current_cost: float
    projected_cost: float
    savings: float
    savings_percent: float
    confidence: float
    reasoning: str
    implementation_steps: List[str]
    risk_level: str  # low, medium, high


class CostOptimizer:
    """
    Cost-Aware Resource Allocation Engine

    Features:
    - Multi-cloud cost comparison
    - Reserved vs spot instance optimization
    - Region-based cost analysis
    - Budget-aware scaling
    - Cost forecasting
    - Real-time cost tracking
    """

    def __init__(
        self,
        monthly_budget: float = 5000.0,
        alert_threshold: float = 0.80,  # Alert at 80% of budget
        cost_optimization_interval: int = 3600,  # 1 hour
    ):
        self.monthly_budget = monthly_budget
        self.alert_threshold = alert_threshold
        self.cost_optimization_interval = cost_optimization_interval

        # Pricing models (in production, fetch from cloud APIs)
        self.pricing_models: Dict[str, PricingModel] = {}
        self._initialize_pricing_models()

        # Cost tracking
        self.cost_history: List[CostMetrics] = []
        self.current_month_cost: float = 0.0
        self.projected_month_end_cost: float = 0.0

        logger.info(f"Initialized CostOptimizer (budget: ${monthly_budget}/month)")

    def _initialize_pricing_models(self) -> None:
        """Initialize pricing models for different cloud providers and regions"""

        # AWS Pricing (us-east-1)
        self.pricing_models["aws-us-east-1-c5.large"] = PricingModel(
            provider=CloudProvider.AWS,
            region="us-east-1",
            instance_type="c5.large",
            purchase_type=InstanceType.ON_DEMAND,
            hourly_rate=0.085,
            monthly_commitment=0.0,
            spot_discount=0.70,  # 70% discount
            reserved_discount=0.40,  # 40% discount
            network_egress_per_gb=0.09,
            storage_per_gb_month=0.10,
        )

        # AWS Pricing (us-west-2)
        self.pricing_models["aws-us-west-2-c5.large"] = PricingModel(
            provider=CloudProvider.AWS,
            region="us-west-2",
            instance_type="c5.large",
            purchase_type=InstanceType.ON_DEMAND,
            hourly_rate=0.085,
            monthly_commitment=0.0,
            spot_discount=0.65,
            reserved_discount=0.40,
            network_egress_per_gb=0.09,
            storage_per_gb_month=0.10,
        )

        # GCP Pricing (us-central1)
        self.pricing_models["gcp-us-central1-n2-standard-2"] = PricingModel(
            provider=CloudProvider.GCP,
            region="us-central1",
            instance_type="n2-standard-2",
            purchase_type=InstanceType.ON_DEMAND,
            hourly_rate=0.097,
            monthly_commitment=0.0,
            spot_discount=0.60,  # Preemptible discount
            reserved_discount=0.37,  # Committed use discount
            network_egress_per_gb=0.12,
            storage_per_gb_month=0.04,
        )

        # Azure Pricing (eastus)
        self.pricing_models["azure-eastus-Standard_D2s_v3"] = PricingModel(
            provider=CloudProvider.AZURE,
            region="eastus",
            instance_type="Standard_D2s_v3",
            purchase_type=InstanceType.ON_DEMAND,
            hourly_rate=0.096,
            monthly_commitment=0.0,
            spot_discount=0.80,
            reserved_discount=0.35,
            network_egress_per_gb=0.087,
            storage_per_gb_month=0.05,
        )

        # Local (Raspberry Pi)
        self.pricing_models["local-pi5"] = PricingModel(
            provider=CloudProvider.LOCAL,
            region="local",
            instance_type="pi5-8gb",
            purchase_type=InstanceType.ON_DEMAND,
            hourly_rate=0.01,  # Electricity cost estimate
            monthly_commitment=0.0,
            spot_discount=0.0,
            reserved_discount=0.0,
            network_egress_per_gb=0.0,  # No egress charges
            storage_per_gb_month=0.0,
        )

    def record_cost_metrics(self, metrics: CostMetrics) -> None:
        """Record cost metrics for analysis"""
        self.cost_history.append(metrics)
        self.current_month_cost += metrics.total_cost

        # Calculate projected month-end cost
        days_in_month = 30
        current_day = datetime.now().day
        daily_avg = self.current_month_cost / current_day if current_day > 0 else 0
        self.projected_month_end_cost = daily_avg * days_in_month

    def compare_cloud_providers(
        self,
        workload_hours: float = 730,  # ~1 month
        storage_gb: float = 100,
        egress_gb: float = 500,
    ) -> Dict[str, float]:
        """
        Compare costs across cloud providers for a given workload

        Args:
            workload_hours: Total compute hours
            storage_gb: Storage in GB
            egress_gb: Network egress in GB

        Returns:
            Dictionary mapping provider to total cost
        """
        costs = {}

        for key, pricing in self.pricing_models.items():
            # Compute cost (on-demand)
            compute_cost = workload_hours * pricing.hourly_rate

            # Storage cost
            storage_cost = storage_gb * pricing.storage_per_gb_month

            # Network egress cost
            egress_cost = egress_gb * pricing.network_egress_per_gb

            # Total cost
            total_cost = compute_cost + storage_cost + egress_cost

            costs[key] = {
                'total': total_cost,
                'compute': compute_cost,
                'storage': storage_cost,
                'egress': egress_cost,
                'provider': pricing.provider.value,
                'region': pricing.region,
            }

        return costs

    def optimize_instance_type(
        self,
        current_utilization: float,
        current_instance: str,
        workload_variability: float = 0.3,
    ) -> CostOptimizationRecommendation:
        """
        Recommend optimal instance purchase type

        Args:
            current_utilization: Current instance utilization (0-1)
            current_instance: Current instance pricing model key
            workload_variability: How variable the workload is (0-1)

        Returns:
            CostOptimizationRecommendation
        """
        if current_instance not in self.pricing_models:
            raise ValueError(f"Unknown instance: {current_instance}")

        pricing = self.pricing_models[current_instance]
        current_cost = pricing.hourly_rate * 730  # Monthly cost

        # Decision logic
        recommendations = []

        # Spot instances (if workload is fault-tolerant)
        if workload_variability > 0.5:
            spot_cost = current_cost * (1 - pricing.spot_discount)
            savings = current_cost - spot_cost
            recommendations.append({
                'action': 'use_spot',
                'cost': spot_cost,
                'savings': savings,
                'confidence': 0.7,
                'risk': 'medium',
                'reasoning': f"Workload variability {workload_variability:.0%} makes spot instances viable",
            })

        # Reserved instances (if workload is stable)
        if workload_variability < 0.2 and current_utilization > 0.7:
            reserved_cost = current_cost * (1 - pricing.reserved_discount)
            savings = current_cost - reserved_cost
            recommendations.append({
                'action': 'use_reserved',
                'cost': reserved_cost,
                'savings': savings,
                'confidence': 0.9,
                'risk': 'low',
                'reasoning': f"Stable workload (variability {workload_variability:.0%}) benefits from reserved instances",
            })

        # Scale down (if utilization is low)
        if current_utilization < 0.3:
            scaled_cost = current_cost * 0.5  # Assume half the instances
            savings = current_cost - scaled_cost
            recommendations.append({
                'action': 'scale_down',
                'cost': scaled_cost,
                'savings': savings,
                'confidence': 0.8,
                'risk': 'low',
                'reasoning': f"Low utilization ({current_utilization:.0%}) indicates over-provisioning",
            })

        # Choose best recommendation
        if not recommendations:
            return CostOptimizationRecommendation(
                action="no_action",
                current_cost=current_cost,
                projected_cost=current_cost,
                savings=0.0,
                savings_percent=0.0,
                confidence=1.0,
                reasoning="Current configuration is optimal",
                implementation_steps=[],
                risk_level="low",
            )

        best = max(recommendations, key=lambda r: r['savings'])

        return CostOptimizationRecommendation(
            action=best['action'],
            current_cost=current_cost,
            projected_cost=best['cost'],
            savings=best['savings'],
            savings_percent=(best['savings'] / current_cost) * 100,
            confidence=best['confidence'],
            reasoning=best['reasoning'],
            implementation_steps=self._generate_implementation_steps(best['action']),
            risk_level=best['risk'],
        )

    def _generate_implementation_steps(self, action: str) -> List[str]:
        """Generate implementation steps for a given action"""
        steps = {
            'use_spot': [
                "1. Identify fault-tolerant workloads",
                "2. Configure auto-scaling group with spot instances",
                "3. Set spot price limit (recommend: 50% of on-demand)",
                "4. Implement graceful shutdown handling",
                "5. Monitor spot instance interruptions",
            ],
            'use_reserved': [
                "1. Analyze 3-month usage patterns",
                "2. Purchase 1-year or 3-year reserved instances",
                "3. Configure capacity reservation",
                "4. Set up billing alerts",
                "5. Review quarterly for optimization",
            ],
            'scale_down': [
                "1. Analyze peak vs average load",
                "2. Reduce minimum instance count",
                "3. Tighten auto-scaling policies",
                "4. Monitor performance metrics",
                "5. Gradually reduce capacity",
            ],
            'switch_provider': [
                "1. Benchmark workload on target provider",
                "2. Calculate total migration cost",
                "3. Plan phased migration",
                "4. Set up dual-cloud deployment",
                "5. Migrate traffic gradually",
            ],
        }
        return steps.get(action, ["No specific steps available"])

    def forecast_monthly_cost(
        self,
        horizon_days: int = 30,
    ) -> Tuple[float, float]:
        """
        Forecast monthly cost based on historical data

        Args:
            horizon_days: Days ahead to forecast

        Returns:
            (forecasted_cost, confidence)
        """
        if len(self.cost_history) < 7:
            # Insufficient data, use simple projection
            return self.projected_month_end_cost, 0.3

        # Extract daily costs
        daily_costs = {}
        for metrics in self.cost_history:
            date = metrics.timestamp.date()
            daily_costs[date] = daily_costs.get(date, 0.0) + metrics.total_cost

        # Calculate trend
        dates = sorted(daily_costs.keys())
        costs = [daily_costs[d] for d in dates]

        if len(costs) >= 2:
            # Linear regression
            x = np.arange(len(costs))
            coeffs = np.polyfit(x, costs, 1)
            trend = coeffs[0]

            # Project forward
            future_days = horizon_days - len(costs)
            projected_daily = costs[-1] + (trend * future_days)

            # Total forecast
            forecast = sum(costs) + (projected_daily * future_days)
        else:
            # Not enough data for trend
            avg_daily = np.mean(costs)
            forecast = avg_daily * horizon_days

        # Calculate confidence based on variance
        variance = np.var(costs)
        confidence = max(0.3, min(0.9, 1.0 - (variance / np.mean(costs))))

        return forecast, confidence

    def check_budget_status(self) -> Dict:
        """Check current budget utilization and alerts"""
        budget_used = (self.current_month_cost / self.monthly_budget) * 100
        budget_remaining = self.monthly_budget - self.current_month_cost

        # Calculate projected overrun
        projected_overrun = max(0, self.projected_month_end_cost - self.monthly_budget)

        # Generate alerts
        alerts = []
        if budget_used > self.alert_threshold * 100:
            alerts.append(f"WARNING: {budget_used:.1f}% of budget used")

        if projected_overrun > 0:
            alerts.append(f"ALERT: Projected to exceed budget by ${projected_overrun:.2f}")

        return {
            'monthly_budget': self.monthly_budget,
            'current_spend': self.current_month_cost,
            'budget_used_percent': budget_used,
            'budget_remaining': budget_remaining,
            'projected_month_end': self.projected_month_end_cost,
            'projected_overrun': projected_overrun,
            'alerts': alerts,
            'on_track': projected_overrun == 0,
        }

    def get_cost_breakdown(self, days: int = 7) -> Dict:
        """Get detailed cost breakdown for recent period"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_metrics = [m for m in self.cost_history if m.timestamp > cutoff]

        if not recent_metrics:
            return {}

        total_cost = sum(m.total_cost for m in recent_metrics)
        compute_cost = sum(m.compute_cost for m in recent_metrics)
        storage_cost = sum(m.storage_cost for m in recent_metrics)
        network_cost = sum(m.network_cost for m in recent_metrics)
        data_transfer_cost = sum(m.data_transfer_cost for m in recent_metrics)

        return {
            'period_days': days,
            'total_cost': total_cost,
            'breakdown': {
                'compute': {
                    'cost': compute_cost,
                    'percent': (compute_cost / total_cost * 100) if total_cost > 0 else 0,
                },
                'storage': {
                    'cost': storage_cost,
                    'percent': (storage_cost / total_cost * 100) if total_cost > 0 else 0,
                },
                'network': {
                    'cost': network_cost,
                    'percent': (network_cost / total_cost * 100) if total_cost > 0 else 0,
                },
                'data_transfer': {
                    'cost': data_transfer_cost,
                    'percent': (data_transfer_cost / total_cost * 100) if total_cost > 0 else 0,
                },
            },
            'daily_average': total_cost / days,
            'instance_hours': sum(m.instance_hours for m in recent_metrics),
            'storage_gb_hours': sum(m.storage_gb_hours for m in recent_metrics),
            'egress_gb': sum(m.egress_gb for m in recent_metrics),
        }
