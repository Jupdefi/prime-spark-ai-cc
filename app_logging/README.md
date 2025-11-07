# Agent Change Logging System

Comprehensive logging system for tracking all changes and actions performed by AI agents in the Prime Spark AI platform.

## Features

- **📝 Structured Logging**: JSON-based logs with full metadata
- **🔍 Powerful Queries**: Search and filter logs by type, date, file, session
- **📊 Analytics**: Pattern analysis and audit reports
- **💾 Smart Storage**: Automatic compression and rotation
- **📈 Monitoring Integration**: Prometheus metrics export
- **🔒 Audit Trail**: Complete history of all agent actions

## Architecture

### Components

1. **ChangeLogger** - Core logging functionality
2. **LogStorage** - Storage management and maintenance
3. **LogQuery** - Query and analysis interface
4. **LogMetrics** - Metrics export for monitoring
5. **CLI** - Command-line interface for log management

### Log Entry Structure

```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "timestamp": "2025-11-05T17:30:45.123456",
  "session_id": "abc123def456",
  "agent_id": "prime-spark-agent",
  "change_type": "file_update",
  "description": "Updated configuration file",
  "level": "info",
  "file_path": "/path/to/file.py",
  "file_hash_before": "sha256:...",
  "file_hash_after": "sha256:...",
  "before_state": "...",
  "after_state": "...",
  "metadata": {
    "file_size_before": 1234,
    "file_size_after": 1456
  }
}
```

## Installation

The logging system is already integrated into Prime Spark AI. No additional installation required.

## Quick Start

### Basic Usage

```python
from logging import ChangeLogger, ChangeType

# Initialize logger
logger = ChangeLogger(
    log_dir="logs/agent_changes",
    agent_id="my-agent"
)

# Log a file change
logger.log_file_change(
    file_path="/path/to/file.py",
    change_type=ChangeType.FILE_UPDATE,
    before_content="old content",
    after_content="new content",
    description="Updated file with new features"
)

# Log an agent decision
logger.log_agent_decision(
    decision="Deploy to production",
    reasoning="All tests passed and approval received",
    context={"tests_passed": True, "approved_by": "user"}
)

# Log a system command
logger.log_command(
    command="docker-compose up -d",
    output="Service started successfully",
    exit_code=0
)

# Log an API call
logger.log_api_call(
    endpoint="/api/v1/models",
    method="POST",
    request_data={"model": "gpt-4"},
    response_data={"status": "success"},
    status_code=200
)

# Get session summary
summary = logger.get_session_summary()
print(f"Total changes: {summary['total_changes']}")
```

### Query Logs

```python
from logging import LogQuery, ChangeType
from datetime import datetime, timedelta

query = LogQuery()

# Get recent changes
recent = query.get_recent_changes(hours=24, limit=100)

# Search for specific changes
results = query.query(
    change_types=[ChangeType.FILE_UPDATE, ChangeType.FILE_CREATE],
    file_path="api/",
    start_date=datetime.now() - timedelta(days=7),
    search_text="authentication"
)

# Get file history
history = query.get_file_history("/path/to/file.py")

# Generate audit report
report = query.generate_audit_report(
    start_date=datetime(2025, 11, 1),
    end_date=datetime(2025, 11, 5),
    output_file="audit_report.json"
)

# Analyze patterns
patterns = query.analyze_patterns(
    start_date=datetime.now() - timedelta(days=30)
)
```

### Storage Management

```python
from logging import LogStorage

storage = LogStorage()

# Get storage usage
usage = storage.get_storage_usage()
print(f"Total size: {usage['total_size_mb']:.2f} MB")
print(f"Usage: {usage['usage_percentage']:.1f}%")

# Run maintenance
results = storage.maintenance()
print(f"Compressed {results['compressed']} files")
print(f"Deleted {results['deleted_old']} old files")

# Export logs
storage.export_logs(
    output_file="exported_logs.json",
    start_date=datetime.now() - timedelta(days=7),
    format="json"
)
```

### Metrics Export

```python
from logging.metrics import LogMetrics

metrics = LogMetrics()

# Get current metrics
current = metrics.get_metrics(window_hours=24)
print(f"Changes per hour: {current['changes_per_hour']:.2f}")
print(f"Error rate: {current['error_rate']:.2f}%")

# Export to Prometheus
prometheus_metrics = metrics.export_prometheus_metrics(
    output_file="metrics.prom"
)

# Get health status
health = metrics.get_health_status()
print(f"Status: {health['status']}")
print(f"Message: {health['message']}")
```

## Command-Line Interface

### View Recent Changes

```bash
python -m logging.cli recent --hours 24 --limit 50
```

### Search Logs

```bash
# Search by change type
python -m logging.cli search --type file_update --type file_create

# Search by file
python -m logging.cli search --file "api/main.py"

# Search by text
python -m logging.cli search --text "authentication" --limit 20

# Complex search
python -m logging.cli search \
  --type file_update \
  --start-date 2025-11-01 \
  --end-date 2025-11-05 \
  --text "database" \
  --verbose
```

### File History

```bash
python -m logging.cli file-history api/main.py --verbose
```

### Session Logs

```bash
python -m logging.cli session abc123def456 --verbose
```

### Generate Audit Report

```bash
python -m logging.cli audit 2025-11-01 \
  --end-date 2025-11-05 \
  --output audit_report.json
```

### Storage Statistics

```bash
python -m logging.cli stats
```

### Run Maintenance

```bash
python -m logging.cli maintenance
```

### Export Logs

```bash
# Export as JSON
python -m logging.cli export logs_export.json --format json

# Export as CSV with date range
python -m logging.cli export logs_export.csv \
  --format csv \
  --start-date 2025-11-01 \
  --end-date 2025-11-05
```

### Pattern Analysis

```bash
python -m logging.cli patterns \
  --start-date 2025-11-01 \
  --end-date 2025-11-05
```

## Change Types

The system tracks the following change types:

- `file_create` - New file created
- `file_update` - Existing file modified
- `file_delete` - File deleted
- `git_commit` - Git commit created
- `git_push` - Git push executed
- `api_call` - API endpoint called
- `system_command` - System command executed
- `agent_decision` - Agent made a decision
- `config_change` - Configuration modified
- `model_inference` - AI model inference performed
- `database_write` - Database write operation
- `service_start` - Service started
- `service_stop` - Service stopped
- `deployment` - Deployment executed

## Log Levels

- `debug` - Detailed debugging information
- `info` - General informational messages
- `warning` - Warning messages
- `error` - Error messages
- `critical` - Critical issues

## Integration with Monitoring

### Prometheus Integration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'agent_logs'
    static_configs:
      - targets: ['localhost:9090']
    metric_path: '/metrics/agent_logs'
```

Export metrics:

```python
from logging.metrics import LogMetrics

metrics = LogMetrics()
metrics.export_prometheus_metrics(
    output_file="/var/lib/prometheus/agent_logs.prom"
)
```

### Grafana Dashboard

Import the provided Grafana dashboard template (coming soon) to visualize:
- Change rate over time
- Error rates
- Most modified files
- Agent activity
- Storage usage

## Storage Configuration

Default configuration:

- **Log Directory**: `logs/agent_changes/`
- **Max Log Age**: 30 days
- **Max Storage**: 500 MB
- **Compression Age**: 7 days

Customize in your code:

```python
from logging import LogStorage

storage = LogStorage(
    log_dir="custom/log/path",
    max_log_age_days=60,
    max_storage_mb=1000,
    compress_after_days=14
)
```

## Best Practices

1. **Initialize Once**: Create a single ChangeLogger instance per agent session
2. **Log Decisions**: Always log agent decisions with reasoning
3. **Track Files**: Log file changes with before/after content when possible
4. **Use Metadata**: Add relevant metadata to provide context
5. **Regular Maintenance**: Run maintenance periodically to manage storage
6. **Monitor Metrics**: Export metrics to your monitoring system
7. **Generate Audits**: Create regular audit reports for compliance

## Example: Complete Agent Integration

```python
from logging import ChangeLogger, ChangeType, LogLevel

class MyAgent:
    def __init__(self):
        self.logger = ChangeLogger(
            log_dir="logs/agent_changes",
            agent_id="my-agent-v1"
        )

    def process_task(self, task):
        # Log the decision to process
        self.logger.log_agent_decision(
            decision=f"Processing task: {task.name}",
            reasoning="Task matches agent capabilities",
            context={"task_id": task.id, "priority": task.priority}
        )

        try:
            # Perform task
            result = self._execute_task(task)

            # Log success
            self.logger.log(
                change_type=ChangeType.AGENT_DECISION,
                description=f"Task completed: {task.name}",
                metadata={"result": result},
                level=LogLevel.INFO
            )

        except Exception as e:
            # Log error
            self.logger.log(
                change_type=ChangeType.AGENT_DECISION,
                description=f"Task failed: {task.name}",
                metadata={"error": str(e)},
                level=LogLevel.ERROR
            )
            raise

    def deploy_code(self, files):
        for file_path, content in files.items():
            # Read current content
            before_content = self._read_file(file_path)

            # Write new content
            self._write_file(file_path, content)

            # Log the change
            self.logger.log_file_change(
                file_path=file_path,
                change_type=ChangeType.FILE_UPDATE,
                before_content=before_content,
                after_content=content,
                description=f"Deployed update to {file_path}"
            )

        # Log deployment
        self.logger.log(
            change_type=ChangeType.DEPLOYMENT,
            description=f"Deployed {len(files)} files",
            metadata={"files": list(files.keys())},
            level=LogLevel.INFO
        )
```

## Troubleshooting

### Logs Not Appearing

Check that the log directory exists and is writable:

```bash
ls -la logs/agent_changes/
```

### Storage Full

Run maintenance to clean up old logs:

```bash
python -m logging.cli maintenance
```

Or adjust storage limits:

```python
storage = LogStorage(max_storage_mb=1000)
storage.enforce_storage_quota()
```

### Performance Issues

- Use compression for old logs
- Increase `compress_after_days` setting
- Query with date ranges to limit results
- Use `limit` parameter in queries

## API Reference

See individual module documentation:

- [ChangeLogger API](./change_logger.py)
- [LogQuery API](./query.py)
- [LogStorage API](./storage.py)
- [LogMetrics API](./metrics.py)

## License

Part of Prime Spark AI platform. See LICENSE for details.
