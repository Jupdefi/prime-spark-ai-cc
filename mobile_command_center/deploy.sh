#!/bin/bash
# Prime Spark Mobile Command Center Deployment Script

set -e

echo "========================================"
echo "📱 Deploying Mobile Command Center"
echo "========================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check prerequisites
if ! command -v docker &> /dev/null; then
    print_error "Docker not installed"
    exit 1
fi
print_status "Docker found"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose not installed"
    exit 1
fi
print_status "Docker Compose found"

# Load environment
if [ -f ../.env ]; then
    print_status "Loading environment from .env"
    export $(cat ../.env | grep -v '^#' | xargs)
else
    print_warning "No .env file found"
fi

# Check if other agents are running
echo ""
echo "Checking agent dependencies..."

if curl -s -f http://localhost:8001/pulse/health > /dev/null 2>&1; then
    print_status "Pulse agent is running"
else
    print_warning "Pulse agent not running - some features will be limited"
fi

if curl -s -f http://localhost:8002/ > /dev/null 2>&1; then
    print_status "AI Bridge is running"
else
    print_warning "AI Bridge not running - LLM features will be limited"
fi

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true
print_status "Stopped existing containers"

# Build images
echo ""
echo "Building Docker images..."
docker-compose build
print_status "Images built"

# Start services
echo ""
echo "Starting Mobile Command Center..."
docker-compose up -d
print_status "Services started"

# Wait for services
echo ""
echo "Waiting for services to be ready..."
sleep 8

# Check health
if curl -s -f http://localhost:8003/health > /dev/null 2>&1; then
    print_status "Backend API is healthy!"
else
    print_warning "Backend API may not be ready yet"
fi

if curl -s -f http://localhost:3001/ > /dev/null 2>&1; then
    print_status "Frontend is accessible!"
else
    print_warning "Frontend may not be ready yet"
fi

echo ""
echo "========================================"
echo "📱 Mobile Command Center Deployed!"
echo "========================================"
echo ""
echo "📊 Access Points:"
echo "   - Frontend:  http://localhost:3001"
echo "   - Backend:   http://localhost:8003"
echo "   - API Docs:  http://localhost:8003/docs"
echo ""
echo "🔑 Default Credentials:"
echo "   - Username:  admin"
echo "   - Password:  SparkAI2025!"
echo ""
echo "🛠️  Management:"
echo "   - View logs:     docker-compose logs -f"
echo "   - Stop:          docker-compose down"
echo "   - Restart:       docker-compose restart"
echo "   - Backend logs:  docker-compose logs mobile-api"
echo "   - Frontend logs: docker-compose logs mobile-frontend"
echo ""
echo "📱 Mobile Access:"
echo "   - Add to Home Screen for PWA experience"
echo "   - Works on iOS Safari and Android Chrome"
echo "   - Responsive design for all screen sizes"
echo ""
echo "🔗 Integration:"
echo "   - Ensure Pulse agent is running (port 8001)"
echo "   - Ensure AI Bridge is running (port 8002)"
echo "   - Engineering Team available via Python API"
echo ""
echo "🚀 Next Steps:"
echo "   1. Open http://localhost:3001 in your browser"
echo "   2. Login with default credentials"
echo "   3. View agent status and infrastructure"
echo "   4. Try the LLM chat interface"
echo "   5. Monitor alerts from Pulse agent"
echo ""
echo "📱 For mobile access from other devices:"
echo "   - Find your Pi's IP: hostname -I"
echo "   - Access from mobile: http://YOUR_PI_IP:3001"
echo "   - Configure firewall if needed"
echo ""
