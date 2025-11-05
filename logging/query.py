"""
Log query and analysis functionality.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from .storage import LogStorage
from .change_logger import ChangeType, LogLevel


class LogQuery:
    """
    Query and analyze log data.

    Features:
    - Filter by change type, file, date range
    - Search log descriptions and metadata
    - Generate audit reports
    - Analyze change patterns
    """

    def __init__(self, log_dir: str = "logs/agent_changes"):
        """
        Initialize log query interface.

        Args:
            log_dir: Directory containing log files
        """
        self.storage = LogStorage(log_dir=log_dir)

    def query(
        self,
        change_types: Optional[List[ChangeType]] = None,
        file_path: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        log_level: Optional[LogLevel] = None,
        search_text: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query logs with various filters.

        Args:
            change_types: Filter by change types
            file_path: Filter by file path (supports partial match)
            session_id: Filter by session ID
            agent_id: Filter by agent ID
            start_date: Start of date range
            end_date: End of date range
            log_level: Filter by log level
            search_text: Search in description and metadata
            limit: Maximum number of results

        Returns:
            List of matching log entries
        """
        # Get all logs or filter by date range
        if start_date:
            all_logs = self.storage.get_logs_by_date_range(start_date, end_date)
        else:
            all_logs = []
            for log_file in self.storage.get_all_logs():
                all_logs.extend(self.storage.read_log_file(log_file))

        # Apply filters
        filtered_logs = all_logs

        if change_types:
            change_type_values = [ct.value for ct in change_types]
            filtered_logs = [
                log for log in filtered_logs
                if log.get("change_type") in change_type_values
            ]

        if file_path:
            filtered_logs = [
                log for log in filtered_logs
                if "file_path" in log and file_path in log["file_path"]
            ]

        if session_id:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("session_id") == session_id
            ]

        if agent_id:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("agent_id") == agent_id
            ]

        if log_level:
            filtered_logs = [
                log for log in filtered_logs
                if log.get("level") == log_level.value
            ]

        if search_text:
            search_lower = search_text.lower()
            filtered_logs = [
                log for log in filtered_logs
                if self._search_in_log(log, search_lower)
            ]

        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Apply limit
        if limit:
            filtered_logs = filtered_logs[:limit]

        return filtered_logs

    def _search_in_log(self, log: Dict[str, Any], search_text: str) -> bool:
        """Check if search text appears in log entry"""
        # Search in description
        if search_text in log.get("description", "").lower():
            return True

        # Search in metadata
        metadata = log.get("metadata", {})
        if isinstance(metadata, dict):
            metadata_str = json.dumps(metadata).lower()
            if search_text in metadata_str:
                return True

        return False

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get complete change history for a specific file.

        Args:
            file_path: Path to file

        Returns:
            List of changes to the file, ordered by timestamp
        """
        return self.query(
            change_types=[
                ChangeType.FILE_CREATE,
                ChangeType.FILE_UPDATE,
                ChangeType.FILE_DELETE
            ],
            file_path=file_path
        )

    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all logs for a specific session.

        Args:
            session_id: Session ID

        Returns:
            List of log entries for the session
        """
        return self.query(session_id=session_id)

    def get_recent_changes(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent changes within the last N hours.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of results

        Returns:
            List of recent log entries
        """
        from datetime import timedelta
        start_date = datetime.now() - timedelta(hours=hours)

        return self.query(start_date=start_date, limit=limit)

    def generate_audit_report(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an audit report for a date range.

        Args:
            start_date: Start of audit period
            end_date: End of audit period
            output_file: Optional file to save report

        Returns:
            Audit report dictionary
        """
        logs = self.storage.get_logs_by_date_range(start_date, end_date)

        report = {
            "audit_period": {
                "start": start_date.isoformat(),
                "end": (end_date or datetime.now()).isoformat()
            },
            "total_changes": len(logs),
            "change_breakdown": {},
            "files_affected": {},
            "sessions": set(),
            "agents": set(),
            "critical_events": [],
            "errors": []
        }

        for log in logs:
            # Count change types
            change_type = log.get("change_type", "unknown")
            report["change_breakdown"][change_type] = \
                report["change_breakdown"].get(change_type, 0) + 1

            # Track files
            if "file_path" in log:
                file_path = log["file_path"]
                if file_path not in report["files_affected"]:
                    report["files_affected"][file_path] = 0
                report["files_affected"][file_path] += 1

            # Track sessions and agents
            if "session_id" in log:
                report["sessions"].add(log["session_id"])
            if "agent_id" in log:
                report["agents"].add(log["agent_id"])

            # Collect critical events
            if log.get("level") == LogLevel.CRITICAL.value:
                report["critical_events"].append({
                    "timestamp": log.get("timestamp"),
                    "description": log.get("description"),
                    "change_type": change_type
                })

            # Collect errors
            if log.get("level") == LogLevel.ERROR.value:
                report["errors"].append({
                    "timestamp": log.get("timestamp"),
                    "description": log.get("description"),
                    "change_type": change_type
                })

        # Convert sets to lists for JSON serialization
        report["sessions"] = list(report["sessions"])
        report["agents"] = list(report["agents"])

        # Sort files by change count
        report["files_affected"] = dict(
            sorted(
                report["files_affected"].items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

        return report

    def analyze_patterns(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze patterns in log data.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Pattern analysis dictionary
        """
        if start_date:
            logs = self.storage.get_logs_by_date_range(start_date, end_date)
        else:
            logs = []
            for log_file in self.storage.get_all_logs():
                logs.extend(self.storage.read_log_file(log_file))

        analysis = {
            "total_logs": len(logs),
            "time_distribution": {},
            "most_active_files": {},
            "most_common_operations": {},
            "agent_activity": {}
        }

        for log in logs:
            # Time distribution (by hour)
            try:
                timestamp = datetime.fromisoformat(log["timestamp"])
                hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                analysis["time_distribution"][hour_key] = \
                    analysis["time_distribution"].get(hour_key, 0) + 1
            except (KeyError, ValueError):
                pass

            # Track file activity
            if "file_path" in log:
                file_path = log["file_path"]
                analysis["most_active_files"][file_path] = \
                    analysis["most_active_files"].get(file_path, 0) + 1

            # Track operation types
            change_type = log.get("change_type", "unknown")
            analysis["most_common_operations"][change_type] = \
                analysis["most_common_operations"].get(change_type, 0) + 1

            # Track agent activity
            agent_id = log.get("agent_id", "unknown")
            if agent_id not in analysis["agent_activity"]:
                analysis["agent_activity"][agent_id] = {
                    "total_actions": 0,
                    "change_types": {}
                }

            analysis["agent_activity"][agent_id]["total_actions"] += 1
            analysis["agent_activity"][agent_id]["change_types"][change_type] = \
                analysis["agent_activity"][agent_id]["change_types"].get(change_type, 0) + 1

        # Sort results
        analysis["most_active_files"] = dict(
            sorted(
                analysis["most_active_files"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]  # Top 20
        )

        analysis["most_common_operations"] = dict(
            sorted(
                analysis["most_common_operations"].items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        return analysis

    def find_related_changes(self, log_id: str, context_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Find changes related to a specific log entry (within time context).

        Args:
            log_id: Log entry ID
            context_minutes: Time window in minutes

        Returns:
            List of related log entries
        """
        from datetime import timedelta

        # First, find the target log
        target_log = None
        for log_file in self.storage.get_all_logs():
            logs = self.storage.read_log_file(log_file)
            for log in logs:
                if log.get("id") == log_id:
                    target_log = log
                    break
            if target_log:
                break

        if not target_log:
            return []

        # Get timestamp and define window
        try:
            target_time = datetime.fromisoformat(target_log["timestamp"])
        except (KeyError, ValueError):
            return []

        start_time = target_time - timedelta(minutes=context_minutes)
        end_time = target_time + timedelta(minutes=context_minutes)

        # Find logs in the time window
        related = self.storage.get_logs_by_date_range(start_time, end_time)

        # Filter to same session if available
        if "session_id" in target_log:
            related = [
                log for log in related
                if log.get("session_id") == target_log["session_id"]
            ]

        return related
