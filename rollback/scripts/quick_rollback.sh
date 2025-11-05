#!/usr/bin/env bash
#
# Quick rollback to the most recent rollback point
#
# Usage: ./quick_rollback.sh [--dry-run]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Prime Spark AI - Quick Rollback                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Get most recent rollback point
PYTHON_CMD="
from rollback import RollbackManager

manager = RollbackManager(project_root='.')
rollback_points = manager.list_rollback_points()

if not rollback_points:
    print('ERROR:No rollback points available')
    exit(1)

# Get most recent
rp = rollback_points[0]
print(f'ID:{rp.id}')
print(f'DESC:{rp.description}')
print(f'TIME:{rp.timestamp}')
"

ROLLBACK_INFO=$(python3 -c "$PYTHON_CMD" 2>&1)

if [[ "$ROLLBACK_INFO" == ERROR:* ]]; then
    echo -e "${RED}✗ No rollback points available${NC}"
    echo ""
    echo "Create a rollback point first:"
    echo "  ./rollback/scripts/create_rollback_point.sh \"Description\""
    exit 1
fi

# Parse info
ROLLBACK_ID=$(echo "$ROLLBACK_INFO" | grep "^ID:" | cut -d: -f2)
DESCRIPTION=$(echo "$ROLLBACK_INFO" | grep "^DESC:" | cut -d: -f2-)
TIMESTAMP=$(echo "$ROLLBACK_INFO" | grep "^TIME:" | cut -d: -f2-)

echo -e "${YELLOW}→${NC} Rolling back to most recent point:"
echo -e "  ID: ${ROLLBACK_ID}"
echo -e "  Description: ${DESCRIPTION}"
echo -e "  Created: ${TIMESTAMP}"
echo ""

if $DRY_RUN; then
    exec "$SCRIPT_DIR/rollback.sh" "$ROLLBACK_ID" --dry-run
else
    # Ask for confirmation
    read -p "Proceed with rollback? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        exec "$SCRIPT_DIR/rollback.sh" "$ROLLBACK_ID"
    else
        echo -e "${YELLOW}Rollback cancelled${NC}"
        exit 0
    fi
fi
