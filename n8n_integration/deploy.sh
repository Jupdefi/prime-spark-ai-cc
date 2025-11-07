#!/bin/bash
# Prime Spark N8N Integration Hub - Deployment Script

set -e

echo "========================================================================"
echo "🔗 DEPLOYING PRIME SPARK N8N INTEGRATION HUB"
echo "========================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    if [ -f ../.env ]; then
        echo -e "${YELLOW}⚠️  No .env file found in n8n_integration/${NC}"
        echo -e "${YELLOW}   Copying from parent directory...${NC}"
        cp ../.env .env
    else
        echo -e "${RED}❌ No .env file found${NC}"
        echo "Please create a .env file with N8N configuration."
        echo "Use .env.example as a template:"
        echo "  cp .env.example .env"
        echo "  nano .env"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Environment file found${NC}"
echo ""

# Check N8N configuration
source .env

if [ -z "$N8N_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  N8N_API_KEY not set in .env${NC}"
    echo "   N8N integration will not work without API key"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true
echo ""

# Build Docker image
echo "🏗️  Building Docker image..."
docker-compose build
echo ""

# Start services
echo "🚀 Starting N8N Integration Hub..."
docker-compose up -d
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check container status
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Containers are running${NC}"
else
    echo -e "${RED}❌ Containers failed to start${NC}"
    echo "View logs: docker-compose logs"
    exit 1
fi

# Check health endpoint
echo "🔍 Checking health endpoint..."
sleep 3

HEALTH_RESPONSE=$(curl -s http://localhost:8004/health || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ N8N Integration Hub is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed, but service may still be starting${NC}"
    echo "   Check status: curl http://localhost:8004/health"
fi

echo ""
echo "========================================================================"
echo "🎉 N8N INTEGRATION HUB DEPLOYED!"
echo "========================================================================"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🔗 Access Points:"
echo "   API:        http://localhost:8004"
echo "   Health:     http://localhost:8004/health"
echo "   Metrics:    http://localhost:8004/metrics"
echo "   Docs:       http://localhost:8004/docs"
echo "   WebSocket:  ws://localhost:8004/ws/n8n/executions"
echo ""
echo "🔑 API Key: $HUB_API_KEY"
echo "   Include in requests: -H \"X-API-Key: $HUB_API_KEY\""
echo ""
echo "📝 Quick Test:"
echo "   curl -H \"X-API-Key: $HUB_API_KEY\" http://localhost:8004/api/n8n/workflows"
echo ""
echo "📋 View Logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose down"
echo ""
echo "========================================================================"
echo ""
