#!/usr/bin/env python3
"""
Example usage of the Agent Change Logging System
"""

import time
from datetime import datetime
from .change_logger import ChangeLogger, ChangeType, LogLevel
from .query import LogQuery
from .storage import LogStorage
from .metrics import LogMetrics


def example_basic_logging():
    """Demonstrate basic logging operations"""
    print("\n" + "="*60)
    print("Example 1: Basic Logging Operations")
    print("="*60 + "\n")

    # Initialize logger
    logger = ChangeLogger(
        log_dir="logs/agent_changes",
        agent_id="example-agent"
    )

    # Log a file creation
    print("Logging file creation...")
    logger.log_file_change(
        file_path="/example/new_file.py",
        change_type=ChangeType.FILE_CREATE,
        after_content="def hello():\n    print('Hello, World!')\n",
        description="Created new Python file with hello function"
    )

    # Log a file update
    print("Logging file update...")
    logger.log_file_change(
        file_path="/example/config.yaml",
        change_type=ChangeType.FILE_UPDATE,
        before_content="timeout: 30\n",
        after_content="timeout: 60\n",
        description="Increased timeout from 30s to 60s"
    )

    # Log an agent decision
    print("Logging agent decision...")
    logger.log_agent_decision(
        decision="Optimize database queries",
        reasoning="Query performance has degraded by 40% over the past week",
        context={
            "avg_query_time_before": 250,
            "avg_query_time_now": 350,
            "degradation_pct": 40
        }
    )

    # Log a system command
    print("Logging system command...")
    logger.log_command(
        command="docker-compose restart api",
        output="Restarting prime-spark-ai_api_1 ... done",
        exit_code=0,
        working_dir="/home/user/prime-spark-ai"
    )

    # Log an API call
    print("Logging API call...")
    logger.log_api_call(
        endpoint="/api/v1/inference",
        method="POST",
        request_data={"model": "llama-3.2", "prompt": "Hello"},
        response_data={"response": "Hi there!", "tokens": 3},
        status_code=200
    )

    # Log a git operation
    print("Logging git commit...")
    logger.log_git_operation(
        operation="commit",
        description="Added new feature for user authentication",
        metadata={
            "commit_hash": "abc123def456",
            "branch": "feature/auth",
            "files_changed": 5
        }
    )

    # Get session summary
    print("\nSession Summary:")
    summary = logger.get_session_summary()
    print(f"  Session ID: {summary['session_id']}")
    print(f"  Total Changes: {summary['total_changes']}")
    print(f"  Change Types: {summary['change_types']}")
    print(f"  Files Modified: {len(summary['files_modified'])}")


def example_querying():
    """Demonstrate log querying"""
    print("\n" + "="*60)
    print("Example 2: Querying Logs")
    print("="*60 + "\n")

    query = LogQuery()

    # Get recent changes
    print("Getting recent changes...")
    recent = query.get_recent_changes(hours=24, limit=10)
    print(f"Found {len(recent)} recent changes")

    if recent:
        latest = recent[0]
        print(f"\nLatest change:")
        print(f"  Time: {latest['timestamp']}")
        print(f"  Type: {latest['change_type']}")
        print(f"  Description: {latest['description']}")

    # Search for file changes
    print("\nSearching for file changes...")
    file_changes = query.query(
        change_types=[
            ChangeType.FILE_CREATE,
            ChangeType.FILE_UPDATE,
            ChangeType.FILE_DELETE
        ],
        limit=5
    )
    print(f"Found {len(file_changes)} file changes")

    # Get file history
    if file_changes:
        file_path = file_changes[0].get('file_path')
        if file_path:
            print(f"\nGetting history for {file_path}...")
            history = query.get_file_history(file_path)
            print(f"Found {len(history)} changes to this file")


def example_analytics():
    """Demonstrate analytics features"""
    print("\n" + "="*60)
    print("Example 3: Analytics and Patterns")
    print("="*60 + "\n")

    query = LogQuery()

    # Analyze patterns
    print("Analyzing patterns...")
    patterns = query.analyze_patterns()

    print(f"\nTotal Logs Analyzed: {patterns['total_logs']}")

    print("\nMost Common Operations:")
    for op, count in list(patterns['most_common_operations'].items())[:5]:
        print(f"  {op}: {count}")

    if patterns['most_active_files']:
        print("\nMost Active Files:")
        for file_path, count in list(patterns['most_active_files'].items())[:5]:
            print(f"  {file_path}: {count} changes")

    print("\nAgent Activity:")
    for agent_id, activity in patterns['agent_activity'].items():
        print(f"  {agent_id}: {activity['total_actions']} actions")


def example_audit_report():
    """Demonstrate audit report generation"""
    print("\n" + "="*60)
    print("Example 4: Audit Report")
    print("="*60 + "\n")

    query = LogQuery()

    # Generate audit report for the last 7 days
    from datetime import timedelta
    start_date = datetime.now() - timedelta(days=7)

    print("Generating audit report for the last 7 days...")
    report = query.generate_audit_report(
        start_date=start_date,
        output_file="logs/audit_report_example.json"
    )

    print(f"\nAudit Report Summary:")
    print(f"  Period: {report['audit_period']['start']} to {report['audit_period']['end']}")
    print(f"  Total Changes: {report['total_changes']}")
    print(f"  Unique Sessions: {len(report['sessions'])}")
    print(f"  Active Agents: {len(report['agents'])}")

    print(f"\nChange Breakdown:")
    for change_type, count in list(report['change_breakdown'].items())[:10]:
        print(f"  {change_type}: {count}")

    if report['critical_events']:
        print(f"\nCritical Events: {len(report['critical_events'])}")

    if report['errors']:
        print(f"Errors: {len(report['errors'])}")

    print(f"\nReport saved to: logs/audit_report_example.json")


def example_storage_management():
    """Demonstrate storage management"""
    print("\n" + "="*60)
    print("Example 5: Storage Management")
    print("="*60 + "\n")

    storage = LogStorage()

    # Get storage usage
    print("Checking storage usage...")
    usage = storage.get_storage_usage()

    print(f"\nStorage Statistics:")
    print(f"  Total Files: {usage['total_files']}")
    print(f"  Uncompressed: {usage['uncompressed_files']}")
    print(f"  Compressed: {usage['compressed_files']}")
    print(f"  Total Size: {usage['total_size_mb']:.2f} MB")
    print(f"  Storage Limit: {usage['storage_limit_mb']:.2f} MB")
    print(f"  Usage: {usage['usage_percentage']:.1f}%")

    # Run maintenance
    print("\nRunning maintenance...")
    results = storage.maintenance()
    print(f"  Compressed: {results['compressed']} files")
    print(f"  Deleted (old): {results['deleted_old']} files")
    print(f"  Deleted (quota): {results['deleted_quota']} files")


def example_metrics():
    """Demonstrate metrics export"""
    print("\n" + "="*60)
    print("Example 6: Metrics Export")
    print("="*60 + "\n")

    metrics = LogMetrics()

    # Get current metrics
    print("Collecting metrics...")
    current = metrics.get_metrics(window_hours=24)

    print(f"\nMetrics (last 24 hours):")
    print(f"  Total Changes: {current['total_changes']}")
    print(f"  Changes per Hour: {current['changes_per_hour']:.2f}")
    print(f"  Error Count: {current['error_count']}")
    print(f"  Error Rate: {current['error_rate']:.2f}%")
    print(f"  File Changes: {current['file_changes']}")
    print(f"  API Calls: {current['api_calls']}")
    print(f"  Deployments: {current['deployments']}")

    # Get health status
    print("\nHealth Status:")
    health = metrics.get_health_status()
    print(f"  Status: {health['status']}")
    print(f"  Message: {health['message']}")
    print(f"  Error Rate: {health['error_rate']:.2f}%")

    # Export to Prometheus format
    print("\nExporting Prometheus metrics...")
    prometheus = metrics.export_prometheus_metrics(
        output_file="logs/metrics_example.prom"
    )
    print("  Saved to: logs/metrics_example.prom")

    # Export to JSON format
    print("\nExporting JSON metrics...")
    json_metrics = metrics.export_json_metrics(
        output_file="logs/metrics_example.json"
    )
    print("  Saved to: logs/metrics_example.json")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Agent Change Logging System - Examples")
    print("="*60)

    try:
        # Run all examples
        example_basic_logging()
        time.sleep(0.5)

        example_querying()
        time.sleep(0.5)

        example_analytics()
        time.sleep(0.5)

        example_audit_report()
        time.sleep(0.5)

        example_storage_management()
        time.sleep(0.5)

        example_metrics()

        print("\n" + "="*60)
        print("All Examples Completed Successfully!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
