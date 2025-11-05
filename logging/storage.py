"""
Log storage and management functionality.
"""

import json
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional


class LogStorage:
    """
    Manages log file storage, rotation, and archival.

    Features:
    - Automatic log rotation
    - Compression of old logs
    - Storage quota management
    - Log cleanup policies
    """

    def __init__(
        self,
        log_dir: str = "logs/agent_changes",
        max_log_age_days: int = 30,
        max_storage_mb: int = 500,
        compress_after_days: int = 7
    ):
        """
        Initialize log storage manager.

        Args:
            log_dir: Directory containing log files
            max_log_age_days: Delete logs older than this many days
            max_storage_mb: Maximum storage in megabytes
            compress_after_days: Compress logs older than this many days
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_log_age = timedelta(days=max_log_age_days)
        self.max_storage_bytes = max_storage_mb * 1024 * 1024
        self.compress_age = timedelta(days=compress_after_days)

    def get_all_logs(self) -> List[Path]:
        """Get all log files (including compressed)"""
        log_files = list(self.log_dir.glob("changes_*.jsonl"))
        log_files.extend(self.log_dir.glob("changes_*.jsonl.gz"))
        return sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)

    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Calculate current storage usage.

        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        file_count = 0
        compressed_count = 0

        for log_file in self.get_all_logs():
            total_size += log_file.stat().st_size
            file_count += 1
            if log_file.suffix == '.gz':
                compressed_count += 1

        return {
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_files": file_count,
            "compressed_files": compressed_count,
            "uncompressed_files": file_count - compressed_count,
            "storage_limit_mb": self.max_storage_bytes / (1024 * 1024),
            "usage_percentage": (total_size / self.max_storage_bytes) * 100
        }

    def compress_old_logs(self) -> int:
        """
        Compress logs older than compress_age.

        Returns:
            Number of files compressed
        """
        compressed_count = 0
        cutoff_date = datetime.now() - self.compress_age

        for log_file in self.log_dir.glob("changes_*.jsonl"):
            if log_file.suffix == '.gz':
                continue

            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                self._compress_file(log_file)
                compressed_count += 1

        return compressed_count

    def _compress_file(self, file_path: Path):
        """Compress a single log file"""
        compressed_path = file_path.with_suffix('.jsonl.gz')

        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove original file after successful compression
        file_path.unlink()

    def cleanup_old_logs(self) -> int:
        """
        Remove logs older than max_log_age.

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now() - self.max_log_age

        for log_file in self.get_all_logs():
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            if file_mtime < cutoff_date:
                log_file.unlink()
                deleted_count += 1

        return deleted_count

    def enforce_storage_quota(self) -> int:
        """
        Enforce storage quota by removing oldest logs.

        Returns:
            Number of files deleted
        """
        usage = self.get_storage_usage()

        if usage["total_size_bytes"] <= self.max_storage_bytes:
            return 0

        deleted_count = 0
        log_files = self.get_all_logs()  # Already sorted by modification time

        # Remove oldest files until under quota
        for log_file in reversed(log_files):
            if usage["total_size_bytes"] <= self.max_storage_bytes:
                break

            file_size = log_file.stat().st_size
            log_file.unlink()
            usage["total_size_bytes"] -= file_size
            deleted_count += 1

        return deleted_count

    def read_log_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Read a log file (handles both compressed and uncompressed).

        Args:
            file_path: Path to log file

        Returns:
            List of log entries
        """
        logs = []

        if file_path.suffix == '.gz':
            with gzip.open(file_path, 'rt') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        else:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return logs

    def get_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range (defaults to now)

        Returns:
            List of log entries
        """
        if end_date is None:
            end_date = datetime.now()

        all_logs = []

        for log_file in self.get_all_logs():
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            # Skip files clearly outside the range
            if file_mtime < start_date - timedelta(days=1):
                continue

            logs = self.read_log_file(log_file)

            for log in logs:
                try:
                    log_time = datetime.fromisoformat(log["timestamp"])
                    if start_date <= log_time <= end_date:
                        all_logs.append(log)
                except (KeyError, ValueError):
                    continue

        return sorted(all_logs, key=lambda x: x.get("timestamp", ""))

    def export_logs(
        self,
        output_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "jsonl"
    ):
        """
        Export logs to a file.

        Args:
            output_file: Output file path
            start_date: Optional start date filter
            end_date: Optional end date filter
            format: Output format (jsonl, json, csv)
        """
        if start_date:
            logs = self.get_logs_by_date_range(start_date, end_date)
        else:
            logs = []
            for log_file in self.get_all_logs():
                logs.extend(self.read_log_file(log_file))

        output_path = Path(output_file)

        if format == "jsonl":
            with open(output_path, 'w') as f:
                for log in logs:
                    f.write(json.dumps(log) + '\n')

        elif format == "json":
            with open(output_path, 'w') as f:
                json.dump(logs, f, indent=2)

        elif format == "csv":
            import csv
            if not logs:
                return

            with open(output_path, 'w', newline='') as f:
                # Get all unique keys from logs
                fieldnames = set()
                for log in logs:
                    fieldnames.update(log.keys())

                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()

                for log in logs:
                    # Convert nested dicts/lists to JSON strings
                    row = {}
                    for key, value in log.items():
                        if isinstance(value, (dict, list)):
                            row[key] = json.dumps(value)
                        else:
                            row[key] = value
                    writer.writerow(row)

    def maintenance(self) -> Dict[str, int]:
        """
        Run all maintenance tasks.

        Returns:
            Dictionary with task results
        """
        results = {
            "compressed": self.compress_old_logs(),
            "deleted_old": self.cleanup_old_logs(),
            "deleted_quota": self.enforce_storage_quota()
        }

        return results
