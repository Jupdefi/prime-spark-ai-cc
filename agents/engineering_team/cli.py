#!/usr/bin/env python3
"""
Engineering Team CLI

Command-line interface for the Prime Spark Engineering Team.
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.engineering_team.orchestrator import EngineeringTeamOrchestrator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Prime Spark Engineering Team - AI Agent Orchestrator'
    )

    parser.add_argument(
        'command',
        choices=['deploy', 'status', 'project', 'task'],
        help='Command to execute'
    )

    parser.add_argument(
        '--project-file',
        help='Path to project JSON file'
    )

    parser.add_argument(
        '--task-file',
        help='Path to task JSON file'
    )

    parser.add_argument(
        '--description',
        help='Project or task description'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    team = EngineeringTeamOrchestrator()

    if args.command == 'deploy':
        print("🚀 Deploying Engineering Team...")
        print("✅ Team deployed and ready!")
        print("\nAvailable agents:")
        for agent_id, agent in team.agents.items():
            print(f"  - {agent.name} ({agent.role})")

    elif args.command == 'status':
        status = team.get_team_status()
        print(json.dumps(status, indent=2))

    elif args.command == 'project':
        if args.project_file:
            with open(args.project_file, 'r') as f:
                project = json.load(f)
        else:
            # Default example project
            project = {
                'name': 'Example Project',
                'description': args.description or 'Build a REST API',
                'requirements': ['Scalable', 'Secure', 'Well-documented'],
                'priority': 'medium'
            }

        results = team.execute_project(project)
        print("\n📊 Project Results:")
        print(json.dumps(results, indent=2))

    elif args.command == 'task':
        if args.task_file:
            with open(args.task_file, 'r') as f:
                task = json.load(f)
        else:
            print("Error: --task-file required for task command")
            return 1

        result = team.assign_task(task)
        print("\n📊 Task Result:")
        print(json.dumps(result, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main())
