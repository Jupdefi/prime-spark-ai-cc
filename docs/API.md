# Prime Spark AI - API Documentation

## Overview

Prime Spark AI provides a unified REST API for hybrid edge-cloud AI operations.

**Base URL**: `http://localhost:8000`

**Interactive Documentation**: `http://localhost:8000/docs`

## Authentication

Most endpoints require JWT authentication.

### Login

Get an access token:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "username": "admin",
    "roles": ["admin", "user"]
  }
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8000/api/endpoint
```

## Endpoints

### Health & Status

#### GET /health

Basic health check (no auth required).

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "prime-spark-ai",
  "version": "1.0.0"
}
```

#### GET /api/health/detailed

Detailed health check with all subsystems.

```bash
curl http://localhost:8000/api/health/detailed
```

Response:
```json
{
  "overall_status": "healthy",
  "components": {
    "system_resources": {
      "status": "healthy",
      "message": "Normal resource usage",
      "metrics": {
        "cpu_percent": 25.3,
        "memory_percent": 45.2,
        "disk_percent": 60.1
      }
    },
    "vpn": { ... },
    "memory_tiers": { ... },
    "routing": { ... },
    "agents": { ... },
    "power": { ... }
  }
}
```

### LLM Operations

#### POST /api/llm/generate

Generate LLM response with intelligent routing.

```bash
curl -X POST http://localhost:8000/api/llm/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "model": "llama3.2:latest",
    "temperature": 0.7,
    "use_cache": true
  }'
```

Response:
```json
{
  "response": "Quantum computing is...",
  "model": "llama3.2:latest",
  "location": "edge_local",
  "reason": "Edge available and healthy",
  "latency_ms": 125.5,
  "cached": false
}
```

#### POST /api/llm/generate/stream

Stream LLM response for real-time output.

```bash
curl -X POST http://localhost:8000/api/llm/generate/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Write a haiku about AI",
    "model": "llama3.2:latest"
  }'
```

Response (Server-Sent Events):
```
data: Silicon
data:  minds
data:  think
data: ...
```

#### GET /api/llm/models

List available models across edge and cloud.

```bash
curl http://localhost:8000/api/llm/models
```

Response:
```json
{
  "edge": {
    "models": ["llama3.2:latest", "mistral:latest"],
    "endpoint": "http://localhost:11434"
  },
  "cloud": {
    "models": ["llama3.2:latest", "codellama:latest"],
    "endpoint": "http://69.62.123.97:11434"
  }
}
```

### Memory Operations

#### POST /api/memory/set

Store value in memory system.

```bash
curl -X POST http://localhost:8000/api/memory/set \
  -H 'Content-Type: application/json' \
  -d '{
    "key": "user_preferences",
    "value": {"theme": "dark", "language": "en"},
    "persist_to_nas": true,
    "ttl": 3600
  }'
```

Response:
```json
{
  "success": true,
  "key": "user_preferences"
}
```

#### POST /api/memory/get

Retrieve value from memory.

```bash
curl -X POST http://localhost:8000/api/memory/get \
  -H 'Content-Type: application/json' \
  -d '{"key": "user_preferences"}'
```

Response:
```json
{
  "key": "user_preferences",
  "value": {"theme": "dark", "language": "en"}
}
```

#### DELETE /api/memory/{key}

Delete value from memory.

```bash
curl -X DELETE http://localhost:8000/api/memory/user_preferences?all_tiers=true
```

Response:
```json
{
  "success": true,
  "key": "user_preferences"
}
```

#### GET /api/memory/stats

Get memory system statistics.

```bash
curl http://localhost:8000/api/memory/stats
```

Response:
```json
{
  "tier1_local_cache": {
    "total_keys": 1523,
    "hits": 45231,
    "misses": 3421,
    "memory_used_mb": 256.5
  },
  "tier2_nas_storage": { ... },
  "tier3_cloud_storage": { ... }
}
```

### Agent Operations

#### POST /api/tasks/submit

Submit a task for agent execution.

```bash
curl -X POST http://localhost:8000/api/tasks/submit \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "voice_command",
    "payload": {
      "command": "play music",
      "user_id": "user123"
    },
    "priority": "normal"
  }'
```

Response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "submitted"
}
```

#### GET /api/tasks/{task_id}

Get task status.

```bash
curl http://localhost:8000/api/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "voice_command",
  "status": "completed",
  "assigned_agent": "spark-agent-1",
  "result": {"success": true, "action": "music_playing"},
  "created_at": "2025-01-15T10:30:00",
  "completed_at": "2025-01-15T10:30:02"
}
```

#### DELETE /api/tasks/{task_id}

Cancel a task.

```bash
curl -X DELETE http://localhost:8000/api/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### GET /api/agents/status

Get status of all agents.

```bash
curl http://localhost:8000/api/agents/status
```

Response:
```json
{
  "agents": [
    {
      "id": "control-pc-1",
      "type": "control_pc",
      "is_online": true,
      "is_available": true,
      "current_load": 3,
      "max_load": 10,
      "capabilities": ["llm", "vision", "hailo_inference"]
    },
    {
      "id": "spark-agent-1",
      "type": "spark_agent",
      "is_online": true,
      "current_load": 1,
      "capabilities": ["voice_recognition", "task_execution"]
    }
  ],
  "tasks": {
    "total": 1234,
    "pending": 5,
    "in_progress": 3,
    "completed": 1220,
    "failed": 6
  }
}
```

### Power Management

#### GET /api/power/status

Get current power status.

```bash
curl http://localhost:8000/api/power/status
```

Response:
```json
{
  "mode": "auto",
  "is_on_battery": false,
  "battery_percent": 85.0,
  "battery_state": "high",
  "time_remaining_minutes": null,
  "power_plugged": true,
  "edge_only_mode": false,
  "routing_mode": "on-grid"
}
```

#### POST /api/power/mode/{mode}

Set power mode.

```bash
curl -X POST http://localhost:8000/api/power/mode/off-grid
```

Response:
```json
{
  "success": true,
  "mode": "off-grid"
}
```

### VPN Management

#### GET /api/vpn/status

Get VPN connection status.

```bash
curl http://localhost:8000/api/vpn/status
```

Response:
```json
{
  "interface": "wg0",
  "is_active": true,
  "total_peers": 6,
  "connected_peers": 5,
  "peers": [
    {
      "name": "spark-agent",
      "ip": "10.8.0.3",
      "is_connected": true,
      "latest_handshake": "2025-01-15T10:28:45",
      "transfer_rx_mb": 125.3,
      "transfer_tx_mb": 89.7
    }
  ]
}
```

### Routing

#### GET /api/routing/stats

Get routing statistics.

```bash
curl http://localhost:8000/api/routing/stats
```

Response:
```json
{
  "strategy": "edge-first",
  "endpoints": {
    "edge_local": {
      "endpoint": "http://localhost:11434",
      "is_healthy": true,
      "latency_ms": 12.5
    },
    "cloud_core4": {
      "endpoint": "http://69.62.123.97:11434",
      "is_healthy": true,
      "latency_ms": 45.2
    }
  }
}
```

### System Information

#### GET /api/system/info

Get system configuration.

```bash
curl http://localhost:8000/api/system/info
```

Response:
```json
{
  "edge": {
    "control_pc": "192.168.1.100",
    "spark_agent": "192.168.1.92",
    "nas": "192.168.1.49"
  },
  "cloud": {
    "primecore1": "141.136.35.51",
    "primecore4": "69.62.123.97"
  },
  "config": {
    "routing_strategy": "edge-first",
    "power_mode": "auto",
    "vpn_enabled": true
  }
}
```

## Example Workflows

### Complete LLM Workflow

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your_password"}' \
  | jq -r '.access_token')

# 2. Check system health
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/health/detailed

# 3. List available models
curl http://localhost:8000/api/llm/models

# 4. Generate response
curl -X POST http://localhost:8000/api/llm/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Explain edge computing",
    "model": "llama3.2:latest"
  }'
```

### Task Submission Workflow

```bash
# 1. Submit task
TASK_ID=$(curl -X POST http://localhost:8000/api/tasks/submit \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "data_processing",
    "payload": {"data": "..."},
    "priority": "high"
  }' | jq -r '.task_id')

# 2. Check task status
curl http://localhost:8000/api/tasks/$TASK_ID

# 3. Wait for completion (poll)
while true; do
  STATUS=$(curl -s http://localhost:8000/api/tasks/$TASK_ID | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    break
  fi
  sleep 1
done

# 4. Get result
curl http://localhost:8000/api/tasks/$TASK_ID | jq '.result'
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Add rate limiting middleware for production use.

## WebSocket Support

Real-time updates can be added via WebSocket endpoints. This is a future enhancement.

## API Versioning

Current version: v1.0.0

Future versions will be accessible via `/api/v2/` prefix.
