#!/bin/bash
# Prime Spark AI - Main Deployment Script
# Deploys the complete system on edge or cloud nodes

set -e

echo "=================================================="
echo "Prime Spark AI - Deployment Script"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your configuration before continuing${NC}"
    read -p "Press enter to continue after editing .env, or Ctrl+C to exit..."
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${BLUE}Deployment Configuration:${NC}"
echo "  Node Type: ${NODE_TYPE:-edge}"
echo "  API Port: ${API_PORT:-8000}"
echo "  Power Mode: ${POWER_MODE:-auto}"
echo "  Routing Strategy: ${ROUTING_STRATEGY:-edge-first}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 3 found${NC}"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Docker not found. Installing...${NC}"
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        echo -e "${GREEN}✓ Docker installed${NC}"
    else
        echo -e "${GREEN}✓ Docker found${NC}"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}✓ Docker Compose installed${NC}"
    else
        echo -e "${GREEN}✓ Docker Compose found${NC}"
    fi
}

# Function to setup VPN
setup_vpn() {
    echo -e "${YELLOW}Setting up VPN...${NC}"

    if [ -f "$SCRIPT_DIR/setup-vpn.sh" ]; then
        bash "$SCRIPT_DIR/setup-vpn.sh"
    else
        echo -e "${YELLOW}VPN setup script not found. Skipping VPN setup.${NC}"
        echo -e "${YELLOW}You can run it manually later: ./deployment/setup-vpn.sh${NC}"
    fi
}

# Function to setup NAS mount
setup_nas() {
    echo -e "${YELLOW}Setting up NAS mount...${NC}"

    if [ -n "$NAS_SHARE_PATH" ] && [ "$NAS_SHARE_PATH" != "/mnt/nas" ]; then
        echo -e "${BLUE}NAS path already configured: $NAS_SHARE_PATH${NC}"
    else
        echo -e "${YELLOW}Creating NAS mount point...${NC}"
        sudo mkdir -p /mnt/nas

        # Note: Actual NAS mounting depends on your setup (NFS, SMB, etc.)
        echo -e "${YELLOW}Please configure your NAS mount in /etc/fstab if needed${NC}"
    fi
}

# Function to build and start services
start_services() {
    echo -e "${YELLOW}Building and starting services...${NC}"

    # Build Docker images
    docker-compose build

    # Start services
    docker-compose up -d

    echo -e "${GREEN}✓ Services started${NC}"
}

# Function to verify installation
verify_installation() {
    echo -e "${YELLOW}Verifying installation...${NC}"

    # Wait for API to be ready
    echo -n "Waiting for API to be ready"
    for i in {1..30}; do
        if curl -f http://localhost:${API_PORT}/health &> /dev/null; then
            echo ""
            echo -e "${GREEN}✓ API is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done

    # Show service status
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    docker-compose ps
}

# Main deployment flow
main() {
    echo -e "${BLUE}Starting deployment...${NC}"
    echo ""

    # Ask user what to deploy
    echo "What would you like to deploy?"
    echo "1) Full system (VPN + NAS + Services)"
    echo "2) Services only (skip VPN and NAS setup)"
    echo "3) VPN only"
    read -p "Enter choice [1-3]: " choice

    case $choice in
        1)
            check_prerequisites
            setup_vpn
            setup_nas
            start_services
            verify_installation
            ;;
        2)
            check_prerequisites
            start_services
            verify_installation
            ;;
        3)
            setup_vpn
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo "=================================================="
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "=================================================="
    echo ""
    echo "API available at: http://localhost:${API_PORT}"
    echo "API Documentation: http://localhost:${API_PORT}/docs"
    echo ""
    echo "Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart services: docker-compose restart"
    echo "  Check health: curl http://localhost:${API_PORT}/api/health/detailed"
    echo ""
    echo "Next steps:"
    echo "1. Test the API: curl http://localhost:${API_PORT}/health"
    echo "2. Login: curl -X POST http://localhost:${API_PORT}/api/auth/login \\"
    echo "          -H 'Content-Type: application/json' \\"
    echo "          -d '{\"username\":\"${ADMIN_USERNAME}\",\"password\":\"${ADMIN_PASSWORD}\"}'"
    echo "3. Try LLM inference: See API docs at /docs"
    echo ""
}

# Run main
main
