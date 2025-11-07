"""
Metrics export for integration with monitoring systems.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .query import LogQuery
from .storage import LogStorage
from .change_logger import ChangeType


class LogMetrics:
    """
    Export log metrics for monitoring systems (Prometheus, Grafana, etc.)

    Features:
    - Change rate metrics
    - Error rate tracking
    - File modification frequency
    - Agent activity metrics
    """

    def __init__(self, log_dir: str = "logs/agent_changes"):
        """
        Initialize metrics exporter.

        Args:
            log_dir: Directory containing log files
        """
        self.query = LogQuery(log_dir)
        self.storage = LogStorage(log_dir)

    def get_metrics(self, window_hours: int = 24) -> Dict[str, Any]:
        """
        Get all metrics for the specified time window.

        Args:
            window_hours: Time window in hours

        Returns:
            Dictionary of metrics
        """
        start_date = datetime.now() - timedelta(hours=window_hours)
        logs = self.storage.get_logs_by_date_range(start_date)

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "window_hours": window_hours,
            "total_changes": len(logs),
            "changes_per_hour": len(logs) / window_hours if window_hours > 0 else 0,
            "change_types": self._count_change_types(logs),
            "error_count": self._count_errors(logs),
            "error_rate": self._calculate_error_rate(logs),
            "file_changes": self._count_file_changes(logs),
            "api_calls": self._count_api_calls(logs),
            "deployments": self._count_deployments(logs),
            "agent_activity": self._count_agent_activity(logs),
            "storage_metrics": self.storage.get_storage_usage()
        }

        return metrics

    def _count_change_types(self, logs: list) -> Dict[str, int]:
        """Count occurrences of each change type"""
        counts = {}
        for log in logs:
            change_type = log.get("change_type", "unknown")
            counts[change_type] = counts.get(change_type, 0) + 1
        return counts

    def _count_errors(self, logs: list) -> int:
        """Count error and critical level logs"""
        return sum(
            1 for log in logs
            if log.get("level") in ["error", "critical"]
        )

    def _calculate_error_rate(self, logs: list) -> float:
        """Calculate error rate as percentage"""
        if not logs:
            return 0.0
        error_count = self._count_errors(logs)
        return (error_count / len(logs)) * 100

    def _count_file_changes(self, logs: list) -> int:
        """Count file modification events"""
        return sum(
            1 for log in logs
            if log.get("change_type") in [
                ChangeType.FILE_CREATE.value,
                ChangeType.FILE_UPDATE.value,
                ChangeType.FILE_DELETE.value
            ]
        )

    def _count_api_calls(self, logs: list) -> int:
        """Count API call events"""
        return sum(
            1 for log in logs
            if log.get("change_type") == ChangeType.API_CALL.value
        )

    def _count_deployments(self, logs: list) -> int:
        """Count deployment events"""
        return sum(
            1 for log in logs
            if log.get("change_type") == ChangeType.DEPLOYMENT.value
        )

    def _count_agent_activity(self, logs: list) -> Dict[str, int]:
        """Count activity per agent"""
        activity = {}
        for log in logs:
            agent_id = log.get("agent_id", "unknown")
            activity[agent_id] = activity.get(agent_id, 0) + 1
        return activity

    def export_prometheus_metrics(self, output_file: Optional[str] = None) -> str:
        """
        Export metrics in Prometheus format.

        Args:
            output_file: Optional file to write metrics to

        Returns:
            Metrics in Prometheus text format
        """
        metrics = self.get_metrics()

        lines = [
            "# HELP agent_changes_total Total number of agent changes",
            "# TYPE agent_changes_total counter",
            f"agent_changes_total {metrics['total_changes']}",
            "",
            "# HELP agent_changes_per_hour Rate of changes per hour",
            "# TYPE agent_changes_per_hour gauge",
            f"agent_changes_per_hour {metrics['changes_per_hour']:.2f}",
            "",
            "# HELP agent_errors_total Total number of errors",
            "# TYPE agent_errors_total counter",
            f"agent_errors_total {metrics['error_count']}",
            "",
            "# HELP agent_error_rate Error rate percentage",
            "# TYPE agent_error_rate gauge",
            f"agent_error_rate {metrics['error_rate']:.2f}",
            "",
            "# HELP agent_file_changes_total Total file changes",
            "# TYPE agent_file_changes_total counter",
            f"agent_file_changes_total {metrics['file_changes']}",
            "",
            "# HELP agent_api_calls_total Total API calls",
            "# TYPE agent_api_calls_total counter",
            f"agent_api_calls_total {metrics['api_calls']}",
            "",
            "# HELP agent_deployments_total Total deployments",
            "# TYPE agent_deployments_total counter",
            f"agent_deployments_total {metrics['deployments']}",
            "",
            "# HELP agent_log_storage_bytes Log storage size in bytes",
            "# TYPE agent_log_storage_bytes gauge",
            f"agent_log_storage_bytes {metrics['storage_metrics']['total_size_bytes']}",
            "",
            "# HELP agent_log_files_total Total log files",
            "# TYPE agent_log_files_total gauge",
            f"agent_log_files_total {metrics['storage_metrics']['total_files']}",
            ""
        ]

        # Add per-agent activity metrics
        lines.extend([
            "# HELP agent_activity_by_id Activity count by agent ID",
            "# TYPE agent_activity_by_id counter"
        ])
        for agent_id, count in metrics['agent_activity'].items():
            lines.append(f'agent_activity_by_id{{agent_id="{agent_id}"}} {count}')
        lines.append("")

        # Add per-change-type metrics
        lines.extend([
            "# HELP agent_changes_by_type Changes by type",
            "# TYPE agent_changes_by_type counter"
        ])
        for change_type, count in metrics['change_types'].items():
            lines.append(f'agent_changes_by_type{{type="{change_type}"}} {count}')
        lines.append("")

        prometheus_output = "\n".join(lines)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(prometheus_output)

        return prometheus_output

    def export_json_metrics(self, output_file: Optional[str] = None) -> str:
        """
        Export metrics in JSON format.

        Args:
            output_file: Optional file to write metrics to

        Returns:
            Metrics in JSON format
        """
        import json

        metrics = self.get_metrics()
        json_output = json.dumps(metrics, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_output)

        return json_output

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status based on log metrics.

        Returns:
            Health status dictionary
        """
        metrics = self.get_metrics(window_hours=1)

        # Determine health status based on error rate and recent activity
        error_rate = metrics['error_rate']
        recent_changes = metrics['total_changes']

        if error_rate > 10:
            status = "unhealthy"
            message = f"High error rate: {error_rate:.1f}%"
        elif error_rate > 5:
            status = "degraded"
            message = f"Elevated error rate: {error_rate:.1f}%"
        elif recent_changes == 0:
            status = "idle"
            message = "No recent activity"
        else:
            status = "healthy"
            message = "Operating normally"

        return {
            "status": status,
            "message": message,
            "error_rate": error_rate,
            "recent_changes": recent_changes,
            "timestamp": datetime.now().isoformat()
        }
