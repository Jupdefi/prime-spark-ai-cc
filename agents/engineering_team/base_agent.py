#!/usr/bin/env python3
"""
Base Agent Class for Prime Spark Engineering Team

Provides common functionality for all engineering agents including:
- Notion bridge integration
- Task management
- Communication protocols
- Memory and context
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

# Import the Notion bridge agent
import sys
sys.path.append('/home/pironman5/prime-spark-ai')
from agents.notion_bridge_agent import NotionBridgeAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all Prime Spark engineering agents.

    Provides:
    - Notion integration for coordination
    - Task management
    - Memory and context
    - Communication with other agents
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        personality: str,
        capabilities: List[str],
        notion_page_id: Optional[str] = None
    ):
        """
        Initialize a base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            role: Agent's primary role
            personality: Agent's personality/style
            capabilities: List of agent capabilities
            notion_page_id: Optional Notion page for agent workspace
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.personality = personality
        self.capabilities = capabilities
        self.notion_page_id = notion_page_id

        # Initialize Notion bridge
        self.notion = NotionBridgeAgent()

        # Agent state
        self.status = "idle"  # idle, working, completed, error
        self.current_task = None
        self.task_history = []

        # Memory
        self.context = {}
        self.memory_dir = Path(f"/home/pironman5/prime-spark-ai/memory/agents/{agent_id}")
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🤖 Agent initialized: {name} ({role})")

    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task. Must be implemented by subclasses.

        Args:
            task: Task dictionary with details

        Returns:
            Result dictionary with output and status
        """
        pass

    def update_status(self, status: str, message: Optional[str] = None):
        """
        Update agent status and optionally sync to Notion.

        Args:
            status: New status (idle, working, completed, error)
            message: Optional status message
        """
        self.status = status
        timestamp = datetime.now().isoformat()

        logger.info(f"🔄 {self.name} status: {status}")
        if message:
            logger.info(f"   └─ {message}")

        # Update Notion if page exists
        if self.notion_page_id and self.notion.is_connected():
            try:
                status_update = f"\n**[{timestamp}]** Status: {status}"
                if message:
                    status_update += f"\n{message}"

                self.notion.append_to_page(self.notion_page_id, status_update)
            except Exception as e:
                logger.warning(f"Failed to update Notion: {e}")

    def save_memory(self, key: str, value: Any):
        """
        Save information to agent's memory.

        Args:
            key: Memory key
            value: Value to store
        """
        self.context[key] = value

        # Persist to disk
        memory_file = self.memory_dir / f"{key}.json"
        with open(memory_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "key": key,
                "value": value
            }, f, indent=2)

    def recall_memory(self, key: str) -> Optional[Any]:
        """
        Recall information from agent's memory.

        Args:
            key: Memory key

        Returns:
            Stored value or None
        """
        # Try context first
        if key in self.context:
            return self.context[key]

        # Try disk
        memory_file = self.memory_dir / f"{key}.json"
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                data = json.load(f)
                self.context[key] = data['value']
                return data['value']

        return None

    def communicate(self, target_agent_id: str, message: str, data: Optional[Dict] = None):
        """
        Send a message to another agent.

        Args:
            target_agent_id: Target agent's ID
            message: Message text
            data: Optional data payload
        """
        communication = {
            "from": self.agent_id,
            "to": target_agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data or {}
        }

        # Save to shared communication log
        comm_log = Path("/home/pironman5/prime-spark-ai/memory/agent_communications.jsonl")
        with open(comm_log, 'a') as f:
            f.write(json.dumps(communication) + "\n")

        logger.info(f"📨 {self.name} → {target_agent_id}: {message}")

    def get_messages(self) -> List[Dict]:
        """
        Get messages sent to this agent.

        Returns:
            List of message dictionaries
        """
        comm_log = Path("/home/pironman5/prime-spark-ai/memory/agent_communications.jsonl")

        if not comm_log.exists():
            return []

        messages = []
        with open(comm_log, 'r') as f:
            for line in f:
                msg = json.loads(line)
                if msg['to'] == self.agent_id:
                    messages.append(msg)

        return messages

    def log_task(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        Log a completed task.

        Args:
            task: Task that was executed
            result: Task result
        """
        task_log = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "task": task,
            "result": result
        }

        self.task_history.append(task_log)

        # Save to disk
        log_file = self.memory_dir / "task_history.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(task_log) + "\n")

    def report_to_notion(self, title: str, content: str):
        """
        Create a report in Notion workspace.

        Args:
            title: Report title
            content: Report content
        """
        if not self.notion.is_connected():
            logger.warning("Notion not connected, cannot create report")
            return

        # For now, just log. In production, this would create a new Notion page
        logger.info(f"📝 Report: {title}")
        logger.info(f"   {content[:100]}...")

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.name}' status={self.status}>"
