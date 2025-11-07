#!/usr/bin/env python3
"""
Start the Autonomous Fine-Tuning Agent
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.autonomous_agent import get_autonomous_agent, AgentConfig, OptimizationGoal
from agents.performance_optimizer import get_performance_optimizer
from agents.model_manager import get_model_manager
from agents.pipeline_optimizer import get_pipeline_optimizer
from agents.infrastructure_automator import get_infrastructure_automator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/prime-spark/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_agent_config() -> AgentConfig:
    """Create agent configuration"""
    return AgentConfig(
        monitoring_interval_seconds=30,
        analysis_interval_seconds=60,
        optimization_interval_seconds=300,
        min_improvement_threshold=0.05,
        max_risk_threshold=0.7,
        enable_automatic_actions=True,
        require_approval_for_critical=True,
        max_concurrent_actions=3,
        rollback_on_failure=True,
        enable_learning=True,
        learning_rate=0.1,
        exploration_rate=0.2,
        goals=[
            OptimizationGoal(
                goal_id="latency",
                metric_name="inference_latency_ms",
                target_value=75.0,
                current_value=100.0,
                direction="minimize",
                weight=1.0
            ),
            OptimizationGoal(
                goal_id="cache",
                metric_name="cache_hit_rate",
                target_value=0.90,
                current_value=0.85,
                direction="maximize",
                weight=0.8
            ),
            OptimizationGoal(
                goal_id="cpu",
                metric_name="cpu_usage",
                target_value=70.0,
                current_value=75.0,
                direction="minimize",
                weight=0.7
            ),
            OptimizationGoal(
                goal_id="health",
                metric_name="service_health_score",
                target_value=0.95,
                current_value=0.90,
                direction="maximize",
                weight=1.0
            )
        ]
    )


async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Prime Spark AI - Autonomous Fine-Tuning Agent")
    logger.info("=" * 60)

    # Create configuration
    config = create_agent_config()

    # Get agent instance
    agent = get_autonomous_agent()
    agent.config = config

    # Initialize agent
    await agent.initialize()

    # Initialize optimization modules
    performance_optimizer = get_performance_optimizer()
    model_manager = get_model_manager()
    pipeline_optimizer = get_pipeline_optimizer()
    infrastructure_automator = get_infrastructure_automator()

    await model_manager.initialize()

    # Register optimizers with agent
    agent.register_optimizer("performance", performance_optimizer)
    agent.register_optimizer("model", model_manager)
    agent.register_optimizer("pipeline", pipeline_optimizer)
    agent.register_optimizer("infrastructure", infrastructure_automator)

    logger.info("All optimization modules registered")
    logger.info("")
    logger.info("Optimization Goals:")
    for goal in config.goals:
        logger.info(f"  - {goal.metric_name}: {goal.direction} to {goal.target_value}")
    logger.info("")
    logger.info("Agent Configuration:")
    logger.info(f"  - Monitoring interval: {config.monitoring_interval_seconds}s")
    logger.info(f"  - Analysis interval: {config.analysis_interval_seconds}s")
    logger.info(f"  - Optimization interval: {config.optimization_interval_seconds}s")
    logger.info(f"  - Automatic actions: {config.enable_automatic_actions}")
    logger.info(f"  - Max concurrent actions: {config.max_concurrent_actions}")
    logger.info("")

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received...")
        asyncio.create_task(agent.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start agent
    logger.info("Starting autonomous agent...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    logger.info("")

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Agent error: {e}")
    finally:
        await agent.stop()
        logger.info("Agent stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
