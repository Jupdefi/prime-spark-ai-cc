# Prime Spark AI - Quick Start Guide

Get Prime Spark AI up and running in under 10 minutes!

## Prerequisites

- Raspberry Pi 5 or compatible Linux system
- Python 3.11+
- Docker and Docker Compose
- 4GB+ RAM
- Network connectivity

## 1. Quick Installation

```bash
# Clone or navigate to the project
cd /home/pironman5/prime-spark-ai

# Copy environment template
cp .env.example .env

# Edit configuration (see below)
nano .env

# Run deployment script
sudo ./deployment/deploy.sh
```

## 2. Essential Configuration

Edit `.env` and set these minimum values:

```bash
# Set your IPs
CONTROL_PC_IP=192.168.1.100        # Your current machine
SPARK_AGENT_IP=192.168.1.92        # Your other Pi (if you have one)

# Set secure passwords
ADMIN_PASSWORD=your_secure_password_here
REDIS_PASSWORD=another_secure_password
JWT_SECRET=$(openssl rand -hex 32)  # Generate this first

# Cloud endpoints (if you have cloud VMs)
PRIMECORE4_IP=69.62.123.97
OLLAMA_CLOUD_URL=http://69.62.123.97:11434
```

Save and exit (Ctrl+X, Y, Enter).

## 3. Start Services

The deployment script will:
1. Check prerequisites
2. Setup VPN (optional)
3. Configure NAS mount (optional)
4. Start all services

Choose option **2** (Services only) for quickest start:

```bash
sudo ./deployment/deploy.sh
# Select: 2) Services only
```

## 4. Verify Installation

```bash
# Check service status
docker-compose ps

# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy", ...}
```

## 5. First API Call

```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "your_secure_password_here"
  }'

# Copy the access_token from response
```

## 6. Try LLM Inference

**Note**: Requires Ollama running locally or on cloud VM.

```bash
# Simple test (no auth required for LLM endpoint in this version)
curl -X POST http://localhost:8000/api/llm/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Say hello!",
    "model": "llama3.2:latest"
  }'
```

## 7. Explore API Documentation

Open in browser:
```
http://localhost:8000/docs
```

Interactive Swagger UI with all endpoints!

## Common Issues

### "Connection refused" to Ollama

**Problem**: Ollama not running.

**Solution**:
```bash
# Check Ollama status
systemctl status ollama

# Start if needed
sudo systemctl start ollama

# Install a model
ollama pull llama3.2:latest
```

### Redis connection error

**Problem**: Redis container not started.

**Solution**:
```bash
# Check Redis
docker-compose ps | grep redis

# Restart if needed
docker-compose restart redis
```

### "No healthy endpoints"

**Problem**: Neither edge nor cloud Ollama is reachable.

**Solution**:
```bash
# Check edge Ollama
curl http://localhost:11434/api/tags

# Check routing status
curl http://localhost:8000/api/routing/stats

# Update .env with correct Ollama URLs
```

### Permission denied on scripts

**Solution**:
```bash
chmod +x deployment/*.sh
```

## Next Steps

### 1. Setup VPN for Cloud Access

If you have cloud VMs:

```bash
# Run VPN setup
sudo ./deployment/setup-vpn.sh

# Test VPN connectivity
ping 10.8.0.11  # PrimeCore1
```

### 2. Configure NAS Storage

Mount your NAS for persistent storage:

```bash
# For NFS
sudo mount -t nfs 192.168.1.49:/export/prime-spark /mnt/nas

# Add to /etc/fstab for persistent mount
```

### 3. Install More Models

```bash
# On edge (Control PC)
ollama pull mistral:latest
ollama pull codellama:latest

# List models
curl http://localhost:8000/api/llm/models
```

### 4. Test Agent Coordination

```bash
# Submit a test task
curl -X POST http://localhost:8000/api/tasks/submit \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "test",
    "payload": {"message": "Hello from task queue!"}
  }'

# Check agent status
curl http://localhost:8000/api/agents/status
```

### 5. Monitor System Health

```bash
# Detailed health check
curl http://localhost:8000/api/health/detailed | jq

# View logs
docker-compose logs -f

# Check power status
curl http://localhost:8000/api/power/status
```

### 6. Enable Monitoring (Optional)

```bash
# Start Prometheus and Grafana
docker-compose --profile monitoring up -d

# Access:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Prime Spark AI                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  VPN Tunnel   ┌─────────────────┐    │
│  │  Edge Devices│◄──────────────►│  Cloud VMs      │    │
│  │              │  (WireGuard)   │                 │    │
│  │ • Control PC │                │ • PrimeCore1    │    │
│  │ • Spark Agent│                │ • PrimeCore4    │    │
│  └──────────────┘                └─────────────────┘    │
│         │                                 │              │
│         ▼                                 ▼              │
│  ┌──────────────────────────────────────────────┐       │
│  │         Unified API Layer (FastAPI)          │       │
│  └──────────────────────────────────────────────┘       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┬──────────────┬─────────────────┐     │
│  │ Routing      │ Memory       │ Agent           │     │
│  │ (Edge-first) │ (3-tier)     │ Coordination    │     │
│  └──────────────┴──────────────┴─────────────────┘     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Development Tips

### Run without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis separately
docker run -d -p 6379:6379 redis:7-alpine

# Run API directly
python -m api.main
```

### Add Custom Endpoints

Edit `api/main.py`:

```python
@app.get("/api/custom/hello")
async def custom_hello():
    return {"message": "Hello from custom endpoint!"}
```

Restart:
```bash
docker-compose restart api
```

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

## Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a service
docker-compose restart api

# View service status
docker-compose ps

# Access Redis CLI
docker exec -it prime-spark-redis redis-cli -a $REDIS_PASSWORD

# View API logs
docker-compose logs -f api

# Update after code changes
docker-compose build api
docker-compose up -d api
```

## Getting Help

1. **Check logs**: `docker-compose logs -f`
2. **Health check**: `curl http://localhost:8000/api/health/detailed`
3. **API docs**: http://localhost:8000/docs
4. **Read full documentation**: See `docs/` directory
5. **Open an issue**: GitHub issues with logs and config

## What's Next?

- Read the [Configuration Guide](CONFIGURATION.md)
- Explore the [API Documentation](API.md)
- Set up VPN for cloud access
- Configure your NAS for persistent storage
- Install additional Ollama models
- Integrate with your existing systems

**Welcome to Prime Spark AI!** 🚀

Making AI more fun, free, and fair.
