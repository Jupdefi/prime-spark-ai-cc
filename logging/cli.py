#!/usr/bin/env python3
"""
Command-line interface for querying agent change logs.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .query import LogQuery
from .storage import LogStorage
from .change_logger import ChangeType, LogLevel


def format_log_entry(log: dict, verbose: bool = False) -> str:
    """Format a log entry for display"""
    timestamp = log.get("timestamp", "Unknown")
    change_type = log.get("change_type", "Unknown")
    description = log.get("description", "No description")
    log_id = log.get("id", "Unknown")

    output = f"[{timestamp}] [{change_type}] {description}"

    if verbose:
        output += f"\n  ID: {log_id}"
        if "file_path" in log:
            output += f"\n  File: {log['file_path']}"
        if "session_id" in log:
            output += f"\n  Session: {log['session_id']}"
        if "metadata" in log and log["metadata"]:
            output += f"\n  Metadata: {json.dumps(log['metadata'], indent=4)}"

    return output


def cmd_recent(args):
    """Show recent changes"""
    query = LogQuery(args.log_dir)
    logs = query.get_recent_changes(hours=args.hours, limit=args.limit)

    if not logs:
        print("No recent changes found.")
        return

    print(f"\nShowing {len(logs)} recent changes (last {args.hours} hours):\n")
    for log in logs:
        print(format_log_entry(log, args.verbose))
        print()


def cmd_search(args):
    """Search logs"""
    query = LogQuery(args.log_dir)

    # Parse change types if provided
    change_types = None
    if args.type:
        change_types = []
        for ct in args.type:
            try:
                change_types.append(ChangeType(ct))
            except ValueError:
                print(f"Warning: Invalid change type '{ct}', ignoring.")

    # Parse log level if provided
    log_level = None
    if args.level:
        try:
            log_level = LogLevel(args.level)
        except ValueError:
            print(f"Warning: Invalid log level '{args.level}', ignoring.")

    # Parse dates if provided
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)

    logs = query.query(
        change_types=change_types,
        file_path=args.file,
        session_id=args.session,
        agent_id=args.agent,
        start_date=start_date,
        end_date=end_date,
        log_level=log_level,
        search_text=args.text,
        limit=args.limit
    )

    if not logs:
        print("No matching logs found.")
        return

    print(f"\nFound {len(logs)} matching log entries:\n")
    for log in logs:
        print(format_log_entry(log, args.verbose))
        print()


def cmd_file_history(args):
    """Show file change history"""
    query = LogQuery(args.log_dir)
    logs = query.get_file_history(args.file_path)

    if not logs:
        print(f"No changes found for file: {args.file_path}")
        return

    print(f"\nChange history for {args.file_path} ({len(logs)} changes):\n")
    for log in logs:
        print(format_log_entry(log, args.verbose))
        print()


def cmd_session(args):
    """Show session logs"""
    query = LogQuery(args.log_dir)
    logs = query.get_session_logs(args.session_id)

    if not logs:
        print(f"No logs found for session: {args.session_id}")
        return

    print(f"\nSession {args.session_id} ({len(logs)} log entries):\n")
    for log in logs:
        print(format_log_entry(log, args.verbose))
        print()


def cmd_audit(args):
    """Generate audit report"""
    query = LogQuery(args.log_dir)

    start_date = datetime.fromisoformat(args.start_date)
    end_date = datetime.fromisoformat(args.end_date) if args.end_date else None

    report = query.generate_audit_report(start_date, end_date, args.output)

    print(f"\nAudit Report")
    print("=" * 60)
    print(f"Period: {report['audit_period']['start']} to {report['audit_period']['end']}")
    print(f"Total Changes: {report['total_changes']}")
    print(f"Sessions: {len(report['sessions'])}")
    print(f"Agents: {len(report['agents'])}")
    print()

    print("Change Breakdown:")
    for change_type, count in report['change_breakdown'].items():
        print(f"  {change_type}: {count}")
    print()

    if report['files_affected']:
        print(f"Top 10 Most Modified Files:")
        for file_path, count in list(report['files_affected'].items())[:10]:
            print(f"  {file_path}: {count} changes")
        print()

    if report['critical_events']:
        print(f"Critical Events: {len(report['critical_events'])}")
        for event in report['critical_events'][:5]:
            print(f"  [{event['timestamp']}] {event['description']}")
        print()

    if report['errors']:
        print(f"Errors: {len(report['errors'])}")
        for error in report['errors'][:5]:
            print(f"  [{error['timestamp']}] {error['description']}")
        print()

    if args.output:
        print(f"Full report saved to: {args.output}")


def cmd_stats(args):
    """Show storage statistics"""
    storage = LogStorage(args.log_dir)
    usage = storage.get_storage_usage()

    print("\nLog Storage Statistics")
    print("=" * 60)
    print(f"Total Files: {usage['total_files']}")
    print(f"  Uncompressed: {usage['uncompressed_files']}")
    print(f"  Compressed: {usage['compressed_files']}")
    print(f"Total Size: {usage['total_size_mb']:.2f} MB")
    print(f"Storage Limit: {usage['storage_limit_mb']:.2f} MB")
    print(f"Usage: {usage['usage_percentage']:.1f}%")
    print()


def cmd_maintenance(args):
    """Run maintenance tasks"""
    storage = LogStorage(args.log_dir)

    print("Running log maintenance...")
    results = storage.maintenance()

    print(f"Compressed {results['compressed']} old log files")
    print(f"Deleted {results['deleted_old']} expired log files")
    print(f"Deleted {results['deleted_quota']} log files to enforce quota")
    print("\nMaintenance complete.")


def cmd_export(args):
    """Export logs"""
    storage = LogStorage(args.log_dir)

    start_date = datetime.fromisoformat(args.start_date) if args.start_date else None
    end_date = datetime.fromisoformat(args.end_date) if args.end_date else None

    print(f"Exporting logs to {args.output} (format: {args.format})...")
    storage.export_logs(args.output, start_date, end_date, args.format)
    print("Export complete.")


def cmd_patterns(args):
    """Analyze patterns"""
    query = LogQuery(args.log_dir)

    start_date = datetime.fromisoformat(args.start_date) if args.start_date else None
    end_date = datetime.fromisoformat(args.end_date) if args.end_date else None

    analysis = query.analyze_patterns(start_date, end_date)

    print("\nPattern Analysis")
    print("=" * 60)
    print(f"Total Logs Analyzed: {analysis['total_logs']}")
    print()

    print("Most Common Operations:")
    for op, count in list(analysis['most_common_operations'].items())[:10]:
        print(f"  {op}: {count}")
    print()

    print("Most Active Files:")
    for file_path, count in list(analysis['most_active_files'].items())[:10]:
        print(f"  {file_path}: {count} changes")
    print()

    print("Agent Activity:")
    for agent_id, activity in analysis['agent_activity'].items():
        print(f"  {agent_id}: {activity['total_actions']} actions")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Query and analyze agent change logs"
    )

    parser.add_argument(
        '--log-dir',
        default='logs/agent_changes',
        help='Log directory (default: logs/agent_changes)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Recent command
    recent_parser = subparsers.add_parser('recent', help='Show recent changes')
    recent_parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    recent_parser.add_argument('--limit', type=int, default=50, help='Maximum results')
    recent_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    recent_parser.set_defaults(func=cmd_recent)

    # Search command
    search_parser = subparsers.add_parser('search', help='Search logs')
    search_parser.add_argument('--type', action='append', help='Filter by change type')
    search_parser.add_argument('--file', help='Filter by file path')
    search_parser.add_argument('--session', help='Filter by session ID')
    search_parser.add_argument('--agent', help='Filter by agent ID')
    search_parser.add_argument('--level', help='Filter by log level')
    search_parser.add_argument('--text', help='Search text in description/metadata')
    search_parser.add_argument('--start-date', help='Start date (ISO format)')
    search_parser.add_argument('--end-date', help='End date (ISO format)')
    search_parser.add_argument('--limit', type=int, default=50, help='Maximum results')
    search_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    search_parser.set_defaults(func=cmd_search)

    # File history command
    file_parser = subparsers.add_parser('file-history', help='Show file change history')
    file_parser.add_argument('file_path', help='File path to query')
    file_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    file_parser.set_defaults(func=cmd_file_history)

    # Session command
    session_parser = subparsers.add_parser('session', help='Show session logs')
    session_parser.add_argument('session_id', help='Session ID')
    session_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    session_parser.set_defaults(func=cmd_session)

    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Generate audit report')
    audit_parser.add_argument('start_date', help='Start date (ISO format)')
    audit_parser.add_argument('--end-date', help='End date (ISO format)')
    audit_parser.add_argument('--output', help='Output file path')
    audit_parser.set_defaults(func=cmd_audit)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show storage statistics')
    stats_parser.set_defaults(func=cmd_stats)

    # Maintenance command
    maint_parser = subparsers.add_parser('maintenance', help='Run maintenance tasks')
    maint_parser.set_defaults(func=cmd_maintenance)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export logs')
    export_parser.add_argument('output', help='Output file path')
    export_parser.add_argument('--format', choices=['jsonl', 'json', 'csv'], default='jsonl')
    export_parser.add_argument('--start-date', help='Start date (ISO format)')
    export_parser.add_argument('--end-date', help='End date (ISO format)')
    export_parser.set_defaults(func=cmd_export)

    # Patterns command
    patterns_parser = subparsers.add_parser('patterns', help='Analyze patterns')
    patterns_parser.add_argument('--start-date', help='Start date (ISO format)')
    patterns_parser.add_argument('--end-date', help='End date (ISO format)')
    patterns_parser.set_defaults(func=cmd_patterns)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
