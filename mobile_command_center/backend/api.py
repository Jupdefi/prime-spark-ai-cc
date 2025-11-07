#!/usr/bin/env python3
"""
Prime Spark Mobile Command Center - Backend API

FastAPI backend for mobile orchestration interface with:
- Agent status and control
- Infrastructure monitoring
- Task orchestration
- WebSocket real-time updates
- JWT authentication
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
import requests

# Add parent paths
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "19a44647e950489ed3e237fbc1fc1d8495d449cf863f0afa5ee27d784d9bed9a")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Service URLs
PULSE_URL = os.getenv("PULSE_URL", "http://localhost:8001")
AI_BRIDGE_URL = os.getenv("AI_BRIDGE_URL", "http://localhost:8002")

# ===== DATA MODELS =====

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class AgentStatus(BaseModel):
    agent_id: str
    name: str
    type: str
    status: str  # running, stopped, error
    health: str  # healthy, degraded, unhealthy
    uptime: int
    last_activity: str


class TaskCreate(BaseModel):
    name: str
    description: str
    agent_type: str
    requirements: List[str]
    priority: str = "medium"


class AlertAcknowledge(BaseModel):
    alert_id: str
    acknowledged_by: str


# ===== AUTHENTICATION =====

# Fake user database (in production, use real database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash(os.getenv("ADMIN_PASSWORD", "SparkAI2025!")),
        "disabled": False,
    }
}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str):
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# ===== FASTAPI APP =====

app = FastAPI(
    title="Prime Spark Mobile Command Center API",
    description="Backend API for mobile orchestration interface",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")


manager = ConnectionManager()


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh JWT token."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)."""
    return {"message": "Successfully logged out"}


# ===== AGENT ENDPOINTS =====

@app.get("/api/agents")
async def list_agents(current_user: User = Depends(get_current_user)):
    """List all Prime Spark agents."""
    agents = [
        {
            "agent_id": "pulse",
            "name": "Pulse Agent",
            "type": "monitoring",
            "status": "running",
            "health": "healthy",
            "port": 8001,
            "description": "Infrastructure heartbeat monitor"
        },
        {
            "agent_id": "ai_bridge",
            "name": "AI-Enhanced Bridge",
            "type": "integration",
            "status": "running",
            "health": "healthy",
            "port": 8002,
            "description": "Notion Bridge with AI analysis"
        },
        {
            "agent_id": "engineering_team",
            "name": "Engineering Team",
            "type": "orchestration",
            "status": "idle",
            "health": "healthy",
            "port": None,
            "description": "5-agent development team"
        }
    ]

    # Check actual status from services
    for agent in agents:
        if agent['port']:
            try:
                response = requests.get(f"http://localhost:{agent['port']}/", timeout=2)
                agent['status'] = 'running' if response.status_code == 200 else 'error'
            except:
                agent['status'] = 'stopped'
                agent['health'] = 'unhealthy'

    return {"agents": agents, "total": len(agents)}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed agent status."""
    # Map agent IDs to their endpoints
    agent_map = {
        "pulse": {"url": PULSE_URL, "endpoint": "/pulse/health"},
        "ai_bridge": {"url": AI_BRIDGE_URL, "endpoint": "/"}
    }

    if agent_id not in agent_map:
        raise HTTPException(status_code=404, detail="Agent not found")

    config = agent_map[agent_id]
    try:
        response = requests.get(f"{config['url']}{config['endpoint']}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "agent_id": agent_id,
                "status": "running",
                "health": "healthy",
                "data": data
            }
    except Exception as e:
        logger.error(f"Error fetching {agent_id}: {e}")
        return {
            "agent_id": agent_id,
            "status": "stopped",
            "health": "unhealthy",
            "error": str(e)
        }


@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Start an agent."""
    # In production, use Docker API or systemctl
    return {
        "agent_id": agent_id,
        "action": "start",
        "status": "scheduled",
        "message": f"Agent {agent_id} start scheduled"
    }


@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Stop an agent."""
    return {
        "agent_id": agent_id,
        "action": "stop",
        "status": "scheduled",
        "message": f"Agent {agent_id} stop scheduled"
    }


@app.post("/api/agents/{agent_id}/restart")
async def restart_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Restart an agent."""
    return {
        "agent_id": agent_id,
        "action": "restart",
        "status": "scheduled",
        "message": f"Agent {agent_id} restart scheduled"
    }


@app.get("/api/agents/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    lines: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get agent logs."""
    # In production, read from actual log files
    log_file = Path(f"/home/pironman5/prime-spark-ai/logs/{agent_id}.log")

    if not log_file.exists():
        return {"logs": [], "agent_id": agent_id}

    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "agent_id": agent_id,
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(recent_lines)
        }
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return {"logs": [], "agent_id": agent_id, "error": str(e)}


# ===== INFRASTRUCTURE ENDPOINTS =====

@app.get("/api/infrastructure/overview")
async def infrastructure_overview(current_user: User = Depends(get_current_user)):
    """Get infrastructure overview."""
    try:
        # Get from Pulse agent
        response = requests.get(f"{PULSE_URL}/pulse/health", timeout=5)
        if response.status_code == 200:
            pulse_data = response.json()
        else:
            pulse_data = {"status": "unavailable"}
    except:
        pulse_data = {"status": "unavailable"}

    return {
        "timestamp": datetime.now().isoformat(),
        "edge": {
            "node": "Pi 5",
            "status": "operational",
            "agents_running": 3
        },
        "cloud": {
            "primecore_nodes": 4,
            "active_nodes": 2
        },
        "pulse_data": pulse_data
    }


@app.get("/api/infrastructure/nodes")
async def list_nodes(current_user: User = Depends(get_current_user)):
    """List all infrastructure nodes."""
    try:
        response = requests.get(f"{PULSE_URL}/pulse/nodes", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    # Fallback data
    return {
        "nodes": [
            {"node_id": "edge_pi5", "type": "edge", "status": "healthy"},
            {"node_id": "primecore1", "type": "cloud", "status": "healthy"},
            {"node_id": "primecore4", "type": "cloud", "status": "healthy"}
        ]
    }


@app.get("/api/infrastructure/nodes/{node_id}")
async def get_node(node_id: str, current_user: User = Depends(get_current_user)):
    """Get node details."""
    try:
        response = requests.get(f"{PULSE_URL}/pulse/nodes/{node_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        raise HTTPException(status_code=503, detail="Pulse agent unavailable")


# ===== TASK ENDPOINTS =====

@app.get("/api/tasks")
async def list_tasks(current_user: User = Depends(get_current_user)):
    """List all tasks."""
    # Read from workspace
    workspace_dir = Path("/home/pironman5/prime-spark-ai/engineering_workspace")
    tasks = []

    if workspace_dir.exists():
        for result_file in workspace_dir.glob("project_*_results.json"):
            with open(result_file, 'r') as f:
                data = json.load(f)
                tasks.append({
                    "task_id": data['project_id'],
                    "status": data['status'],
                    "completed_at": data.get('completed_at', '')
                })

    return {"tasks": tasks, "total": len(tasks)}


@app.post("/api/tasks/create")
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    """Create and execute a new task."""
    # In production, queue task for execution
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Task queued for execution"
    }


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Get task status."""
    result_file = Path(f"/home/pironman5/prime-spark-ai/engineering_workspace/{task_id}_results.json")

    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Task not found")

    with open(result_file, 'r') as f:
        return json.load(f)


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Cancel a running task."""
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancellation requested"
    }


# ===== NOTION ENDPOINTS =====

@app.get("/api/notion/recent")
async def recent_notion_pages(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get recent Notion pages."""
    # In production, call AI Bridge or Notion Bridge
    return {
        "pages": [],
        "total": 0,
        "message": "Connect to AI Bridge for Notion data"
    }


@app.post("/api/notion/sync")
async def sync_notion(current_user: User = Depends(get_current_user)):
    """Trigger Notion sync."""
    return {
        "status": "started",
        "message": "Notion sync started"
    }


@app.post("/api/notion/search")
async def search_notion(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Search Notion content."""
    return {
        "results": [],
        "query": query
    }


# ===== LLM ENDPOINTS =====

@app.post("/api/llm/chat")
async def llm_chat(
    prompt: str,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Chat with LLM."""
    try:
        response = requests.post(
            f"{AI_BRIDGE_URL}/bridge/llm/ask",
            json={"prompt": prompt, "context": context},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass

    return {
        "response": "AI Bridge unavailable. Please ensure the AI Bridge agent is running.",
        "error": True
    }


@app.get("/api/llm/models")
async def list_llm_models(current_user: User = Depends(get_current_user)):
    """List available LLM models."""
    try:
        response = requests.get(f"{AI_BRIDGE_URL}/bridge/llm/models", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    return {"models": ["llama3.2:latest"], "source": "default"}


# ===== ALERT ENDPOINTS =====

@app.get("/api/alerts")
async def list_alerts(
    active_only: bool = True,
    current_user: User = Depends(get_current_user)
):
    """List alerts from Pulse."""
    try:
        response = requests.get(
            f"{PULSE_URL}/pulse/alerts",
            params={"active_only": active_only},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass

    return {"alerts": [], "count": 0}


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    return {
        "alert_id": alert_id,
        "acknowledged": True,
        "acknowledged_by": current_user.username,
        "acknowledged_at": datetime.now().isoformat()
    }


# ===== WEBSOCKET ENDPOINTS =====

@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket for real-time status updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send status updates every 5 seconds
            await asyncio.sleep(5)

            status_update = {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    "pulse": "running",
                    "ai_bridge": "running",
                    "engineering_team": "idle"
                }
            }

            await websocket.send_json(status_update)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket for real-time log streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # In production, tail log files and stream
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ===== ROOT ENDPOINT =====

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Prime Spark Mobile Command Center API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Prime Spark Mobile Command Center API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
