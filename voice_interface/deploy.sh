#!/bin/bash
# Prime Spark Voice Command Hub - Deployment Script

set -e

echo "========================================================================"
echo "🎤 DEPLOYING PRIME SPARK VOICE COMMAND HUB"
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
        echo -e "${YELLOW}⚠️  No .env file found in voice_interface/${NC}"
        echo -e "${YELLOW}   Copying from parent directory...${NC}"
        cp ../.env .env
    else
        echo -e "${YELLOW}⚠️  No .env file found${NC}"
        echo "Creating .env from template..."
        cp .env.example .env
        echo -e "${YELLOW}   Please edit .env with your configuration${NC}"
    fi
fi

echo -e "${GREEN}✅ Environment file found${NC}"
echo ""

# Check for audio devices
echo "🔍 Checking audio devices..."
if [ -d "/dev/snd" ]; then
    echo -e "${GREEN}✅ Audio devices found${NC}"
    ls -l /dev/snd | grep -E "pcm|control" || echo -e "${YELLOW}   No PCM devices detected${NC}"
else
    echo -e "${RED}❌ No audio devices found${NC}"
    echo "   Voice hub needs audio devices to function"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Check for Whisper model
echo "🔍 Checking Whisper availability..."
python3 -c "import faster_whisper" 2>/dev/null && echo -e "${GREEN}✅ faster-whisper installed${NC}" || echo -e "${YELLOW}⚠️  faster-whisper not found (will install in container)${NC}"
echo ""

# Check for Ollama
echo "🔍 Checking Ollama availability..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not detected${NC}"
    echo "   Voice hub uses Ollama for NLU (optional)"
fi
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true
echo ""

# Build Docker image
echo "🏗️  Building Docker image..."
docker-compose build
echo ""

# Start services
echo "🚀 Starting Voice Command Hub..."
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

HEALTH_RESPONSE=$(curl -s http://localhost:8005/health || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Voice Command Hub is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed, but service may still be starting${NC}"
    echo "   Check status: curl http://localhost:8005/health"
fi

echo ""
echo "========================================================================"
echo "🎉 VOICE COMMAND HUB DEPLOYED!"
echo "========================================================================"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🔗 Access Points:"
echo "   API:        http://localhost:8005"
echo "   Health:     http://localhost:8005/health"
echo "   Metrics:    http://localhost:8005/metrics"
echo "   Docs:       http://localhost:8005/docs"
echo ""
echo "🎤 Voice Commands:"
echo "   Wake words: 'Hey Spark' or 'Hey Prime'"
echo "   Examples:"
echo "     - 'Check system status'"
echo "     - 'Show Pulse agent health'"
echo "     - 'Trigger deployment workflow'"
echo "     - 'What's the CPU usage?'"
echo "     - 'Help'"
echo ""
echo "🔑 API Key: \$HUB_API_KEY"
echo "   Include in requests: -H \"X-API-Key: \$HUB_API_KEY\""
echo ""
echo "🎙️ Hardware:"
if [ -d "/dev/snd" ]; then
    echo "   Audio devices: Available"
    echo "   ReSpeaker: Auto-detect enabled"
else
    echo "   Audio devices: Not detected"
fi
echo ""
echo "📝 Quick Test:"
echo "   # Check health"
echo "   curl http://localhost:8005/health"
echo ""
echo "   # Test transcription (requires audio file)"
echo "   curl -X POST -H \"X-API-Key: \$HUB_API_KEY\" \\"
echo "        -F \"file=@test_audio.wav\" \\"
echo "        http://localhost:8005/api/voice/transcribe"
echo ""
echo "📋 View Logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose down"
echo ""
echo "========================================================================"
echo ""
echo "⚠️  NOTE: Voice Command Hub requires:"
echo "   1. Audio input device (ReSpeaker USB 4 Mic Array recommended)"
echo "   2. Whisper model (downloads automatically on first use)"
echo "   3. Piper TTS (installed in container)"
echo "   4. Ollama running for NLU (optional)"
echo ""
