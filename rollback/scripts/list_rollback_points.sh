#!/usr/bin/env bash
#
# List all available rollback points
#
# Usage: ./list_rollback_points.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Prime Spark AI - Available Rollback Points         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# List rollback points using Python
PYTHON_CMD="
from rollback import RollbackManager
from datetime import datetime

manager = RollbackManager(project_root='.')
rollback_points = manager.list_rollback_points()

if not rollback_points:
    print('No rollback points available.')
    print()
    print('Create a rollback point with:')
    print('  ./rollback/scripts/create_rollback_point.sh \"Description\"')
else:
    print(f'Found {len(rollback_points)} rollback point(s):')
    print()

    for i, rp in enumerate(rollback_points, 1):
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(rp.timestamp)
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            time_str = rp.timestamp

        print(f'{i}. [{rp.id}]')
        print(f'   Description: {rp.description}')
        print(f'   Created: {time_str}')
        print(f'   Services: {\", \".join(rp.services)}')
        print(f'   Images: {len(rp.docker_images)}')

        if rp.metadata.get('git_commit'):
            git_commit = rp.metadata['git_commit'][:8]
            print(f'   Git commit: {git_commit}')

        if rp.volumes:
            print(f'   Volumes: {len(rp.volumes)} backed up')

        print()

    print('To rollback to a specific point:')
    print('  ./rollback/scripts/rollback.sh <rollback-id>')
    print()
    print('To perform a dry run first:')
    print('  ./rollback/scripts/rollback.sh <rollback-id> --dry-run')
"

python3 -c "$PYTHON_CMD" 2>&1
