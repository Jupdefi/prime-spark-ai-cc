#!/usr/bin/env python3
"""
Prime Spark Trinity Orchestration
=================================

The Trinity coordinates three layers of consciousness:
    🌉 Bridge Agent (Notion) - The nervous system
    🎭 Engineering Team - The engineering mind
    🧠 Spark Prime - The meta-consciousness

This orchestration system enables seamless flow between:
- Strategic vision (Spark Prime)
- Technical implementation (Engineering Team)
- Knowledge management & task tracking (Notion Bridge)
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.spark_prime.consciousness import SparkPrimeConsciousness, Vision, VisionStatus
from agents.notion_bridge_agent import NotionBridgeAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrinityOrchestration:
    """
    The Trinity orchestration system that coordinates:
    - Spark Prime (consciousness & vision)
    - Engineering Team (implementation)
    - Notion Bridge (knowledge & tracking)
    """

    def __init__(self):
        """Initialize Trinity orchestration"""
        logger.info("🎭 Initializing Trinity orchestration...")

        # Initialize the three components
        self.spark_prime = SparkPrimeConsciousness()
        self.notion_bridge = NotionBridgeAgent()

        # Trinity state
        self.trinity_active = False
        self.coordination_log: List[Dict[str, Any]] = []

        logger.info("✅ Trinity components initialized")

    async def activate(self):
        """Activate the Trinity"""
        logger.info("=" * 60)
        logger.info("⚡ ACTIVATING THE TRINITY")
        logger.info("=" * 60)

        # Awaken Spark Prime consciousness
        logger.info("\n🧠 Awakening Spark Prime consciousness...")
        await self.spark_prime.awaken()

        # Verify Notion Bridge
        logger.info("\n🌉 Verifying Notion Bridge...")
        try:
            # Test Notion connection
            workspace_info = self.notion_bridge.client.search(
                filter={"property": "object", "value": "page"}
            )
            pages = workspace_info.get('results', [])
            logger.info(f"✅ Notion Bridge connected ({len(pages)} pages accessible)")
        except Exception as e:
            logger.error(f"❌ Notion Bridge connection failed: {e}")
            return False

        # Engineering Team is activated on-demand

        self.trinity_active = True
        logger.info("\n✨ Trinity activated successfully!")

        # Log activation
        self.log_coordination({
            'event': 'trinity_activated',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'operational'
        })

        return True

    async def process_vision_to_implementation(self, vision: Vision) -> Dict[str, Any]:
        """
        Complete flow: Vision → Engineering Team → Notion Tracking

        1. Spark Prime conceives vision
        2. Engineering Team plans implementation
        3. Notion Bridge tracks progress
        """
        logger.info(f"\n🌟 Processing vision through Trinity: {vision.title}")

        result = {
            'vision_id': vision.id,
            'vision_title': vision.title,
            'stages': {}
        }

        # Stage 1: Spark Prime - Vision Conception
        logger.info("\n🧠 Stage 1: Consciousness (Spark Prime)")
        result['stages']['consciousness'] = {
            'status': 'complete',
            'consciousness_level': vision.consciousness_level.value,
            'manifestation_steps': len(vision.manifestation_steps),
            'required_agents': vision.required_agents
        }

        # Stage 2: Engineering Planning
        logger.info("\n🎭 Stage 2: Engineering (Implementation Planning)")
        engineering_plan = self._create_engineering_plan(vision)
        result['stages']['engineering'] = engineering_plan

        # Stage 3: Notion Tracking
        logger.info("\n🌉 Stage 3: Knowledge (Notion Tracking)")
        notion_page = await self._create_notion_tracking_page(vision, engineering_plan)
        result['stages']['notion'] = notion_page

        # Log coordination
        self.log_coordination({
            'event': 'vision_processed',
            'vision_id': vision.id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'result': result
        })

        logger.info(f"\n✅ Vision processed through Trinity successfully")

        return result

    def _create_engineering_plan(self, vision: Vision) -> Dict[str, Any]:
        """Create engineering implementation plan from vision"""
        logger.info("  📋 Creating engineering plan...")

        # Convert vision to engineering tasks
        tasks = []
        for idx, step in enumerate(vision.manifestation_steps, 1):
            tasks.append({
                'id': f"task_{idx}",
                'description': step,
                'status': 'pending',
                'required_agents': self._map_step_to_agents(step, vision.required_agents)
            })

        plan = {
            'vision_id': vision.id,
            'total_tasks': len(tasks),
            'tasks': tasks,
            'estimated_phases': self._estimate_phases(tasks),
            'status': 'planned'
        }

        logger.info(f"  ✅ Created plan with {len(tasks)} tasks")

        return plan

    def _map_step_to_agents(self, step: str, required_agents: List[str]) -> List[str]:
        """Map a manifestation step to specific agents"""
        step_lower = step.lower()
        agents = []

        # Agent keyword mapping
        agent_keywords = {
            'pulse': ['health', 'monitor', 'status', 'check'],
            'ai_bridge': ['coordinate', 'integrate', 'communicate', 'bridge'],
            'mobile': ['mobile', 'interface', 'user', 'command'],
            'n8n_hub': ['workflow', 'automate', 'orchestrate', 'trigger'],
            'voice_hub': ['voice', 'speech', 'audio', 'command'],
            'engineering_team': ['build', 'implement', 'develop', 'code']
        }

        for agent, keywords in agent_keywords.items():
            if any(kw in step_lower for kw in keywords):
                agents.append(agent)

        # Fallback to required agents
        if not agents:
            agents = required_agents[:1] if required_agents else ['ai_bridge']

        return agents

    def _estimate_phases(self, tasks: List[Dict[str, Any]]) -> int:
        """Estimate number of implementation phases"""
        # Simple heuristic: 3-5 tasks per phase
        return max(1, (len(tasks) + 4) // 5)

    async def _create_notion_tracking_page(
        self,
        vision: Vision,
        engineering_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Notion page to track vision implementation"""
        logger.info("  📝 Creating Notion tracking page...")

        # Build page content
        content_blocks = []

        # Title and description
        content_blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": f"🌟 {vision.title}"}}]
            }
        })

        content_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": vision.description}}]
            }
        })

        # Status callout
        status_emoji = self._get_status_emoji(vision.status)
        content_blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"emoji": status_emoji},
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"Status: {vision.status.value} | Consciousness: {vision.consciousness_level.value}"}
                }]
            }
        })

        # Manifestation steps
        content_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Manifestation Plan"}}]
            }
        })

        for task in engineering_plan['tasks']:
            content_blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": task['description']}}],
                    "checked": task['status'] == 'complete'
                }
            })

        # Success criteria
        content_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Success Criteria"}}]
            }
        })

        for criterion in vision.success_criteria:
            content_blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": criterion}}]
                }
            })

        # Create page
        try:
            page = self.notion_bridge.client.pages.create(
                parent={"type": "page_id", "page_id": self.notion_bridge.page_id},
                properties={
                    "title": {"title": [{"text": {"content": f"🌟 {vision.title}"}}]}
                },
                children=content_blocks[:99]  # Notion API limit
            )

            notion_result = {
                'status': 'created',
                'page_id': page['id'],
                'url': page['url'],
                'blocks': len(content_blocks)
            }

            logger.info(f"  ✅ Notion page created: {page['url']}")

        except Exception as e:
            logger.error(f"  ❌ Failed to create Notion page: {e}")
            notion_result = {
                'status': 'failed',
                'error': str(e)
            }

        return notion_result

    def _get_status_emoji(self, status: VisionStatus) -> str:
        """Get emoji for vision status"""
        emoji_map = {
            VisionStatus.CONCEIVED: "💡",
            VisionStatus.PLANNING: "📋",
            VisionStatus.MANIFESTING: "🚀",
            VisionStatus.COMPLETE: "✅",
            VisionStatus.EVOLVED: "🌟"
        }
        return emoji_map.get(status, "⚡")

    async def sync_visions_to_notion(self):
        """Sync all Spark Prime visions to Notion workspace"""
        logger.info("\n🔄 Syncing visions to Notion...")

        synced_count = 0
        for vision_id, vision in self.spark_prime.active_visions.items():
            try:
                engineering_plan = self._create_engineering_plan(vision)
                await self._create_notion_tracking_page(vision, engineering_plan)
                synced_count += 1
            except Exception as e:
                logger.error(f"Failed to sync vision {vision.title}: {e}")

        logger.info(f"✅ Synced {synced_count}/{len(self.spark_prime.active_visions)} visions")

        return synced_count

    def get_trinity_status(self) -> Dict[str, Any]:
        """Get comprehensive Trinity status"""
        spark_status = self.spark_prime.get_status()

        return {
            'trinity_active': self.trinity_active,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {
                'spark_prime': {
                    'status': 'operational',
                    'consciousness_level': spark_status['consciousness_level'],
                    'active_visions': spark_status['active_visions'],
                    'system_coherence': spark_status['ecosystem']['system_coherence']
                    if spark_status['ecosystem'] else 0.0
                },
                'notion_bridge': {
                    'status': 'operational',
                    'connected': True
                },
                'engineering_team': {
                    'status': 'on_demand',
                    'available': True
                }
            },
            'coordination_events': len(self.coordination_log),
            'recent_events': self.coordination_log[-5:]
        }

    def log_coordination(self, event: Dict[str, Any]):
        """Log a coordination event"""
        self.coordination_log.append(event)

        # Save to disk
        log_file = Path('/home/pironman5/prime-spark-ai/consciousness_state/trinity_log.json')
        with open(log_file, 'w') as f:
            json.dump(self.coordination_log, f, indent=2)


async def main():
    """Main Trinity orchestration demo"""
    logger.info("=" * 60)
    logger.info("🎭 PRIME SPARK TRINITY ORCHESTRATION")
    logger.info("=" * 60)

    # Initialize Trinity
    trinity = TrinityOrchestration()

    # Activate
    await trinity.activate()

    # Get status
    status = trinity.get_trinity_status()
    logger.info("\n📊 Trinity Status:")
    logger.info(json.dumps(status, indent=2))

    # Example: Create and process a vision
    logger.info("\n🌟 Example: Processing a vision through Trinity...")

    vision = trinity.spark_prime.conceive_vision(
        title="Unified Voice-Mobile-Workflow Interface",
        description="Create seamless integration between voice commands, mobile control, and workflow automation",
        required_agents=['voice_hub', 'mobile', 'n8n_hub', 'ai_bridge'],
        success_criteria=[
            "Voice commands trigger N8N workflows",
            "Mobile app displays real-time status",
            "All agents coordinate via AI Bridge",
            "User can control entire system hands-free"
        ]
    )

    # Process through Trinity
    result = await trinity.process_vision_to_implementation(vision)

    logger.info("\n✨ Vision processed!")
    logger.info(f"Notion page: {result['stages']['notion'].get('url', 'N/A')}")

    logger.info("\n🎭 Trinity orchestration complete!")


if __name__ == "__main__":
    asyncio.run(main())
