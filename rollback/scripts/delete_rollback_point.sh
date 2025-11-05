#!/usr/bin/env bash
#
# Delete a specific rollback point
#
# Usage: ./delete_rollback_point.sh <rollback-id>
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

# Parse arguments
ROLLBACK_ID="$1"

if [[ -z "$ROLLBACK_ID" ]]; then
    echo -e "${RED}✗ Rollback ID required${NC}"
    echo ""
    echo "Usage: $0 <rollback-id>"
    echo ""
    echo "To list available rollback points:"
    echo "  ./rollback/scripts/list_rollback_points.sh"
    exit 1
fi

echo -e "${YELLOW}⚠ Deleting rollback point: ${ROLLBACK_ID}${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Delete using Python
PYTHON_CMD="
import sys
from rollback import RollbackManager

manager = RollbackManager(project_root='.')

if manager.delete_rollback_point('${ROLLBACK_ID}'):
    sys.exit(0)
else:
    print('Rollback point not found: ${ROLLBACK_ID}')
    sys.exit(1)
"

if python3 -c "$PYTHON_CMD" 2>&1; then
    echo -e "${GREEN}✓ Rollback point deleted${NC}"
    exit 0
else
    echo -e "${RED}✗ Failed to delete rollback point${NC}"
    exit 1
fi
