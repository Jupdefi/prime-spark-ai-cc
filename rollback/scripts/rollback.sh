#!/usr/bin/env bash
#
# Rollback Prime Spark AI to a previous state
#
# Usage: ./rollback.sh <rollback-id> [--dry-run]
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
DRY_RUN=false

if [[ "$2" == "--dry-run" ]] || [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    if [[ "$1" == "--dry-run" ]]; then
        ROLLBACK_ID="$2"
    fi
fi

if [[ -z "$ROLLBACK_ID" ]]; then
    echo -e "${RED}✗ Rollback ID required${NC}"
    echo ""
    echo "Usage: $0 <rollback-id> [--dry-run]"
    echo ""
    echo "To list available rollback points:"
    echo "  ./rollback/scripts/list_rollback_points.sh"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            Prime Spark AI - Rollback System                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if $DRY_RUN; then
    echo -e "${YELLOW}⚠ DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# Change to project root
cd "$PROJECT_ROOT"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

# Perform rollback using Python
echo -e "${YELLOW}→${NC} Initiating rollback..."
echo -e "  Target: ${ROLLBACK_ID}"
echo ""

PYTHON_CMD="
import sys
from rollback import RollbackManager

manager = RollbackManager(project_root='.')

# Perform rollback
success = manager.rollback('${ROLLBACK_ID}', dry_run=${DRY_RUN})

if success:
    sys.exit(0)
else:
    sys.exit(1)
"

if python3 -c "$PYTHON_CMD" 2>&1; then
    echo ""
    if $DRY_RUN; then
        echo -e "${GREEN}✓ Dry run completed${NC}"
        echo -e "  Run without --dry-run to perform actual rollback"
    else
        echo -e "${GREEN}✓ Rollback completed successfully${NC}"
        echo ""
        echo -e "Services have been restored to the previous state."
        echo ""
        echo -e "Verify deployment:"
        echo -e "  ${BLUE}docker-compose ps${NC}"
        echo -e "  ${BLUE}docker-compose logs${NC}"
    fi
    exit 0
else
    echo ""
    echo -e "${RED}✗ Rollback failed${NC}"
    echo ""
    echo -e "Check logs and service status:"
    echo -e "  ${BLUE}docker-compose ps${NC}"
    echo -e "  ${BLUE}docker-compose logs${NC}"
    exit 1
fi
