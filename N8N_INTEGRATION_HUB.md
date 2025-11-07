# 🔗 PRIME SPARK N8N INTEGRATION HUB

**Deployment Date**: 2025-11-07
**Status**: ✅ READY FOR DEPLOYMENT
**Version**: 1.0.0
**Location**: `/home/pironman5/prime-spark-ai/n8n_integration/`

---

## 🎯 WHAT IS IT?

The **Prime Spark N8N Integration Hub** provides bidirectional integration between Prime Spark agents and your 140+ N8N workflows, enabling automated task execution, workflow orchestration, and event-driven automation across your entire AI infrastructure.

### Key Features

🔍 **Workflow Discovery & Catalog**
- Automatic discovery of all N8N workflows
- Smart categorization (monitoring, alerts, deployment, etc.)
- Searchable workflow catalog
- Caching for fast lookup
- Metadata tracking

⚡ **Workflow Execution**
- Trigger workflows from Prime Spark agents
- Batch workflow execution
- Priority queuing
- Async and sync execution modes
- Timeout and retry handling

📨 **Webhook System**
- Receive callbacks from N8N workflows
- Route webhooks to appropriate agents
- HMAC signature verification
- Webhook payload validation

📊 **Monitoring & Tracking**
- Real-time execution tracking
- Workflow success/failure monitoring
- Execution history (last 1000)
- Performance metrics
- WebSocket real-time updates

🔗 **Agent Integration**
- **Pulse**: Trigger monitoring workflows
- **AI Bridge**: Trigger analysis workflows
- **Engineering Team**: Trigger deployment workflows
- **Mobile Command Center**: Trigger any workflow

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│         N8N INTEGRATION HUB ARCHITECTURE            │
└─────────────────────────────────────────────────────┘

Prime Spark Agents                    N8N Workflows
      │                                     │
      ├─ Pulse (8001)                      │
      ├─ AI Bridge (8002)                  │
      ├─ Mobile (8003)                     │
      │                                     │
      └────────────┐                       │
                   ▼                       ▼
           ┌────────────────┐      ┌──────────────┐
           │  N8N HUB API   │◄────►│  N8N API     │
           │   Port 8004    │      │  REST + WH   │
           └────────┬───────┘      └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │ Redis Cache  │
            │  Port 6379   │
            └──────────────┘

Data Flow:
1. Agent → Hub: Trigger workflow
2. Hub → N8N: Execute workflow
3. N8N → Hub: Webhook callback
4. Hub → Agent: Deliver results
```

### Tech Stack

**Backend:**
- FastAPI + WebSockets
- Redis caching (workflow metadata, execution history)
- Pydantic models for validation
- HMAC signature verification
- API key authentication

**Integration:**
- N8N REST API client
- Webhook handlers
- Event broadcasting
- Real-time status updates

**Deployment:**
- Docker + Docker Compose
- Health checks
- Auto-restart policies
- Volume persistence

---

## 📁 FILE STRUCTURE

```
n8n_integration/
├── n8n_hub.py              # Main hub implementation (1,200+ lines)
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Orchestration
├── .env.example          # Environment template
├── deploy.sh             # Deployment script
└── build_results.json    # Architecture design
```

---

## 🚀 DEPLOYMENT

### Prerequisites

1. **Docker & Docker Compose** installed
2. **N8N instance** running with API access
3. **N8N API Key** for authentication
4. **Prime Spark agents** (optional but recommended)

### Quick Deploy

```bash
cd /home/pironman5/prime-spark-ai/n8n_integration

# Copy environment template
cp .env.example .env

# Edit with your N8N credentials
nano .env

# Deploy
./deploy.sh
```

The deployment script will:
1. ✅ Check prerequisites
2. ✅ Verify environment configuration
3. ✅ Build Docker image
4. ✅ Start services (Hub + Redis)
5. ✅ Verify health

### Manual Deployment

```bash
cd /home/pironman5/prime-spark-ai/n8n_integration

# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## ⚙️ CONFIGURATION

### Environment Variables

**Required:**

```bash
# N8N Configuration
N8N_API_URL=https://n8n.example.com/api/v1
N8N_API_KEY=your-n8n-api-key
N8N_WEBHOOK_URL=https://n8n.example.com/webhook
N8N_WEBHOOK_SECRET=your-webhook-secret

# Redis
REDIS_PASSWORD=your-redis-password

# Hub
HUB_API_KEY=prime-spark-n8n-key
```

**Optional (with defaults):**

```bash
# Performance
CACHE_TTL=3600                    # Cache lifetime (seconds)
MAX_CONCURRENT_WORKFLOWS=10       # Max parallel executions
WORKFLOW_TIMEOUT=60               # Execution timeout (seconds)
RATE_LIMIT_PER_MINUTE=100         # API rate limit

# Agent URLs (auto-detected)
PULSE_API_URL=http://localhost:8001
AI_BRIDGE_API_URL=http://localhost:8002
MOBILE_API_URL=http://localhost:8003
```

### N8N Setup

1. **Enable N8N API**
   - Settings → API → Enable API Access
   - Generate API Key

2. **Configure Webhooks**
   - Note your N8N webhook URL
   - Set webhook secret for security
   - Configure webhook callbacks to point to Hub

3. **Tag Your Workflows**
   - Add tags for categorization (monitoring, alerts, etc.)
   - Tag workflows to make them discoverable
   - Update workflow descriptions

---

## 📱 ACCESS & USAGE

### API Access

**Base URL:** `http://localhost:8004`

**Authentication:** API Key required
```bash
curl -H "X-API-Key: prime-spark-n8n-key" http://localhost:8004/api/n8n/workflows
```

**Interactive Docs:** `http://localhost:8004/docs`

**Health Check:** `http://localhost:8004/health`

**Metrics:** `http://localhost:8004/metrics`

### WebSocket Access

**Execution Updates:** `ws://localhost:8004/ws/n8n/executions`

**Hub Status:** `ws://localhost:8004/ws/n8n/status`

---

## 🔌 API ENDPOINTS

### Workflow Discovery

```
GET    /api/n8n/workflows                    # List all workflows
GET    /api/n8n/workflows/{workflow_id}      # Get workflow details
GET    /api/n8n/workflows/search?q=query     # Search workflows
GET    /api/n8n/workflows/categories         # List categories
```

**Example:**
```bash
# List all workflows
curl -H "X-API-Key: prime-spark-n8n-key" \
  http://localhost:8004/api/n8n/workflows

# Search workflows
curl -H "X-API-Key: prime-spark-n8n-key" \
  "http://localhost:8004/api/n8n/workflows/search?q=monitoring"

# Get categories
curl -H "X-API-Key: prime-spark-n8n-key" \
  http://localhost:8004/api/n8n/workflows/categories
```

### Workflow Execution

```
POST   /api/n8n/execute/{workflow_id}        # Trigger workflow
POST   /api/n8n/execute/batch                # Trigger multiple
GET    /api/n8n/execute/status/{exec_id}     # Get execution status
POST   /api/n8n/execute/cancel/{exec_id}     # Cancel execution
```

**Example: Trigger Workflow**
```bash
curl -X POST \
  -H "X-API-Key: prime-spark-n8n-key" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "abc123",
    "data": {"message": "Hello from Prime Spark"},
    "agent_id": "pulse",
    "priority": "high",
    "async_execution": true
  }' \
  http://localhost:8004/api/n8n/execute/abc123
```

**Example: Batch Execution**
```bash
curl -X POST \
  -H "X-API-Key: prime-spark-n8n-key" \
  -H "Content-Type: application/json" \
  -d '{
    "workflows": [
      {"workflow_id": "wf1", "data": {"type": "health"}},
      {"workflow_id": "wf2", "data": {"type": "metrics"}}
    ],
    "sequential": false,
    "stop_on_error": false
  }' \
  http://localhost:8004/api/n8n/execute/batch
```

### Execution Monitoring

```
GET    /api/n8n/executions                   # List executions
GET    /api/n8n/executions/{execution_id}    # Get execution details
GET    /api/n8n/executions/{exec_id}/logs    # Get execution logs
```

**Example: List Executions**
```bash
# All executions
curl -H "X-API-Key: prime-spark-n8n-key" \
  http://localhost:8004/api/n8n/executions

# Filter by workflow
curl -H "X-API-Key: prime-spark-n8n-key" \
  "http://localhost:8004/api/n8n/executions?workflow_id=abc123"

# Filter by status
curl -H "X-API-Key: prime-spark-n8n-key" \
  "http://localhost:8004/api/n8n/executions?status=running"
```

### Webhooks

```
POST   /webhook/n8n/{agent_id}              # Receive N8N callback
```

**Configure in N8N:**
- Webhook URL: `http://YOUR_HUB_IP:8004/webhook/n8n/pulse`
- Method: POST
- Authentication: None (uses HMAC signature)
- Headers: `X-N8N-Signature: <hmac-sha256>`

**Example Payload:**
```json
{
  "execution_id": "exec_20251107_123456_abc12345",
  "workflow_id": "abc123",
  "workflow_name": "Health Check Monitor",
  "status": "success",
  "data": {
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "disk_usage": 38.5
  },
  "timestamp": "2025-11-07T21:30:00Z"
}
```

### WebSocket

```
WS     /ws/n8n/executions                   # Real-time execution updates
WS     /ws/n8n/status                       # Hub status updates
```

**Example (Python):**
```python
import asyncio
import websockets
import json

async def watch_executions():
    uri = "ws://localhost:8004/ws/n8n/executions"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Execution update: {data['type']}")
            print(f"Status: {data['data']['status']}")

asyncio.run(watch_executions())
```

---

## 🔗 AGENT INTEGRATION

### Pulse Agent Integration

Pulse can trigger monitoring workflows based on health checks:

```python
import requests

# Pulse detects high CPU usage
def on_high_cpu_alert(node_id, cpu_usage):
    # Trigger N8N alert workflow
    response = requests.post(
        "http://localhost:8004/api/n8n/execute/monitoring_alert",
        headers={"X-API-Key": "prime-spark-n8n-key"},
        json={
            "workflow_id": "monitoring_alert",
            "data": {
                "alert_type": "high_cpu",
                "node_id": node_id,
                "cpu_usage": cpu_usage,
                "severity": "warning"
            },
            "agent_id": "pulse",
            "priority": "high"
        }
    )
```

### AI Bridge Integration

AI Bridge can trigger analysis workflows after content analysis:

```python
# AI Bridge completes page analysis
def on_analysis_complete(page_id, insights):
    # Trigger documentation workflow
    requests.post(
        "http://localhost:8004/api/n8n/execute/create_documentation",
        headers={"X-API-Key": "prime-spark-n8n-key"},
        json={
            "workflow_id": "create_documentation",
            "data": {
                "page_id": page_id,
                "insights": insights,
                "auto_publish": True
            },
            "agent_id": "ai-bridge",
            "async_execution": True
        }
    )
```

### Mobile Command Center Integration

Mobile can trigger any workflow on-demand:

```typescript
// Mobile UI: Trigger workflow button
async function triggerWorkflow(workflowId: string) {
  const response = await fetch(
    `http://localhost:8004/api/n8n/execute/${workflowId}`,
    {
      method: 'POST',
      headers: {
        'X-API-Key': 'prime-spark-n8n-key',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        workflow_id: workflowId,
        agent_id: 'mobile',
        priority: 'normal',
        async_execution: true
      })
    }
  );

  return await response.json();
}
```

---

## 📊 WORKFLOW CATEGORIES

The hub automatically categorizes workflows:

| Category | Description | Example Workflows |
|----------|-------------|-------------------|
| **monitoring** | Health checks, system monitoring | CPU monitor, Service health check |
| **alerts** | Notifications, warnings | Slack alerts, Email notifications |
| **deployment** | CI/CD, releases | Deploy to production, Run tests |
| **analysis** | Data analysis, insights | Log analysis, Metrics aggregation |
| **documentation** | Docs generation | Generate README, Update wiki |
| **integration** | Third-party integrations | Sync to GitHub, Update Notion |
| **automation** | Scheduled tasks | Daily reports, Backups |
| **other** | Uncategorized workflows | Custom workflows |

---

## 🧪 TESTING

### Health Check

```bash
curl http://localhost:8004/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-07T21:30:00",
  "redis": "connected",
  "active_executions": 2,
  "websocket_connections": 1,
  "n8n_reachable": true
}
```

### Discover Workflows

```bash
curl -H "X-API-Key: prime-spark-n8n-key" \
  http://localhost:8004/api/n8n/workflows
```

### Trigger Test Workflow

```bash
curl -X POST \
  -H "X-API-Key: prime-spark-n8n-key" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test_workflow",
    "data": {"test": true},
    "agent_id": "manual",
    "priority": "normal",
    "async_execution": false
  }' \
  http://localhost:8004/api/n8n/execute/test_workflow
```

### Check Metrics

```bash
curl http://localhost:8004/metrics
```

**Expected Response:**
```json
{
  "active_executions": 0,
  "total_executions": 42,
  "status_distribution": {
    "pending": 0,
    "running": 0,
    "success": 38,
    "failed": 4,
    "cancelled": 0,
    "timeout": 0
  },
  "websocket_connections": 1,
  "cache_enabled": true,
  "max_concurrent": 10
}
```

---

## 🐛 TROUBLESHOOTING

### Hub Not Starting

```bash
# Check logs
docker-compose logs n8n-hub

# Common issues:
# 1. Port 8004 already in use
sudo lsof -i :8004

# 2. Redis not connecting
docker-compose logs n8n-redis

# 3. Environment variables missing
docker-compose exec n8n-hub env | grep N8N
```

### Cannot Discover Workflows

**Problem:** `/api/n8n/workflows` returns empty or error

**Solutions:**
```bash
# 1. Check N8N API credentials
curl -H "X-N8N-API-KEY: your-key" https://n8n.example.com/api/v1/workflows

# 2. Verify N8N_API_URL in .env
docker-compose exec n8n-hub env | grep N8N_API_URL

# 3. Check N8N is reachable from Docker
docker-compose exec n8n-hub curl https://n8n.example.com/api/v1/workflows

# 4. Force refresh cache
curl -H "X-API-Key: prime-spark-n8n-key" \
  "http://localhost:8004/api/n8n/workflows?refresh=true"
```

### Workflow Execution Fails

**Problem:** Workflow triggers but fails immediately

**Solutions:**
```bash
# 1. Check execution logs
curl -H "X-API-Key: prime-spark-n8n-key" \
  http://localhost:8004/api/n8n/executions/{execution_id}/logs

# 2. Verify workflow is active
curl -H "X-API-Key: prime-spark-n8n-key" \
  http://localhost:8004/api/n8n/workflows/{workflow_id}

# 3. Check N8N workflow execution logs in N8N UI

# 4. Increase timeout if needed
# Edit docker-compose.yml: WORKFLOW_TIMEOUT=120
docker-compose down && docker-compose up -d
```

### Webhooks Not Received

**Problem:** N8N sends webhook but Hub doesn't receive

**Solutions:**
```bash
# 1. Check webhook URL is correct
# In N8N: http://YOUR_HUB_IP:8004/webhook/n8n/pulse

# 2. Verify webhook secret matches
docker-compose exec n8n-hub env | grep N8N_WEBHOOK_SECRET

# 3. Check webhook signature verification
# View Hub logs for signature errors
docker-compose logs n8n-hub | grep webhook

# 4. Test webhook manually
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "test",
    "workflow_id": "test",
    "workflow_name": "Test",
    "status": "success",
    "timestamp": "2025-11-07T21:30:00Z"
  }' \
  http://localhost:8004/webhook/n8n/pulse
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps n8n-redis

# Check Redis logs
docker-compose logs n8n-redis

# Test Redis connection
docker-compose exec n8n-redis redis-cli ping

# Test with password
docker-compose exec n8n-redis redis-cli -a YOUR_PASSWORD ping

# Restart Redis
docker-compose restart n8n-redis
```

---

## 🔐 SECURITY

### API Key Authentication

All API endpoints (except webhooks) require API key:

```bash
# Include in header
curl -H "X-API-Key: prime-spark-n8n-key" http://localhost:8004/api/n8n/workflows
```

**Change Default API Key:**
```bash
# Edit .env
HUB_API_KEY=your-secure-key-here

# Restart
docker-compose restart n8n-hub
```

### Webhook Signature Verification

N8N webhooks are verified using HMAC-SHA256:

```python
import hmac
import hashlib

# In N8N workflow:
signature = hmac.new(
    webhook_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

# Include in request header: X-N8N-Signature
```

### Production Checklist

- [ ] Change default API keys
- [ ] Configure HTTPS/SSL (use reverse proxy)
- [ ] Restrict network access (firewall rules)
- [ ] Enable webhook signature verification
- [ ] Use strong Redis password
- [ ] Monitor failed authentication attempts
- [ ] Set up rate limiting
- [ ] Configure CORS for production
- [ ] Regular security updates
- [ ] Backup Redis data

---

## 📈 MONITORING

### Application Logs

```bash
# View all logs
docker-compose logs -f

# Hub logs only
docker-compose logs -f n8n-hub

# Redis logs only
docker-compose logs -f n8n-redis

# Last 100 lines
docker-compose logs --tail=100 n8n-hub
```

### Container Health

```bash
# Check container status
docker-compose ps

# Inspect health
docker inspect prime-spark-n8n-hub | grep -A 10 Health

# Resource usage
docker stats prime-spark-n8n-hub prime-spark-n8n-redis
```

### Hub Metrics

```bash
# Get current metrics
curl http://localhost:8004/metrics

# Watch metrics (every 5 seconds)
watch -n 5 curl -s http://localhost:8004/metrics | jq
```

### Real-time Monitoring

```bash
# WebSocket monitoring (requires websocat)
websocat ws://localhost:8004/ws/n8n/status

# Or use Python:
python -c "
import asyncio
import websockets
import json

async def monitor():
    uri = 'ws://localhost:8004/ws/n8n/status'
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            print(json.dumps(json.loads(msg), indent=2))

asyncio.run(monitor())
"
```

---

## 🚀 PRODUCTION DEPLOYMENT

### Deploy to VPS

```bash
# 1. Copy files to VPS
scp -r n8n_integration user@PRIMECORE1_IP:/opt/prime-spark/

# 2. SSH to VPS
ssh user@PRIMECORE1_IP
cd /opt/prime-spark/n8n_integration

# 3. Configure environment
cp .env.example .env
nano .env  # Add N8N credentials

# 4. Deploy
./deploy.sh

# 5. Verify
curl http://localhost:8004/health
```

### Configure Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/n8n-hub
server {
    listen 80;
    server_name n8n-hub.primespark.ai;

    location / {
        proxy_pass http://localhost:8004;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d n8n-hub.primespark.ai

# Auto-renew
sudo systemctl enable certbot.timer
```

### Firewall Configuration

```bash
# Allow N8N Hub
sudo ufw allow 8004/tcp

# For production with reverse proxy
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 💡 USE CASES

### 1. Automated Monitoring

Pulse detects issues → Triggers N8N alert workflow → Sends notifications

```python
# In Pulse agent
if cpu_usage > 90:
    trigger_workflow("high_cpu_alert", {
        "node": node_id,
        "cpu": cpu_usage,
        "severity": "critical"
    })
```

### 2. Content Pipeline

AI Bridge analyzes page → Triggers documentation workflow → Updates wiki

```python
# In AI Bridge
insights = analyze_notion_page(page_id)
trigger_workflow("update_documentation", {
    "page_id": page_id,
    "insights": insights,
    "auto_publish": True
})
```

### 3. Deployment Automation

Engineering Team completes feature → Triggers deployment workflow → Deploys to production

```python
# In Engineering Team
project_complete = build_feature(spec)
trigger_workflow("deploy_to_production", {
    "project_id": project_id,
    "version": "1.2.0",
    "environment": "production"
})
```

### 4. Scheduled Tasks

N8N cron workflow runs → Sends webhook to Hub → Triggers agent action

```
N8N Daily Report Workflow:
1. Collect metrics from all agents
2. Generate report
3. Send webhook to Mobile Command Center
4. Display in dashboard
```

### 5. Multi-Workflow Orchestration

Complex task requires multiple workflows running in sequence:

```python
# Trigger batch sequential execution
workflows = [
    {"workflow_id": "backup_data"},
    {"workflow_id": "run_analysis"},
    {"workflow_id": "generate_report"},
    {"workflow_id": "send_notifications"}
]

trigger_batch(workflows, sequential=True, stop_on_error=True)
```

---

## 🎯 ROADMAP

### Phase 2 (Coming Soon)

- [ ] Workflow templates (pre-configured patterns)
- [ ] Conditional workflow chaining
- [ ] Advanced retry strategies
- [ ] Workflow scheduling via Hub
- [ ] Multi-N8N instance support
- [ ] Workflow versioning
- [ ] Execution analytics dashboard
- [ ] Custom webhook routing rules

### Phase 3 (Future)

- [ ] Workflow A/B testing
- [ ] Machine learning for workflow optimization
- [ ] Visual workflow builder integration
- [ ] Distributed execution across nodes
- [ ] Workflow marketplace
- [ ] Advanced security (OAuth2, SSO)
- [ ] GraphQL API
- [ ] Workflow debugging tools

---

## 📞 SUPPORT

### Common Commands

```bash
# Restart Hub
docker-compose restart n8n-hub

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View environment
docker-compose exec n8n-hub env

# Shell into container
docker-compose exec n8n-hub bash

# Clear Redis cache
docker-compose exec n8n-redis redis-cli -a PASSWORD FLUSHDB
```

### Logs Location

- **Container logs:** `docker-compose logs`
- **Hub application logs:** Stdout (captured by Docker)
- **Redis logs:** `docker-compose logs n8n-redis`

### Quick Diagnostics

```bash
# Full diagnostic check
echo "=== N8N Hub Health ==="
curl -s http://localhost:8004/health | jq

echo -e "\n=== Container Status ==="
docker-compose ps

echo -e "\n=== Resource Usage ==="
docker stats --no-stream prime-spark-n8n-hub

echo -e "\n=== Recent Logs ==="
docker-compose logs --tail=20 n8n-hub
```

---

## ✨ ALIGNMENT WITH PRIME SPARK VALUES

The N8N Integration Hub embodies Prime Spark principles:

1. **Soul Before System** ✅
   - Workflow automation serves agents and users
   - Human-in-the-loop for critical workflows
   - Meaningful categorization and discovery

2. **Vision as Directive** ✅
   - Scalable to 1000+ workflows
   - Future-ready architecture
   - Event-driven automation

3. **Decentralize the Power** ✅
   - No central control bottleneck
   - Distributed workflow execution
   - Agent autonomy preserved

4. **Creative Flow is Sacred** ✅
   - Frictionless workflow triggering
   - Real-time feedback
   - No manual intervention needed

5. **Agents Are Archetypes** ✅
   - Hub = "The Conductor"
   - Orchestrates all workflows
   - Enables agent collaboration

---

## 🎯 READY TO USE!

The N8N Integration Hub is **ready for deployment**!

### Quick Start

```bash
cd /home/pironman5/prime-spark-ai/n8n_integration

# Configure
cp .env.example .env
nano .env  # Add your N8N credentials

# Deploy
./deploy.sh
```

Then access:
- **API**: http://localhost:8004
- **Docs**: http://localhost:8004/docs
- **Health**: http://localhost:8004/health

### First Steps

1. Deploy the Hub
2. Configure N8N credentials
3. Discover your workflows
4. Trigger a test workflow
5. Set up webhooks in N8N
6. Integrate with Prime Spark agents

---

**Status**: 🟢 READY FOR DEPLOYMENT
**Version**: 1.0.0
**Built by**: Prime Spark Engineering Team
**Deployed**: 2025-11-07
**Location**: Raspberry Pi 5 @ `/home/pironman5/prime-spark-ai/n8n_integration/`

⚡ **"Orchestrate 140+ workflows with a single API call!"** ⚡
