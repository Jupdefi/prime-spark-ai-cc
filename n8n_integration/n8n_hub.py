#!/usr/bin/env python3
"""
Prime Spark N8N Integration Hub

Bidirectional integration between Prime Spark agents and 140+ N8N workflows.
Provides workflow discovery, triggering, monitoring, and webhook handling.

Author: Prime Spark Engineering Team
Version: 1.0.0
"""

import os
import json
import hashlib
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import redis
import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import hmac
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================

class Config:
    """N8N Integration Hub Configuration"""

    # N8N Configuration
    N8N_API_URL = os.getenv("N8N_API_URL", "https://n8n.example.com/api/v1")
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://n8n.example.com/webhook")
    N8N_API_KEY = os.getenv("N8N_API_KEY", "")
    N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "your-webhook-secret")

    # Prime Spark Agents
    PULSE_API_URL = os.getenv("PULSE_API_URL", "http://localhost:8001")
    AI_BRIDGE_API_URL = os.getenv("AI_BRIDGE_API_URL", "http://localhost:8002")
    MOBILE_API_URL = os.getenv("MOBILE_API_URL", "http://localhost:8003")

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 3))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # Hub Configuration
    HUB_API_KEY = os.getenv("HUB_API_KEY", "prime-spark-n8n-key")
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1 hour
    MAX_CONCURRENT_WORKFLOWS = int(os.getenv("MAX_CONCURRENT_WORKFLOWS", 10))
    WORKFLOW_TIMEOUT = int(os.getenv("WORKFLOW_TIMEOUT", 60))  # seconds

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 100))


config = Config()

# ==================== Models ====================

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowCategory(str, Enum):
    """Workflow categories"""
    MONITORING = "monitoring"
    ALERTS = "alerts"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"
    AUTOMATION = "automation"
    OTHER = "other"


class Workflow(BaseModel):
    """N8N Workflow Model"""
    id: str
    name: str
    active: bool
    tags: List[str] = []
    category: WorkflowCategory = WorkflowCategory.OTHER
    description: Optional[str] = None
    trigger_type: str = "webhook"
    webhook_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkflowExecution(BaseModel):
    """Workflow Execution Model"""
    id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration: Optional[float] = None
    triggered_by: str
    agent_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TriggerWorkflowRequest(BaseModel):
    """Request to trigger a workflow"""
    workflow_id: str
    data: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    priority: str = "normal"
    async_execution: bool = True


class TriggerBatchRequest(BaseModel):
    """Request to trigger multiple workflows"""
    workflows: List[TriggerWorkflowRequest]
    sequential: bool = False
    stop_on_error: bool = False


class WebhookPayload(BaseModel):
    """Webhook payload from N8N"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime


class WorkflowTemplate(BaseModel):
    """Workflow template for common patterns"""
    name: str
    description: str
    workflow_ids: List[str]
    parameters: Dict[str, Any]
    category: WorkflowCategory


# ==================== N8N Integration Hub ====================

class N8NIntegrationHub:
    """
    N8N Integration Hub

    Manages bidirectional communication between Prime Spark and N8N:
    - Discover and catalog N8N workflows
    - Trigger workflow executions
    - Handle N8N webhooks
    - Monitor execution status
    - Cache workflow metadata
    """

    def __init__(self):
        """Initialize N8N Integration Hub"""
        self.config = config

        # Redis connection
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD,
            decode_responses=True
        )

        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connected")
        except redis.ConnectionError:
            logger.warning("⚠️ Redis unavailable - caching disabled")
            self.redis_client = None

        # Active executions tracking
        self.active_executions: Dict[str, WorkflowExecution] = {}

        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []

        logger.info("🔗 N8N Integration Hub initialized")

    # ==================== Caching ====================

    def _cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        key_str = "|".join(str(arg) for arg in args)
        return f"n8n:hub:{hashlib.md5(key_str.encode()).hexdigest()}"

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.redis_client:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    def _set_cached(self, key: str, value: Any, ttl: int = None):
        """Set cached value"""
        if not self.redis_client:
            return

        try:
            ttl = ttl or config.CACHE_TTL
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def _invalidate_cache(self, pattern: str = "n8n:hub:*"):
        """Invalidate cache by pattern"""
        if not self.redis_client:
            return

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")

    # ==================== N8N API Client ====================

    def _n8n_headers(self) -> Dict[str, str]:
        """Get N8N API headers"""
        return {
            "X-N8N-API-KEY": config.N8N_API_KEY,
            "Content-Type": "application/json"
        }

    async def discover_workflows(self, refresh: bool = False) -> List[Workflow]:
        """
        Discover all N8N workflows

        Args:
            refresh: Force refresh from N8N API

        Returns:
            List of discovered workflows
        """
        cache_key = self._cache_key("workflows", "all")

        if not refresh:
            cached = self._get_cached(cache_key)
            if cached:
                logger.info(f"📦 Returning {len(cached)} workflows from cache")
                return [Workflow(**w) for w in cached]

        logger.info("🔍 Discovering N8N workflows...")

        try:
            # Call N8N API to list workflows
            response = requests.get(
                f"{config.N8N_API_URL}/workflows",
                headers=self._n8n_headers(),
                timeout=10
            )
            response.raise_for_status()

            workflows_data = response.json()
            workflows = []

            for wf_data in workflows_data.get("data", []):
                # Extract workflow metadata
                workflow = Workflow(
                    id=wf_data["id"],
                    name=wf_data["name"],
                    active=wf_data.get("active", False),
                    tags=wf_data.get("tags", []),
                    category=self._categorize_workflow(wf_data),
                    description=wf_data.get("description"),
                    trigger_type=self._get_trigger_type(wf_data),
                    webhook_url=self._get_webhook_url(wf_data),
                    created_at=wf_data.get("createdAt"),
                    updated_at=wf_data.get("updatedAt")
                )
                workflows.append(workflow)

            # Cache workflows
            self._set_cached(cache_key, [w.dict() for w in workflows])

            logger.info(f"✅ Discovered {len(workflows)} workflows")
            return workflows

        except requests.RequestException as e:
            logger.error(f"❌ Failed to discover workflows: {e}")
            raise HTTPException(status_code=503, detail=f"N8N API error: {str(e)}")

    def _categorize_workflow(self, workflow_data: Dict) -> WorkflowCategory:
        """Categorize workflow based on name and tags"""
        name = workflow_data.get("name", "").lower()
        tags = [t.lower() for t in workflow_data.get("tags", [])]

        if any(k in name or k in tags for k in ["monitor", "health", "check"]):
            return WorkflowCategory.MONITORING
        elif any(k in name or k in tags for k in ["alert", "notification", "warn"]):
            return WorkflowCategory.ALERTS
        elif any(k in name or k in tags for k in ["deploy", "release", "ci", "cd"]):
            return WorkflowCategory.DEPLOYMENT
        elif any(k in name or k in tags for k in ["analyze", "analysis", "insight"]):
            return WorkflowCategory.ANALYSIS
        elif any(k in name or k in tags for k in ["doc", "documentation", "readme"]):
            return WorkflowCategory.DOCUMENTATION
        elif any(k in name or k in tags for k in ["integrate", "integration", "connect"]):
            return WorkflowCategory.INTEGRATION
        elif any(k in name or k in tags for k in ["automate", "automation", "schedule"]):
            return WorkflowCategory.AUTOMATION
        else:
            return WorkflowCategory.OTHER

    def _get_trigger_type(self, workflow_data: Dict) -> str:
        """Extract trigger type from workflow"""
        nodes = workflow_data.get("nodes", [])
        for node in nodes:
            if node.get("type") == "n8n-nodes-base.webhook":
                return "webhook"
            elif node.get("type") == "n8n-nodes-base.cron":
                return "schedule"
            elif node.get("type") == "n8n-nodes-base.start":
                return "manual"
        return "unknown"

    def _get_webhook_url(self, workflow_data: Dict) -> Optional[str]:
        """Extract webhook URL from workflow"""
        nodes = workflow_data.get("nodes", [])
        for node in nodes:
            if node.get("type") == "n8n-nodes-base.webhook":
                webhook_path = node.get("parameters", {}).get("path", "")
                if webhook_path:
                    return f"{config.N8N_WEBHOOK_URL}/{webhook_path}"
        return None

    async def get_workflow(self, workflow_id: str) -> Workflow:
        """Get single workflow by ID"""
        cache_key = self._cache_key("workflow", workflow_id)

        cached = self._get_cached(cache_key)
        if cached:
            return Workflow(**cached)

        try:
            response = requests.get(
                f"{config.N8N_API_URL}/workflows/{workflow_id}",
                headers=self._n8n_headers(),
                timeout=5
            )
            response.raise_for_status()

            wf_data = response.json()
            workflow = Workflow(
                id=wf_data["id"],
                name=wf_data["name"],
                active=wf_data.get("active", False),
                tags=wf_data.get("tags", []),
                category=self._categorize_workflow(wf_data),
                description=wf_data.get("description"),
                trigger_type=self._get_trigger_type(wf_data),
                webhook_url=self._get_webhook_url(wf_data)
            )

            self._set_cached(cache_key, workflow.dict())
            return workflow

        except requests.RequestException as e:
            logger.error(f"❌ Failed to get workflow {workflow_id}: {e}")
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    # ==================== Workflow Execution ====================

    async def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        priority: str = "normal"
    ) -> WorkflowExecution:
        """
        Trigger N8N workflow execution

        Args:
            workflow_id: N8N workflow ID
            data: Input data for workflow
            agent_id: Prime Spark agent triggering the workflow
            priority: Execution priority (low, normal, high, critical)

        Returns:
            WorkflowExecution object
        """
        logger.info(f"🚀 Triggering workflow {workflow_id} (priority: {priority})")

        # Check concurrent execution limit
        if len(self.active_executions) >= config.MAX_CONCURRENT_WORKFLOWS:
            raise HTTPException(
                status_code=429,
                detail=f"Max concurrent workflows ({config.MAX_CONCURRENT_WORKFLOWS}) reached"
            )

        # Get workflow details
        workflow = await self.get_workflow(workflow_id)

        if not workflow.active:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow {workflow_id} is not active"
            )

        # Create execution record
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{workflow_id[:8]}"

        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            status=WorkflowStatus.PENDING,
            started_at=datetime.now(),
            triggered_by=agent_id or "manual",
            agent_id=agent_id,
            input_data=data
        )

        self.active_executions[execution_id] = execution

        # Execute workflow
        try:
            if workflow.webhook_url:
                # Trigger via webhook
                execution.status = WorkflowStatus.RUNNING
                await self._broadcast_execution_update(execution)

                response = requests.post(
                    workflow.webhook_url,
                    json=data or {},
                    timeout=config.WORKFLOW_TIMEOUT
                )
                response.raise_for_status()

                execution.status = WorkflowStatus.SUCCESS
                execution.output_data = response.json()

            else:
                # Trigger via N8N API
                execution.status = WorkflowStatus.RUNNING
                await self._broadcast_execution_update(execution)

                response = requests.post(
                    f"{config.N8N_API_URL}/workflows/{workflow_id}/execute",
                    headers=self._n8n_headers(),
                    json={"data": data or {}},
                    timeout=config.WORKFLOW_TIMEOUT
                )
                response.raise_for_status()

                execution.status = WorkflowStatus.SUCCESS
                execution.output_data = response.json()

            execution.finished_at = datetime.now()
            execution.duration = (execution.finished_at - execution.started_at).total_seconds()

            logger.info(f"✅ Workflow {workflow_id} completed in {execution.duration:.2f}s")

        except requests.Timeout:
            execution.status = WorkflowStatus.TIMEOUT
            execution.error = f"Workflow execution timed out after {config.WORKFLOW_TIMEOUT}s"
            logger.error(f"⏱️ Workflow {workflow_id} timed out")

        except requests.RequestException as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            logger.error(f"❌ Workflow {workflow_id} failed: {e}")

        finally:
            execution.finished_at = execution.finished_at or datetime.now()
            execution.duration = (execution.finished_at - execution.started_at).total_seconds()

            # Broadcast final status
            await self._broadcast_execution_update(execution)

            # Store execution history
            self._store_execution(execution)

        return execution

    async def trigger_batch(
        self,
        workflows: List[TriggerWorkflowRequest],
        sequential: bool = False,
        stop_on_error: bool = False
    ) -> List[WorkflowExecution]:
        """
        Trigger multiple workflows

        Args:
            workflows: List of workflows to trigger
            sequential: Execute workflows sequentially (default: parallel)
            stop_on_error: Stop batch on first error (sequential only)

        Returns:
            List of WorkflowExecution objects
        """
        logger.info(f"🔄 Triggering batch of {len(workflows)} workflows (sequential={sequential})")

        executions = []

        if sequential:
            # Execute workflows one by one
            for wf_req in workflows:
                try:
                    execution = await self.trigger_workflow(
                        workflow_id=wf_req.workflow_id,
                        data=wf_req.data,
                        agent_id=wf_req.agent_id,
                        priority=wf_req.priority
                    )
                    executions.append(execution)

                    if stop_on_error and execution.status == WorkflowStatus.FAILED:
                        logger.warning(f"⚠️ Stopping batch - workflow {wf_req.workflow_id} failed")
                        break

                except Exception as e:
                    logger.error(f"❌ Batch execution error: {e}")
                    if stop_on_error:
                        break
        else:
            # Execute workflows in parallel
            tasks = [
                self.trigger_workflow(
                    workflow_id=wf_req.workflow_id,
                    data=wf_req.data,
                    agent_id=wf_req.agent_id,
                    priority=wf_req.priority
                )
                for wf_req in workflows
            ]

            executions = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            executions = [e for e in executions if isinstance(e, WorkflowExecution)]

        logger.info(f"✅ Batch completed: {len(executions)} executions")
        return executions

    async def cancel_execution(self, execution_id: str) -> WorkflowExecution:
        """Cancel running workflow execution"""
        if execution_id not in self.active_executions:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        execution = self.active_executions[execution_id]

        if execution.status in [WorkflowStatus.SUCCESS, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail=f"Execution {execution_id} already completed")

        execution.status = WorkflowStatus.CANCELLED
        execution.finished_at = datetime.now()
        execution.duration = (execution.finished_at - execution.started_at).total_seconds()

        await self._broadcast_execution_update(execution)

        logger.info(f"🛑 Cancelled execution {execution_id}")
        return execution

    def _store_execution(self, execution: WorkflowExecution):
        """Store execution in history"""
        history_key = f"n8n:execution:{execution.id}"
        self._set_cached(history_key, execution.dict(), ttl=86400)  # 24 hours

        # Add to execution list
        list_key = "n8n:executions:list"
        if self.redis_client:
            try:
                self.redis_client.lpush(list_key, execution.id)
                self.redis_client.ltrim(list_key, 0, 999)  # Keep last 1000
            except Exception as e:
                logger.warning(f"Failed to store execution: {e}")

    async def get_execution(self, execution_id: str) -> WorkflowExecution:
        """Get execution by ID"""
        # Check active executions first
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]

        # Check history
        history_key = f"n8n:execution:{execution_id}"
        cached = self._get_cached(history_key)

        if cached:
            return WorkflowExecution(**cached)

        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters"""
        executions = []

        # Get from active executions
        for execution in self.active_executions.values():
            if workflow_id and execution.workflow_id != workflow_id:
                continue
            if status and execution.status != status:
                continue
            executions.append(execution)

        # Get from history
        list_key = "n8n:executions:list"
        if self.redis_client:
            try:
                execution_ids = self.redis_client.lrange(list_key, 0, limit - 1)
                for exec_id in execution_ids:
                    if len(executions) >= limit:
                        break

                    history_key = f"n8n:execution:{exec_id}"
                    cached = self._get_cached(history_key)
                    if cached:
                        execution = WorkflowExecution(**cached)
                        if workflow_id and execution.workflow_id != workflow_id:
                            continue
                        if status and execution.status != status:
                            continue
                        executions.append(execution)
            except Exception as e:
                logger.warning(f"Failed to list executions: {e}")

        return executions[:limit]

    # ==================== Webhooks ====================

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify HMAC signature from N8N webhook"""
        expected = hmac.new(
            config.N8N_WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    async def handle_webhook(self, agent_id: str, payload: WebhookPayload) -> Dict[str, Any]:
        """
        Handle incoming webhook from N8N

        Args:
            agent_id: Prime Spark agent ID receiving the webhook
            payload: Webhook payload

        Returns:
            Response data
        """
        logger.info(f"📨 Webhook received for agent {agent_id}: {payload.workflow_name}")

        # Update execution status if we're tracking it
        if payload.execution_id in self.active_executions:
            execution = self.active_executions[payload.execution_id]
            execution.status = payload.status
            execution.output_data = payload.data
            execution.error = payload.error
            execution.finished_at = payload.timestamp
            execution.duration = (execution.finished_at - execution.started_at).total_seconds()

            await self._broadcast_execution_update(execution)
            self._store_execution(execution)

        # Route webhook to appropriate agent
        if agent_id == "pulse":
            return await self._handle_pulse_webhook(payload)
        elif agent_id == "ai-bridge":
            return await self._handle_ai_bridge_webhook(payload)
        elif agent_id == "engineering-team":
            return await self._handle_engineering_webhook(payload)
        else:
            logger.warning(f"⚠️ Unknown agent ID: {agent_id}")
            return {"status": "received", "agent": agent_id}

    async def _handle_pulse_webhook(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Handle webhook for Pulse agent"""
        try:
            # Forward to Pulse agent
            response = requests.post(
                f"{config.PULSE_API_URL}/webhook/n8n",
                json=payload.dict(),
                timeout=5
            )
            return {"status": "forwarded_to_pulse", "response": response.json()}
        except Exception as e:
            logger.error(f"Failed to forward to Pulse: {e}")
            return {"status": "error", "error": str(e)}

    async def _handle_ai_bridge_webhook(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Handle webhook for AI Bridge agent"""
        try:
            # Forward to AI Bridge
            response = requests.post(
                f"{config.AI_BRIDGE_API_URL}/webhook/n8n",
                json=payload.dict(),
                timeout=5
            )
            return {"status": "forwarded_to_ai_bridge", "response": response.json()}
        except Exception as e:
            logger.error(f"Failed to forward to AI Bridge: {e}")
            return {"status": "error", "error": str(e)}

    async def _handle_engineering_webhook(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Handle webhook for Engineering Team"""
        # Engineering Team doesn't have HTTP API, so just log it
        logger.info(f"📝 Engineering Team webhook: {payload.workflow_name}")
        return {"status": "logged", "agent": "engineering-team"}

    # ==================== WebSocket Broadcasting ====================

    async def _broadcast_execution_update(self, execution: WorkflowExecution):
        """Broadcast execution update to all connected WebSocket clients"""
        if not self.websocket_connections:
            return

        message = {
            "type": "execution_update",
            "data": execution.dict()
        }

        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for real-time updates"""
        await websocket.accept()
        self.websocket_connections.append(websocket)

        logger.info(f"📡 WebSocket connected (total: {len(self.websocket_connections)})")

        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.websocket_connections.remove(websocket)
            logger.info(f"📡 WebSocket disconnected (remaining: {len(self.websocket_connections)})")

    # ==================== Health & Metrics ====================

    async def health_check(self) -> Dict[str, Any]:
        """Health check for N8N Integration Hub"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "redis": "connected" if self.redis_client else "disconnected",
            "active_executions": len(self.active_executions),
            "websocket_connections": len(self.websocket_connections),
            "n8n_reachable": False
        }

        # Check N8N connectivity
        try:
            response = requests.get(
                f"{config.N8N_API_URL}/workflows",
                headers=self._n8n_headers(),
                timeout=5
            )
            health["n8n_reachable"] = response.status_code == 200
        except:
            pass

        if not health["n8n_reachable"]:
            health["status"] = "degraded"

        return health

    async def get_metrics(self) -> Dict[str, Any]:
        """Get N8N integration metrics"""
        # Count executions by status
        status_counts = {}
        for status in WorkflowStatus:
            status_counts[status.value] = 0

        for execution in self.active_executions.values():
            status_counts[execution.status.value] += 1

        # Get execution history stats
        list_key = "n8n:executions:list"
        total_executions = 0
        if self.redis_client:
            try:
                total_executions = self.redis_client.llen(list_key)
            except:
                pass

        return {
            "active_executions": len(self.active_executions),
            "total_executions": total_executions,
            "status_distribution": status_counts,
            "websocket_connections": len(self.websocket_connections),
            "cache_enabled": self.redis_client is not None,
            "max_concurrent": config.MAX_CONCURRENT_WORKFLOWS
        }


# ==================== FastAPI Application ====================

app = FastAPI(
    title="Prime Spark N8N Integration Hub",
    description="Bidirectional integration between Prime Spark agents and N8N workflows",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key"""
    if api_key != config.HUB_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Initialize hub
hub = N8NIntegrationHub()

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Prime Spark N8N Integration Hub",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return await hub.health_check()

@app.get("/metrics")
async def metrics():
    """Metrics endpoint"""
    return await hub.get_metrics()

# ==================== Workflow Discovery ====================

@app.get("/api/n8n/workflows", response_model=List[Workflow])
async def list_workflows(
    refresh: bool = False,
    category: Optional[WorkflowCategory] = None,
    api_key: str = Depends(verify_api_key)
):
    """List all N8N workflows"""
    workflows = await hub.discover_workflows(refresh=refresh)

    if category:
        workflows = [w for w in workflows if w.category == category]

    return workflows

@app.get("/api/n8n/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get single workflow by ID"""
    return await hub.get_workflow(workflow_id)

@app.get("/api/n8n/workflows/search")
async def search_workflows(
    q: str,
    api_key: str = Depends(verify_api_key)
):
    """Search workflows by name or tags"""
    workflows = await hub.discover_workflows()

    q_lower = q.lower()
    matches = [
        w for w in workflows
        if q_lower in w.name.lower() or
        any(q_lower in tag.lower() for tag in w.tags)
    ]

    return matches

@app.get("/api/n8n/workflows/categories")
async def list_categories(api_key: str = Depends(verify_api_key)):
    """List workflow categories with counts"""
    workflows = await hub.discover_workflows()

    categories = {}
    for category in WorkflowCategory:
        count = len([w for w in workflows if w.category == category])
        categories[category.value] = count

    return categories

# ==================== Workflow Execution ====================

@app.post("/api/n8n/execute/{workflow_id}", response_model=WorkflowExecution)
async def trigger_workflow(
    workflow_id: str,
    request: TriggerWorkflowRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Trigger workflow execution"""
    if request.async_execution:
        # Execute in background
        background_tasks.add_task(
            hub.trigger_workflow,
            workflow_id=workflow_id,
            data=request.data,
            agent_id=request.agent_id,
            priority=request.priority
        )

        return {
            "id": f"async_{workflow_id}",
            "workflow_id": workflow_id,
            "workflow_name": "Async Execution",
            "status": WorkflowStatus.PENDING,
            "started_at": datetime.now(),
            "triggered_by": request.agent_id or "manual",
            "agent_id": request.agent_id,
            "input_data": request.data
        }
    else:
        # Execute synchronously
        return await hub.trigger_workflow(
            workflow_id=workflow_id,
            data=request.data,
            agent_id=request.agent_id,
            priority=request.priority
        )

@app.post("/api/n8n/execute/batch", response_model=List[WorkflowExecution])
async def trigger_batch(
    request: TriggerBatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger multiple workflows"""
    return await hub.trigger_batch(
        workflows=request.workflows,
        sequential=request.sequential,
        stop_on_error=request.stop_on_error
    )

@app.get("/api/n8n/execute/status/{execution_id}", response_model=WorkflowExecution)
async def get_execution_status(
    execution_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get execution status"""
    return await hub.get_execution(execution_id)

@app.post("/api/n8n/execute/cancel/{execution_id}", response_model=WorkflowExecution)
async def cancel_execution(
    execution_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Cancel running execution"""
    return await hub.cancel_execution(execution_id)

# ==================== Executions ====================

@app.get("/api/n8n/executions", response_model=List[WorkflowExecution])
async def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[WorkflowStatus] = None,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """List workflow executions"""
    return await hub.list_executions(
        workflow_id=workflow_id,
        status=status,
        limit=limit
    )

@app.get("/api/n8n/executions/{execution_id}", response_model=WorkflowExecution)
async def get_execution(
    execution_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get execution details"""
    return await hub.get_execution(execution_id)

@app.get("/api/n8n/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get execution logs"""
    execution = await hub.get_execution(execution_id)

    return {
        "execution_id": execution_id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "logs": [
            {
                "timestamp": execution.started_at,
                "level": "INFO",
                "message": f"Execution started by {execution.triggered_by}"
            },
            {
                "timestamp": execution.finished_at or datetime.now(),
                "level": "INFO" if execution.status == WorkflowStatus.SUCCESS else "ERROR",
                "message": f"Execution {execution.status.value}"
            }
        ]
    }

# ==================== Webhooks ====================

@app.post("/webhook/n8n/{agent_id}")
async def webhook_handler(
    agent_id: str,
    payload: WebhookPayload,
    x_n8n_signature: Optional[str] = None
):
    """
    Webhook endpoint for N8N callbacks

    Receives callbacks from N8N workflows and routes them to appropriate agents
    """
    # Verify signature if provided
    if x_n8n_signature and config.N8N_WEBHOOK_SECRET:
        payload_str = json.dumps(payload.dict(), default=str)
        if not hub.verify_webhook_signature(payload_str, x_n8n_signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    return await hub.handle_webhook(agent_id, payload)

# ==================== WebSocket ====================

@app.websocket("/ws/n8n/executions")
async def websocket_executions(websocket: WebSocket):
    """WebSocket endpoint for real-time execution updates"""
    await hub.handle_websocket(websocket)

@app.websocket("/ws/n8n/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for hub status updates"""
    await websocket.accept()

    try:
        while True:
            status = await hub.health_check()
            await websocket.send_json(status)
            await asyncio.sleep(10)  # Update every 10 seconds
    except WebSocketDisconnect:
        pass


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )
