#!/usr/bin/env bash
#
# Create a new rollback point for Prime Spark AI
#
# Usage: ./create_rollback_point.sh [description] [--include-volumes]
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
DESCRIPTION="${1:-Manual rollback point}"
INCLUDE_VOLUMES=false

if [[ "$2" == "--include-volumes" ]] || [[ "$1" == "--include-volumes" ]]; then
    INCLUDE_VOLUMES=true
    if [[ "$1" == "--include-volumes" ]]; then
        DESCRIPTION="${2:-Manual rollback point}"
    fi
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Prime Spark AI - Create Rollback Point            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

# Check if services are running
echo -e "${YELLOW}→${NC} Checking service status..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠ Warning: No services are currently running${NC}"
fi

# Create rollback point using Python
echo -e "${YELLOW}→${NC} Creating rollback point..."
echo -e "  Description: ${DESCRIPTION}"
echo -e "  Include volumes: ${INCLUDE_VOLUMES}"
echo ""

PYTHON_CMD="
from rollback import RollbackManager

manager = RollbackManager(project_root='.')
rp = manager.create_rollback_point(
    description='${DESCRIPTION}',
    include_volumes=${INCLUDE_VOLUMES}
)

print(f'Rollback ID: {rp.id}')
print(f'Services: {len(rp.services)}')
print(f'Images: {len(rp.docker_images)}')
print(f'Configs: {len(rp.config_hashes)}')
if rp.volumes:
    print(f'Volumes: {len(rp.volumes)}')
"

if python3 -c "$PYTHON_CMD" 2>&1; then
    echo ""
    echo -e "${GREEN}✓ Rollback point created successfully${NC}"
    echo ""
    echo -e "To rollback to this point, use:"
    echo -e "  ${BLUE}./rollback/scripts/rollback.sh <rollback-id>${NC}"
    echo ""
    echo -e "To list all rollback points:"
    echo -e "  ${BLUE}./rollback/scripts/list_rollback_points.sh${NC}"
else
    echo -e "${RED}✗ Failed to create rollback point${NC}"
    exit 1
fi
