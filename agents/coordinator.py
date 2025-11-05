"""
Agent Coordination System
Manages task distribution between Control PC and Spark Agent
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import httpx


class AgentType(Enum):
    """Agent types in the system"""
    CONTROL_PC = "control_pc"
    SPARK_AGENT = "spark_agent"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Agent:
    """Agent information"""
    id: str
    type: AgentType
    ip: str
    port: int
    capabilities: List[str]
    is_online: bool = False
    current_load: int = 0
    max_load: int = 5
    last_heartbeat: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        return self.is_online and self.current_load < self.max_load

    @property
    def endpoint(self) -> str:
        """Get agent API endpoint"""
        return f"http://{self.ip}:{self.port}"


@dataclass
class Task:
    """Task to be executed by an agent"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class AgentCoordinator:
    """
    Coordinates task execution across multiple agents.

    Features:
    - Task queue with priority
    - Load balancing across agents
    - Health monitoring
    - Automatic retry and failover
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

        # Initialize default agents
        self._register_default_agents()

    def _register_default_agents(self):
        """Register default agents in the system"""
        # Control PC - Main coordinator with Hailo-8
        control_pc = Agent(
            id="control-pc-1",
            type=AgentType.CONTROL_PC,
            ip="10.8.0.2",  # VPN IP
            port=8000,
            capabilities=[
                "llm",
                "vision",
                "hailo_inference",
                "coordination",
                "memory_management"
            ],
            max_load=10
        )

        # Spark Agent - Voice and task execution
        spark_agent = Agent(
            id="spark-agent-1",
            type=AgentType.SPARK_AGENT,
            ip="10.8.0.3",  # VPN IP
            port=8000,
            capabilities=[
                "voice_recognition",
                "voice_synthesis",
                "task_execution",
                "llm"
            ],
            max_load=5
        )

        self.agents[control_pc.id] = control_pc
        self.agents[spark_agent.id] = spark_agent

    async def start(self):
        """Start the coordinator"""
        # Start worker to process task queue
        self._worker_task = asyncio.create_task(self._process_task_queue())

        # Start health check loop
        asyncio.create_task(self._health_check_loop())

    async def stop(self):
        """Stop the coordinator"""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Submit a task for execution.

        Args:
            task_type: Type of task (e.g., "voice_command", "llm_query")
            payload: Task data
            priority: Task priority

        Returns:
            Task ID
        """
        task = Task(
            type=task_type,
            payload=payload,
            priority=priority
        )

        self.tasks[task.id] = task
        await self.task_queue.put(task)

        return task.id

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get status of a task"""
        return self.tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or in-progress task"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
            task.status = TaskStatus.CANCELLED
            return True

        # TODO: Implement cancellation for in-progress tasks
        return False

    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while True:
            try:
                task = await self.task_queue.get()

                # Find suitable agent
                agent = await self._find_suitable_agent(task)

                if agent:
                    # Assign and execute task
                    await self._execute_task(task, agent)
                else:
                    # No agent available, requeue with delay
                    await asyncio.sleep(1)
                    await self.task_queue.put(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing task queue: {e}")

    async def _find_suitable_agent(self, task: Task) -> Optional[Agent]:
        """Find the best agent for a task"""
        suitable_agents = []

        for agent in self.agents.values():
            if not agent.is_available:
                continue

            # Check if agent has required capability
            if task.type in agent.capabilities or "all" in agent.capabilities:
                suitable_agents.append(agent)

        if not suitable_agents:
            return None

        # Sort by current load (least loaded first)
        suitable_agents.sort(key=lambda a: a.current_load)

        return suitable_agents[0]

    async def _execute_task(self, task: Task, agent: Agent):
        """Execute a task on an agent"""
        task.status = TaskStatus.ASSIGNED
        task.assigned_agent = agent.id
        agent.current_load += 1

        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()

            # Make API call to agent
            result = await self._call_agent(agent, task)

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()

        except Exception as e:
            task.error = str(e)

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.assigned_agent = None
                await self.task_queue.put(task)
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()

        finally:
            agent.current_load = max(0, agent.current_load - 1)

    async def _call_agent(self, agent: Agent, task: Task) -> Any:
        """Make API call to agent to execute task"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{agent.endpoint}/api/execute",
                json={
                    "task_id": task.id,
                    "type": task.type,
                    "payload": task.payload
                }
            )
            response.raise_for_status()
            return response.json()

    async def _health_check_loop(self):
        """Periodically check agent health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                for agent in self.agents.values():
                    await self._check_agent_health(agent)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health check loop: {e}")

    async def _check_agent_health(self, agent: Agent):
        """Check health of a specific agent"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{agent.endpoint}/health")

                agent.is_online = response.status_code == 200
                agent.last_heartbeat = datetime.now()

                if agent.is_online:
                    data = response.json()
                    agent.current_load = data.get("current_load", agent.current_load)

        except Exception as e:
            agent.is_online = False
            print(f"Health check failed for {agent.id}: {e}")

    async def get_coordinator_status(self) -> Dict[str, Any]:
        """Get status of the coordinator and all agents"""
        return {
            "agents": [
                {
                    "id": agent.id,
                    "type": agent.type.value,
                    "is_online": agent.is_online,
                    "is_available": agent.is_available,
                    "current_load": agent.current_load,
                    "max_load": agent.max_load,
                    "capabilities": agent.capabilities,
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                }
                for agent in self.agents.values()
            ],
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "in_progress": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                "completed": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            },
            "queue_size": self.task_queue.qsize()
        }


# Global coordinator instance
coordinator = AgentCoordinator()
