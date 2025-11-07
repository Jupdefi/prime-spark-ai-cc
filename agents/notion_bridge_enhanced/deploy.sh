#!/bin/bash
# AI-Enhanced Notion Bridge Deployment Script

set -e

echo "========================================"
echo "🧠 Deploying AI-Enhanced Notion Bridge"
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

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not installed"
    exit 1
fi
print_status "Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose not installed"
    exit 1
fi
print_status "Docker Compose found"

# Check Ollama
echo ""
echo "Checking Ollama availability..."
if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_status "Ollama is running"
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; print(len(json.load(sys.stdin)['models']))")
    echo "   Available models: $MODELS"
else
    print_warning "Ollama not responding - AI features may not work"
    echo "   Start Ollama: systemctl start ollama"
fi

# Load environment
if [ -f ../../.env ]; then
    print_status "Loading environment from .env"
    export $(cat ../../.env | grep -v '^#' | xargs)
else
    print_warning "No .env file found"
fi

# Check Notion API key
if [ -z "$NOTION_API_KEY" ]; then
    print_error "NOTION_API_KEY not set in environment"
    exit 1
fi
print_status "Notion API key configured"

# Stop existing containers
echo ""
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true
print_status "Stopped existing containers"

# Build image
echo ""
echo "Building AI-Enhanced Bridge image..."
docker-compose build
print_status "Docker image built"

# Start services
echo ""
echo "Starting AI-Enhanced Notion Bridge..."
docker-compose up -d
print_status "Services started"

# Wait for service
echo ""
echo "Waiting for service to be ready..."
sleep 5

# Check health
if curl -s -f http://localhost:8002/ > /dev/null 2>&1; then
    print_status "AI-Enhanced Bridge is healthy!"
else
    print_warning "Service may not be ready yet. Check logs: docker-compose logs ai-bridge"
fi

echo ""
echo "========================================"
echo "🧠 AI-Enhanced Bridge Deployed!"
echo "========================================"
echo ""
echo "📊 Access Points:"
echo "   - API:            http://localhost:8002"
echo "   - Health:         http://localhost:8002/"
echo "   - Analyze Page:   POST /bridge/analyze/page/{page_id}"
echo "   - Get Summary:    GET /bridge/analyze/summary/{page_id}"
echo "   - Get Insights:   GET /bridge/analyze/insights/{page_id}"
echo "   - Semantic Search: POST /bridge/search/semantic"
echo "   - Ask LLM:        POST /bridge/llm/ask"
echo "   - List Models:    GET /bridge/llm/models"
echo ""
echo "🛠️  Management:"
echo "   - View logs:  docker-compose logs -f ai-bridge"
echo "   - Stop:       docker-compose down"
echo "   - Restart:    docker-compose restart ai-bridge"
echo ""
echo "🧪 Quick Test:"
echo '   curl http://localhost:8002/ | python3 -m json.tool'
echo ""
echo '   curl -X POST http://localhost:8002/bridge/llm/ask \\'
echo '     -H "Content-Type: application/json" \\'
echo '     -d '"'"'{"prompt": "What is Prime Spark AI?", "max_tokens": 100}'"'"
echo ""
