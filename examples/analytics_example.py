"""
Prime Spark AI - Analytics Pipeline Example

Demonstrates real-time and batch analytics capabilities:
- Data ingestion and transformation
- Real-time stream processing
- Batch analytics and aggregations
- Time-series analysis
- Predictive analytics
- Anomaly detection
"""

import asyncio
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum


class AggregationType(Enum):
    """Aggregation types for analytics"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


@dataclass
class DataPoint:
    """Individual data point"""
    timestamp: datetime
    metric: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnalyticsResult:
    """Analytics computation result"""
    metric: str
    aggregation: AggregationType
    value: float
    time_range: tuple
    sample_count: int


class StreamAnalyzer:
    """
    Real-time Stream Analytics Engine

    Features:
    - Sliding window aggregations
    - Real-time metric computation
    - Anomaly detection
    - Time-series forecasting
    """

    def __init__(self, window_size_seconds: int = 60):
        self.window_size = window_size_seconds
        self.data_windows: Dict[str, deque] = defaultdict(lambda: deque())
        self.processed_count = 0

        print("✓ Stream Analyzer initialized")
        print(f"  Window size: {window_size_seconds}s")

    async def ingest(self, data_point: DataPoint):
        """Ingest data point into stream"""
        metric_key = data_point.metric
        self.data_windows[metric_key].append(data_point)

        # Clean old data points outside window
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size)
        while self.data_windows[metric_key] and \
              self.data_windows[metric_key][0].timestamp < cutoff_time:
            self.data_windows[metric_key].popleft()

        self.processed_count += 1

    async def aggregate(
        self,
        metric: str,
        aggregation: AggregationType
    ) -> Optional[AnalyticsResult]:
        """Compute aggregation over window"""
        if metric not in self.data_windows:
            return None

        window = self.data_windows[metric]
        if not window:
            return None

        values = [dp.value for dp in window]
        time_range = (window[0].timestamp, window[-1].timestamp)

        # Compute aggregation
        if aggregation == AggregationType.SUM:
            result_value = sum(values)
        elif aggregation == AggregationType.AVG:
            result_value = statistics.mean(values)
        elif aggregation == AggregationType.MIN:
            result_value = min(values)
        elif aggregation == AggregationType.MAX:
            result_value = max(values)
        elif aggregation == AggregationType.COUNT:
            result_value = len(values)
        elif aggregation == AggregationType.PERCENTILE:
            result_value = statistics.median(values)  # P50
        else:
            result_value = 0

        return AnalyticsResult(
            metric=metric,
            aggregation=aggregation,
            value=result_value,
            time_range=time_range,
            sample_count=len(values)
        )

    async def detect_anomaly(self, metric: str, threshold_std: float = 2.0) -> bool:
        """Detect anomaly using standard deviation"""
        if metric not in self.data_windows:
            return False

        window = self.data_windows[metric]
        if len(window) < 3:
            return False

        values = [dp.value for dp in window]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)

        # Check if latest value is anomalous
        latest = values[-1]
        z_score = abs((latest - mean_val) / std_val) if std_val > 0 else 0

        return z_score > threshold_std


class BatchAnalytics:
    """
    Batch Analytics Engine

    Features:
    - Large-scale data aggregations
    - Multi-dimensional analysis
    - Time-series grouping
    - Statistical computations
    """

    def __init__(self):
        self.data_store: List[DataPoint] = []
        print("✓ Batch Analytics Engine initialized")

    def load_data(self, data_points: List[DataPoint]):
        """Load data for batch processing"""
        self.data_store.extend(data_points)
        print(f"  Loaded {len(data_points)} data points")

    def group_by_time(
        self,
        metric: str,
        interval_minutes: int = 5
    ) -> Dict[datetime, List[float]]:
        """Group data by time intervals"""
        grouped = defaultdict(list)

        for dp in self.data_store:
            if dp.metric != metric:
                continue

            # Round to interval
            rounded_time = dp.timestamp.replace(
                minute=(dp.timestamp.minute // interval_minutes) * interval_minutes,
                second=0,
                microsecond=0
            )
            grouped[rounded_time].append(dp.value)

        return grouped

    def compute_statistics(self, metric: str) -> Dict[str, float]:
        """Compute comprehensive statistics"""
        values = [dp.value for dp in self.data_store if dp.metric == metric]

        if not values:
            return {}

        return {
            'count': len(values),
            'sum': sum(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'p25': statistics.quantiles(values, n=4)[0] if len(values) >= 4 else values[0],
            'p75': statistics.quantiles(values, n=4)[2] if len(values) >= 4 else values[-1],
        }

    def analyze_trends(self, metric: str) -> Dict[str, Any]:
        """Analyze trends in time-series data"""
        values = [(dp.timestamp, dp.value) for dp in self.data_store if dp.metric == metric]
        values.sort(key=lambda x: x[0])

        if len(values) < 2:
            return {'trend': 'insufficient_data'}

        # Simple linear trend
        timestamps = [(v[0] - values[0][0]).total_seconds() for v in values]
        data_values = [v[1] for v in values]

        # Calculate slope (basic linear regression)
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(data_values)
        sum_xy = sum(x * y for x, y in zip(timestamps, data_values))
        sum_xx = sum(x * x for x in timestamps)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x) if (n * sum_xx - sum_x * sum_x) != 0 else 0

        trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'

        return {
            'trend': trend_direction,
            'slope': slope,
            'data_points': n,
            'start_value': data_values[0],
            'end_value': data_values[-1],
            'change_percent': ((data_values[-1] - data_values[0]) / data_values[0] * 100) if data_values[0] != 0 else 0
        }


async def demo_stream_analytics():
    """Demo 1: Real-time stream analytics"""
    print("\n" + "=" * 80)
    print("DEMO 1: Real-Time Stream Analytics")
    print("=" * 80)

    analyzer = StreamAnalyzer(window_size_seconds=10)

    print("\n1. Simulating real-time data stream (CPU usage):")
    base_cpu = 45.0

    for i in range(20):
        # Simulate CPU usage with some variance
        cpu_value = base_cpu + random.gauss(0, 5)

        data_point = DataPoint(
            timestamp=datetime.now(),
            metric="cpu_usage",
            value=cpu_value,
            tags={"host": "edge-device-1"}
        )

        await analyzer.ingest(data_point)
        await asyncio.sleep(0.1)

        if i % 5 == 0:
            # Compute aggregations
            avg_result = await analyzer.aggregate("cpu_usage", AggregationType.AVG)
            max_result = await analyzer.aggregate("cpu_usage", AggregationType.MAX)

            print(f"   t={i}: CPU avg={avg_result.value:.1f}%, max={max_result.value:.1f}%")

    print(f"\n2. Total data points processed: {analyzer.processed_count}")


async def demo_anomaly_detection():
    """Demo 2: Real-time anomaly detection"""
    print("\n" + "=" * 80)
    print("DEMO 2: Anomaly Detection")
    print("=" * 80)

    analyzer = StreamAnalyzer(window_size_seconds=30)

    print("\n1. Ingesting normal data with occasional spikes:")

    for i in range(30):
        # Normal data: mean=100, std=10
        if i == 15:
            # Inject anomaly
            value = 200.0
        else:
            value = random.gauss(100, 10)

        data_point = DataPoint(
            timestamp=datetime.now(),
            metric="response_time_ms",
            value=value,
            tags={"endpoint": "/api/predict"}
        )

        await analyzer.ingest(data_point)

        # Check for anomaly
        is_anomaly = await analyzer.detect_anomaly("response_time_ms", threshold_std=2.0)

        if is_anomaly:
            print(f"   ⚠️  ANOMALY DETECTED at t={i}: value={value:.1f}ms")
        elif i % 10 == 0:
            print(f"   t={i}: value={value:.1f}ms (normal)")

        await asyncio.sleep(0.05)

    print("\n2. Anomaly detection complete")


async def demo_batch_analytics():
    """Demo 3: Batch analytics and aggregations"""
    print("\n" + "=" * 80)
    print("DEMO 3: Batch Analytics")
    print("=" * 80)

    analytics = BatchAnalytics()

    print("\n1. Generating historical data (last 24 hours):")

    # Generate 24 hours of data at 5-minute intervals
    data_points = []
    start_time = datetime.now() - timedelta(hours=24)

    for i in range(288):  # 24 * 12 (5-minute intervals)
        timestamp = start_time + timedelta(minutes=i * 5)

        # Simulate daily pattern (higher during day, lower at night)
        hour = timestamp.hour
        base_requests = 100 + 50 * (1 if 8 <= hour <= 20 else 0)
        requests = base_requests + random.gauss(0, 20)

        data_points.append(DataPoint(
            timestamp=timestamp,
            metric="api_requests",
            value=max(0, requests),
            tags={"service": "inference"}
        ))

    analytics.load_data(data_points)

    print("\n2. Computing statistics:")
    stats = analytics.compute_statistics("api_requests")
    print(f"   Total requests: {stats['count']}")
    print(f"   Mean: {stats['mean']:.1f}")
    print(f"   Median: {stats['median']:.1f}")
    print(f"   Std Dev: {stats['std']:.1f}")
    print(f"   Min: {stats['min']:.1f}")
    print(f"   Max: {stats['max']:.1f}")
    print(f"   P25: {stats['p25']:.1f}")
    print(f"   P75: {stats['p75']:.1f}")

    print("\n3. Grouping by hour:")
    hourly_data = analytics.group_by_time("api_requests", interval_minutes=60)

    # Show first 6 hours
    sorted_hours = sorted(hourly_data.keys())[:6]
    for hour in sorted_hours:
        values = hourly_data[hour]
        avg_value = statistics.mean(values)
        print(f"   {hour.strftime('%Y-%m-%d %H:%M')}: {avg_value:.1f} avg requests")


async def demo_trend_analysis():
    """Demo 4: Trend analysis"""
    print("\n" + "=" * 80)
    print("DEMO 4: Trend Analysis")
    print("=" * 80)

    analytics = BatchAnalytics()

    print("\n1. Analyzing model accuracy trend:")

    # Simulate improving model accuracy over 30 days
    data_points = []
    start_time = datetime.now() - timedelta(days=30)

    for day in range(30):
        timestamp = start_time + timedelta(days=day)
        # Simulate improving accuracy: 0.85 -> 0.92
        accuracy = 0.85 + (day / 30) * 0.07 + random.gauss(0, 0.01)
        accuracy = max(0.8, min(0.95, accuracy))

        data_points.append(DataPoint(
            timestamp=timestamp,
            metric="model_accuracy",
            value=accuracy,
            tags={"model": "classifier_v1"}
        ))

    analytics.load_data(data_points)

    trend_analysis = analytics.analyze_trends("model_accuracy")

    print(f"   Trend: {trend_analysis['trend']}")
    print(f"   Start accuracy: {trend_analysis['start_value']:.3f}")
    print(f"   End accuracy: {trend_analysis['end_value']:.3f}")
    print(f"   Change: {trend_analysis['change_percent']:.2f}%")
    print(f"   Data points: {trend_analysis['data_points']}")

    print("\n2. Analyzing inference latency trend:")
    data_points = []

    for day in range(30):
        timestamp = start_time + timedelta(days=day)
        # Simulate decreasing latency: 250ms -> 120ms
        latency = 250 - (day / 30) * 130 + random.gauss(0, 10)
        latency = max(100, latency)

        data_points.append(DataPoint(
            timestamp=timestamp,
            metric="inference_latency",
            value=latency,
            tags={"model": "classifier_v1"}
        ))

    analytics.data_store = data_points  # Replace data
    trend_analysis = analytics.analyze_trends("inference_latency")

    print(f"   Trend: {trend_analysis['trend']}")
    print(f"   Start latency: {trend_analysis['start_value']:.1f}ms")
    print(f"   End latency: {trend_analysis['end_value']:.1f}ms")
    print(f"   Change: {trend_analysis['change_percent']:.2f}%")


async def demo_multi_metric_dashboard():
    """Demo 5: Multi-metric dashboard simulation"""
    print("\n" + "=" * 80)
    print("DEMO 5: Multi-Metric Dashboard")
    print("=" * 80)

    stream = StreamAnalyzer(window_size_seconds=30)

    print("\n1. Monitoring multiple system metrics:")

    metrics_config = {
        "cpu_usage": {"base": 45, "variance": 10},
        "memory_usage": {"base": 60, "variance": 5},
        "disk_io": {"base": 100, "variance": 30},
        "network_throughput": {"base": 500, "variance": 100},
    }

    # Simulate 15 seconds of multi-metric data
    for i in range(15):
        for metric_name, config in metrics_config.items():
            value = config["base"] + random.gauss(0, config["variance"])
            value = max(0, value)

            await stream.ingest(DataPoint(
                timestamp=datetime.now(),
                metric=metric_name,
                value=value
            ))

        await asyncio.sleep(0.2)

    print("\n2. Current dashboard view:")
    print(f"   {'Metric':<25} {'Avg':<10} {'Min':<10} {'Max':<10}")
    print(f"   {'-' * 55}")

    for metric_name in metrics_config.keys():
        avg_result = await stream.aggregate(metric_name, AggregationType.AVG)
        min_result = await stream.aggregate(metric_name, AggregationType.MIN)
        max_result = await stream.aggregate(metric_name, AggregationType.MAX)

        print(f"   {metric_name:<25} {avg_result.value:<10.1f} {min_result.value:<10.1f} {max_result.value:<10.1f}")

    print(f"\n3. Total data points processed: {stream.processed_count}")


async def main():
    """Run all analytics demos"""
    print("=" * 80)
    print("PRIME SPARK AI - ANALYTICS PIPELINE DEMO")
    print("=" * 80)
    print("\nDemonstrates analytics capabilities:")
    print("  1. Real-Time Stream Analytics")
    print("  2. Anomaly Detection")
    print("  3. Batch Analytics")
    print("  4. Trend Analysis")
    print("  5. Multi-Metric Dashboard")

    input("\nPress Enter to start demos...")

    await demo_stream_analytics()
    input("\nPress Enter to continue...")

    await demo_anomaly_detection()
    input("\nPress Enter to continue...")

    await demo_batch_analytics()
    input("\nPress Enter to continue...")

    await demo_trend_analysis()
    input("\nPress Enter to continue...")

    await demo_multi_metric_dashboard()

    print("\n" + "=" * 80)
    print("ANALYTICS DEMOS COMPLETE")
    print("=" * 80)
    print("\nKey Capabilities:")
    print("  • Real-time stream processing with sliding windows")
    print("  • Anomaly detection using statistical methods")
    print("  • Batch aggregations and time-series grouping")
    print("  • Trend analysis and forecasting")
    print("  • Multi-metric monitoring dashboards")


if __name__ == "__main__":
    asyncio.run(main())
