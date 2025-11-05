"""
Prime Spark AI - Unified API
Main FastAPI application providing unified access to all system capabilities
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio

from config.settings import settings
from memory.memory_manager import memory
from routing.router import router
from routing.llm_client import llm_client
from agents.coordinator import coordinator, TaskPriority
from power.power_manager import power_manager
from vpn.manager import VPNManager
from monitoring.health_monitor import health_monitor
from auth.routes import router as auth_router

# Create FastAPI app
app = FastAPI(
    title="Prime Spark AI",
    description="Hybrid Edge-Cloud AI System API",
    version="1.0.0"
)

# Include auth routes
app.include_router(auth_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class LLMRequest(BaseModel):
    prompt: str
    model: str = "llama3.2:latest"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    use_cache: bool = True


class LLMResponse(BaseModel):
    response: str
    model: str
    location: str
    reason: str
    latency_ms: Optional[float]
    cached: bool


class TaskSubmitRequest(BaseModel):
    type: str
    payload: Dict[str, Any]
    priority: str = "normal"


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str


class MemorySetRequest(BaseModel):
    key: str
    value: Any
    persist_to_nas: bool = True
    ttl: Optional[int] = None


class MemoryGetRequest(BaseModel):
    key: str


# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    print("Starting Prime Spark AI services...")
    await coordinator.start()
    await power_manager.start()
    await health_monitor.start()
    print("All services started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    print("Shutting down Prime Spark AI services...")
    await coordinator.stop()
    await power_manager.stop()
    await health_monitor.stop()
    print("All services stopped")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "prime-spark-ai",
        "version": "1.0.0"
    }


@app.get("/api/health/detailed")
async def detailed_health():
    """Detailed health check with all subsystems"""
    return await health_monitor.get_overall_health()


# LLM endpoints
@app.post("/api/llm/generate", response_model=LLMResponse)
async def generate_llm_response(request: LLMRequest):
    """
    Generate LLM response with intelligent routing.
    Automatically routes to edge or cloud based on availability and power mode.
    """
    power_mode = await power_manager.get_routing_mode()

    result = await llm_client.generate(
        prompt=request.prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        use_cache=request.use_cache,
        power_mode=power_mode
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return LLMResponse(**result)


@app.post("/api/llm/generate/stream")
async def generate_llm_stream(request: LLMRequest):
    """
    Generate LLM response with streaming.
    Returns tokens as they're generated.
    """
    power_mode = await power_manager.get_routing_mode()

    async def generate():
        async for token in llm_client.generate_stream(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            power_mode=power_mode
        ):
            yield f"data: {token}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/llm/models")
async def list_models():
    """List available LLM models across edge and cloud"""
    return await llm_client.list_models()


# Memory endpoints
@app.post("/api/memory/set")
async def set_memory(request: MemorySetRequest):
    """Store value in memory system"""
    success = await memory.set(
        key=request.key,
        value=request.value,
        persist_to_nas=request.persist_to_nas,
        ttl=request.ttl
    )

    return {"success": success, "key": request.key}


@app.post("/api/memory/get")
async def get_memory(request: MemoryGetRequest):
    """Retrieve value from memory system"""
    value = await memory.get(request.key)

    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")

    return {"key": request.key, "value": value}


@app.delete("/api/memory/{key}")
async def delete_memory(key: str, all_tiers: bool = True):
    """Delete value from memory system"""
    success = await memory.delete(key, all_tiers=all_tiers)
    return {"success": success, "key": key}


@app.get("/api/memory/stats")
async def memory_stats():
    """Get memory system statistics"""
    return await memory.get_stats()


# Agent coordination endpoints
@app.post("/api/tasks/submit", response_model=TaskSubmitResponse)
async def submit_task(request: TaskSubmitRequest):
    """Submit a task for execution by an agent"""
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT
    }

    priority = priority_map.get(request.priority.lower(), TaskPriority.NORMAL)

    task_id = await coordinator.submit_task(
        task_type=request.type,
        payload=request.payload,
        priority=priority
    )

    return TaskSubmitResponse(task_id=task_id, status="submitted")


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    task = await coordinator.get_task_status(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "type": task.type,
        "status": task.status.value,
        "assigned_agent": task.assigned_agent,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "retry_count": task.retry_count
    }


@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a task"""
    success = await coordinator.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")

    return {"success": True, "task_id": task_id}


@app.get("/api/agents/status")
async def agents_status():
    """Get status of all agents"""
    return await coordinator.get_coordinator_status()


# Power management endpoints
@app.get("/api/power/status")
async def power_status():
    """Get current power status"""
    return await power_manager.get_power_stats()


@app.post("/api/power/mode/{mode}")
async def set_power_mode(mode: str):
    """Set power mode (auto, on-grid, off-grid)"""
    from power.power_manager import PowerMode

    try:
        power_mode = PowerMode(mode)
        await power_manager.set_mode(power_mode)
        return {"success": True, "mode": mode}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid power mode")


# VPN endpoints
@app.get("/api/vpn/status")
async def vpn_status():
    """Get VPN connection status"""
    vpn = VPNManager()
    return await vpn.get_vpn_status()


# Routing endpoints
@app.get("/api/routing/stats")
async def routing_stats():
    """Get routing statistics"""
    return await router.get_routing_stats()


# System info endpoint
@app.get("/api/system/info")
async def system_info():
    """Get system information"""
    return {
        "edge": {
            "control_pc": settings.edge.control_pc_ip,
            "spark_agent": settings.edge.spark_agent_ip,
            "nas": settings.edge.nas_ip,
        },
        "cloud": {
            "primecore1": settings.cloud.primecore1_ip,
            "primecore4": settings.cloud.primecore4_ip,
        },
        "config": {
            "routing_strategy": settings.routing.strategy,
            "power_mode": settings.power.mode,
            "vpn_enabled": True,
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_level=settings.api.log_level
    )
