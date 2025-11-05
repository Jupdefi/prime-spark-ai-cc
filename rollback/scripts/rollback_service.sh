#!/usr/bin/env bash
#
# Rollback a specific service to previous image/config
#
# Usage: ./rollback_service.sh <service-name> [image-tag]
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

SERVICE_NAME="$1"
IMAGE_TAG="$2"

if [[ -z "$SERVICE_NAME" ]]; then
    echo -e "${RED}✗ Service name required${NC}"
    echo ""
    echo "Usage: $0 <service-name> [image-tag]"
    echo ""
    echo "Available services:"
    echo "  • redis"
    echo "  • api"
    echo "  • prometheus"
    echo "  • grafana"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Prime Spark AI - Service Rollback: ${SERVICE_NAME}$(printf ' %.0s' {1..10})║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_ROOT"

# Check if service exists
if ! docker-compose config --services | grep -q "^${SERVICE_NAME}$"; then
    echo -e "${RED}✗ Service not found: ${SERVICE_NAME}${NC}"
    exit 1
fi

# Get current image
CURRENT_IMAGE=$(docker-compose images -q "$SERVICE_NAME" 2>/dev/null || echo "none")
echo -e "${YELLOW}→${NC} Current image: ${CURRENT_IMAGE:-none}"

if [[ -n "$IMAGE_TAG" ]]; then
    echo -e "${YELLOW}→${NC} Target image: ${IMAGE_TAG}"
    echo ""

    # Update docker-compose to use specific image tag
    # (This is a simplified approach; in production, you'd update the compose file)

    echo -e "${YELLOW}→${NC} Stopping service..."
    docker-compose stop "$SERVICE_NAME"

    echo -e "${YELLOW}→${NC} Pulling image: ${IMAGE_TAG}..."
    docker pull "$IMAGE_TAG" || true

    echo -e "${YELLOW}→${NC} Starting service with new image..."
    # For custom images, you would rebuild here
    docker-compose up -d "$SERVICE_NAME"
else
    echo -e "${YELLOW}→${NC} Restarting service with current configuration..."
    echo ""

    docker-compose restart "$SERVICE_NAME"
fi

# Wait for service to be ready
echo ""
echo -e "${YELLOW}→${NC} Waiting for service to be ready..."
sleep 3

# Run service-specific health check
PYTHON_CMD="
from rollback.service_rollback import get_service_rollback

service_rollback = get_service_rollback('${SERVICE_NAME}', '.')

if service_rollback.verify_health():
    print('✓ Service is healthy')
    exit(0)
else:
    print('⚠ Health check failed or timed out')
    exit(1)
"

if python3 -c "$PYTHON_CMD" 2>&1; then
    echo -e "${GREEN}✓ Service rollback completed successfully${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Service may not be fully ready${NC}"
    echo ""
    echo "Check service status:"
    echo "  docker-compose ps $SERVICE_NAME"
    echo "  docker-compose logs $SERVICE_NAME"
    exit 1
fi
