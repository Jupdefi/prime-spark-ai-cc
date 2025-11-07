"""
Core change logging functionality for tracking agent actions.
"""

import json
import hashlib
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading


class LogLevel(Enum):
    """Log level definitions"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ChangeType(Enum):
    """Types of changes that can be logged"""
    FILE_CREATE = "file_create"
    FILE_UPDATE = "file_update"
    FILE_DELETE = "file_delete"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    API_CALL = "api_call"
    SYSTEM_COMMAND = "system_command"
    AGENT_DECISION = "agent_decision"
    CONFIG_CHANGE = "config_change"
    MODEL_INFERENCE = "model_inference"
    DATABASE_WRITE = "database_write"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    DEPLOYMENT = "deployment"


class ChangeLogger:
    """
    Main logger class for tracking all agent changes.

    Features:
    - Structured JSON logging
    - File change tracking with diffs
    - Agent action logging
    - Thread-safe operations
    - Automatic log rotation
    """

    def __init__(self, log_dir: str = "logs/agent_changes", agent_id: str = "prime-spark-agent"):
        """
        Initialize the change logger.

        Args:
            log_dir: Directory to store log files
            agent_id: Unique identifier for this agent instance
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.agent_id = agent_id
        self.session_id = self._generate_session_id()
        self._lock = threading.Lock()

        # Initialize current session log file
        self.current_log_file = self._get_log_file_path()

        # Log session start
        self._log_session_start()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(f"{self.agent_id}-{timestamp}".encode()).hexdigest()[:12]

    def _get_log_file_path(self) -> Path:
        """Get the current log file path with date-based naming"""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"changes_{date_str}_{self.session_id}.jsonl"

    def _log_session_start(self):
        """Log the start of a new session"""
        self.log(
            change_type=ChangeType.AGENT_DECISION,
            description="Agent session started",
            metadata={
                "session_id": self.session_id,
                "agent_id": self.agent_id,
                "start_time": datetime.utcnow().isoformat()
            },
            level=LogLevel.INFO
        )

    def log(
        self,
        change_type: ChangeType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO,
        file_path: Optional[str] = None,
        before_state: Optional[Any] = None,
        after_state: Optional[Any] = None
    ) -> str:
        """
        Log a change or action.

        Args:
            change_type: Type of change being logged
            description: Human-readable description
            metadata: Additional metadata about the change
            level: Log level
            file_path: Path to affected file (if applicable)
            before_state: State before the change
            after_state: State after the change

        Returns:
            Log entry ID
        """
        with self._lock:
            log_entry = {
                "id": self._generate_log_id(),
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": self.session_id,
                "agent_id": self.agent_id,
                "change_type": change_type.value,
                "description": description,
                "level": level.value,
                "metadata": metadata or {},
            }

            if file_path:
                log_entry["file_path"] = str(file_path)
                log_entry["file_hash_before"] = self._hash_state(before_state)
                log_entry["file_hash_after"] = self._hash_state(after_state)

            if before_state is not None:
                log_entry["before_state"] = self._serialize_state(before_state)

            if after_state is not None:
                log_entry["after_state"] = self._serialize_state(after_state)

            # Write to log file
            self._write_log_entry(log_entry)

            return log_entry["id"]

    def _generate_log_id(self) -> str:
        """Generate a unique log entry ID"""
        timestamp = datetime.utcnow().isoformat()
        random_component = os.urandom(4).hex()
        return hashlib.sha256(f"{timestamp}-{random_component}".encode()).hexdigest()[:16]

    def _hash_state(self, state: Any) -> Optional[str]:
        """Generate a hash of a state for change detection"""
        if state is None:
            return None

        if isinstance(state, (str, bytes)):
            content = state.encode() if isinstance(state, str) else state
            return hashlib.sha256(content).hexdigest()

        return hashlib.sha256(str(state).encode()).hexdigest()

    def _serialize_state(self, state: Any) -> Any:
        """Serialize state for storage"""
        if isinstance(state, (str, int, float, bool, type(None))):
            return state
        elif isinstance(state, (dict, list)):
            return state
        elif isinstance(state, bytes):
            return state.decode('utf-8', errors='replace')
        else:
            return str(state)

    def _write_log_entry(self, log_entry: Dict[str, Any]):
        """Write a log entry to the log file"""
        try:
            with open(self.current_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Error writing log entry: {e}")

    def log_file_change(
        self,
        file_path: str,
        change_type: ChangeType,
        before_content: Optional[str] = None,
        after_content: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Log a file change with optional content tracking.

        Args:
            file_path: Path to the file
            change_type: Type of change (create, update, delete)
            before_content: Content before change
            after_content: Content after change
            description: Optional description

        Returns:
            Log entry ID
        """
        if description is None:
            description = f"File {change_type.value}: {file_path}"

        metadata = {
            "file_size_before": len(before_content) if before_content else 0,
            "file_size_after": len(after_content) if after_content else 0,
        }

        return self.log(
            change_type=change_type,
            description=description,
            metadata=metadata,
            file_path=file_path,
            before_state=before_content,
            after_state=after_content
        )

    def log_git_operation(
        self,
        operation: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a git operation.

        Args:
            operation: Git operation type (commit, push, pull, etc.)
            description: Description of the operation
            metadata: Additional metadata (commit hash, branch, etc.)

        Returns:
            Log entry ID
        """
        change_type = ChangeType.GIT_COMMIT if operation == "commit" else ChangeType.GIT_PUSH

        return self.log(
            change_type=change_type,
            description=description,
            metadata=metadata or {}
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        status_code: Optional[int] = None
    ) -> str:
        """
        Log an API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            request_data: Request payload
            response_data: Response payload
            status_code: HTTP status code

        Returns:
            Log entry ID
        """
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        }

        return self.log(
            change_type=ChangeType.API_CALL,
            description=f"API call: {method} {endpoint}",
            metadata=metadata,
            before_state=request_data,
            after_state=response_data
        )

    def log_command(
        self,
        command: str,
        output: Optional[str] = None,
        exit_code: Optional[int] = None,
        working_dir: Optional[str] = None
    ) -> str:
        """
        Log a system command execution.

        Args:
            command: Command that was executed
            output: Command output
            exit_code: Exit code
            working_dir: Working directory

        Returns:
            Log entry ID
        """
        metadata = {
            "command": command,
            "exit_code": exit_code,
            "working_dir": working_dir or os.getcwd()
        }

        return self.log(
            change_type=ChangeType.SYSTEM_COMMAND,
            description=f"Executed command: {command}",
            metadata=metadata,
            after_state=output
        )

    def log_agent_decision(
        self,
        decision: str,
        reasoning: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an agent decision with reasoning.

        Args:
            decision: The decision made
            reasoning: Reasoning behind the decision
            context: Context information

        Returns:
            Log entry ID
        """
        metadata = {
            "decision": decision,
            "reasoning": reasoning,
            "context": context or {}
        }

        return self.log(
            change_type=ChangeType.AGENT_DECISION,
            description=f"Agent decision: {decision}",
            metadata=metadata,
            level=LogLevel.INFO
        )

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session's changes.

        Returns:
            Summary dictionary with statistics
        """
        logs = self._read_session_logs()

        summary = {
            "session_id": self.session_id,
            "total_changes": len(logs),
            "change_types": {},
            "files_modified": set(),
            "start_time": None,
            "end_time": None
        }

        for log in logs:
            # Count change types
            change_type = log.get("change_type")
            summary["change_types"][change_type] = summary["change_types"].get(change_type, 0) + 1

            # Track modified files
            if "file_path" in log:
                summary["files_modified"].add(log["file_path"])

            # Track time range
            timestamp = log.get("timestamp")
            if summary["start_time"] is None or timestamp < summary["start_time"]:
                summary["start_time"] = timestamp
            if summary["end_time"] is None or timestamp > summary["end_time"]:
                summary["end_time"] = timestamp

        summary["files_modified"] = list(summary["files_modified"])

        return summary

    def _read_session_logs(self) -> List[Dict[str, Any]]:
        """Read all logs for the current session"""
        logs = []

        if not self.current_log_file.exists():
            return logs

        with open(self.current_log_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return logs
