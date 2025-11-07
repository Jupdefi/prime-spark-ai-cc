"""
Predictive Scaling Engine

Uses time-series forecasting to predict resource needs and automatically
scale infrastructure before demand spikes.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    network_mbps: float
    request_rate: float
    avg_latency_ms: float


@dataclass
class ScalingRecommendation:
    """Scaling recommendation"""
    action: str  # scale_up, scale_down, no_action
    target_capacity: int
    confidence: float
    reasoning: str
    predicted_load: float
    time_to_threshold: Optional[timedelta]


class PredictiveScaler:
    """
    Predictive Scaling Engine

    Features:
    - Time-series forecasting (ARIMA-like)
    - Pattern recognition (daily, weekly cycles)
    - Anomaly detection
    - Proactive scaling decisions
    - Cost-aware scaling policies
    """

    def __init__(
        self,
        scale_up_threshold: float = 0.70,
        scale_down_threshold: float = 0.30,
        cooldown_minutes: int = 5,
        history_hours: int = 168,  # 1 week
        min_capacity: int = 2,
        max_capacity: int = 100,
    ):
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.cooldown_minutes = cooldown_minutes
        self.history_hours = history_hours
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity

        self.metrics_history: deque = deque(maxlen=history_hours * 60)  # 1-minute intervals
        self.last_scale_time: Optional[datetime] = None
        self.current_capacity: int = min_capacity

        logger.info(f"Initialized PredictiveScaler (thresholds: {scale_up_threshold}/{scale_down_threshold})")

    def record_metrics(self, metrics: ResourceMetrics) -> None:
        """Record resource metrics for historical analysis"""
        self.metrics_history.append(metrics)

    def predict_load(
        self,
        horizon_minutes: int = 30,
    ) -> Tuple[float, float]:
        """
        Predict future load using time-series forecasting

        Args:
            horizon_minutes: How far ahead to predict

        Returns:
            (predicted_load, confidence)
        """
        if len(self.metrics_history) < 10:
            logger.warning("Insufficient history for prediction")
            current = self.metrics_history[-1] if self.metrics_history else None
            if current:
                return current.cpu_percent, 0.3
            return 50.0, 0.1

        # Extract recent CPU utilization
        recent_cpu = [m.cpu_percent for m in list(self.metrics_history)[-60:]]  # Last hour

        # Simple forecasting: weighted moving average + trend
        current_avg = np.mean(recent_cpu[-10:])  # Last 10 minutes
        historical_avg = np.mean(recent_cpu)

        # Calculate trend
        if len(recent_cpu) >= 2:
            trend = np.polyfit(range(len(recent_cpu)), recent_cpu, 1)[0]
        else:
            trend = 0

        # Predict future load
        predicted_load = current_avg + (trend * horizon_minutes)

        # Add seasonality adjustment (detect daily patterns)
        seasonality_factor = self._detect_seasonality()
        predicted_load *= seasonality_factor

        # Bound prediction
        predicted_load = max(0, min(100, predicted_load))

        # Calculate confidence based on variance
        variance = np.var(recent_cpu)
        confidence = max(0.3, min(0.95, 1.0 - variance / 1000))

        return predicted_load, confidence

    def _detect_seasonality(self) -> float:
        """Detect and apply seasonality patterns"""
        if len(self.metrics_history) < 1440:  # Less than 24 hours
            return 1.0

        # Get current hour
        current_hour = datetime.now().hour

        # Calculate average load for this hour historically
        hourly_loads = {}
        for metrics in self.metrics_history:
            hour = metrics.timestamp.hour
            if hour not in hourly_loads:
                hourly_loads[hour] = []
            hourly_loads[hour].append(metrics.cpu_percent)

        if current_hour in hourly_loads and len(hourly_loads[current_hour]) > 0:
            hour_avg = np.mean(hourly_loads[current_hour])
            overall_avg = np.mean([m.cpu_percent for m in self.metrics_history])

            if overall_avg > 0:
                return hour_avg / overall_avg

        return 1.0

    def recommend_scaling(
        self,
        current_load: float,
        prediction_horizon: int = 30,
    ) -> ScalingRecommendation:
        """
        Recommend scaling action based on current and predicted load

        Args:
            current_load: Current load percentage (0-100)
            prediction_horizon: Minutes ahead to consider

        Returns:
            ScalingRecommendation
        """
        # Check cooldown period
        if self.last_scale_time:
            time_since_scale = datetime.now() - self.last_scale_time
            if time_since_scale < timedelta(minutes=self.cooldown_minutes):
                return ScalingRecommendation(
                    action="no_action",
                    target_capacity=self.current_capacity,
                    confidence=1.0,
                    reasoning=f"Cooldown active ({time_since_scale.seconds}s remaining)",
                    predicted_load=current_load,
                    time_to_threshold=None,
                )

        # Predict future load
        predicted_load, confidence = self.predict_load(prediction_horizon)

        # Determine if scaling is needed
        action = "no_action"
        target_capacity = self.current_capacity
        reasoning = "Load within acceptable range"
        time_to_threshold = None

        # Scale up if predicted load exceeds threshold
        if predicted_load > self.scale_up_threshold * 100:
            # Calculate required capacity
            target_capacity = min(
                self.max_capacity,
                int(np.ceil(self.current_capacity * (predicted_load / (self.scale_up_threshold * 100))))
            )
            action = "scale_up"
            reasoning = f"Predicted load {predicted_load:.1f}% exceeds threshold {self.scale_up_threshold*100}%"

            # Estimate time to threshold
            if current_load < self.scale_up_threshold * 100:
                load_increase_rate = (predicted_load - current_load) / prediction_horizon
                if load_increase_rate > 0:
                    minutes_to_threshold = (self.scale_up_threshold * 100 - current_load) / load_increase_rate
                    time_to_threshold = timedelta(minutes=minutes_to_threshold)

        # Scale down if load is consistently low
        elif predicted_load < self.scale_down_threshold * 100 and current_load < self.scale_down_threshold * 100:
            # Calculate optimal capacity
            target_capacity = max(
                self.min_capacity,
                int(np.ceil(self.current_capacity * (predicted_load / (self.scale_down_threshold * 100))))
            )
            action = "scale_down"
            reasoning = f"Predicted load {predicted_load:.1f}% below threshold {self.scale_down_threshold*100}%"

        # Detect anomalies
        if self._detect_anomaly(predicted_load):
            reasoning += " (anomaly detected, increasing caution)"
            confidence *= 0.8

        return ScalingRecommendation(
            action=action,
            target_capacity=target_capacity,
            confidence=confidence,
            reasoning=reasoning,
            predicted_load=predicted_load,
            time_to_threshold=time_to_threshold,
        )

    def _detect_anomaly(self, predicted_load: float) -> bool:
        """Detect if predicted load is anomalous"""
        if len(self.metrics_history) < 60:
            return False

        # Get recent loads
        recent_loads = [m.cpu_percent for m in list(self.metrics_history)[-60:]]

        # Calculate mean and standard deviation
        mean = np.mean(recent_loads)
        std = np.std(recent_loads)

        # Check if prediction is beyond 2 standard deviations
        return abs(predicted_load - mean) > 2 * std

    def execute_scaling(self, target_capacity: int) -> bool:
        """
        Execute scaling action

        Args:
            target_capacity: Target number of instances

        Returns:
            True if scaling was initiated
        """
        if target_capacity == self.current_capacity:
            return False

        if target_capacity < self.min_capacity or target_capacity > self.max_capacity:
            logger.error(f"Invalid target capacity: {target_capacity}")
            return False

        logger.info(f"Scaling from {self.current_capacity} to {target_capacity} instances")

        # In production, this would trigger actual infrastructure scaling
        # via Kubernetes HPA, AWS Auto Scaling, etc.
        self.current_capacity = target_capacity
        self.last_scale_time = datetime.now()

        return True

    def get_insights(self) -> Dict:
        """Get insights from historical data"""
        if not self.metrics_history:
            return {}

        recent_metrics = list(self.metrics_history)[-60:]  # Last hour

        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        latency_values = [m.avg_latency_ms for m in recent_metrics]

        return {
            'current_capacity': self.current_capacity,
            'avg_cpu': np.mean(cpu_values),
            'max_cpu': np.max(cpu_values),
            'avg_memory': np.mean(memory_values),
            'max_memory': np.max(memory_values),
            'avg_latency': np.mean(latency_values),
            'p95_latency': np.percentile(latency_values, 95),
            'data_points': len(self.metrics_history),
            'prediction_confidence': self.predict_load()[1],
        }

    def optimize_thresholds(self) -> Dict[str, float]:
        """
        Optimize scaling thresholds based on historical data

        Returns:
            Recommended thresholds
        """
        if len(self.metrics_history) < 1440:  # Less than 24 hours
            return {
                'scale_up_threshold': self.scale_up_threshold,
                'scale_down_threshold': self.scale_down_threshold,
            }

        # Analyze load patterns
        cpu_values = [m.cpu_percent for m in self.metrics_history]

        # Calculate percentiles
        p50 = np.percentile(cpu_values, 50)
        p75 = np.percentile(cpu_values, 75)
        p95 = np.percentile(cpu_values, 95)

        # Recommend thresholds based on actual usage patterns
        recommended_scale_up = min(0.85, (p75 + p95) / 200)  # Average of P75 and P95
        recommended_scale_down = max(0.25, p50 / 200)  # Half of median

        return {
            'scale_up_threshold': recommended_scale_up,
            'scale_down_threshold': recommended_scale_down,
            'current_p50': p50,
            'current_p75': p75,
            'current_p95': p95,
        }
