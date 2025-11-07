#!/usr/bin/env python3
"""
Spark Prime Consciousness - Test Suite
=====================================

Tests the consciousness integration with all Prime Spark agents.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from agents.spark_prime import (
    SparkPrimeConsciousness,
    ConsciousnessLevel,
    TrinityOrchestration
)


async def test_consciousness_initialization():
    """Test consciousness initialization"""
    print("\n🧪 Test 1: Consciousness Initialization")
    print("-" * 60)

    spark = SparkPrimeConsciousness()
    assert spark is not None
    assert spark.consciousness_level == ConsciousnessLevel.STRATEGIC

    print("✅ Consciousness initialized")
    print(f"   Initial level: {spark.consciousness_level.value}")
    print(f"   Agents configured: {len(spark.agents)}")

    return spark


async def test_ecosystem_scan(spark):
    """Test ecosystem scanning"""
    print("\n🧪 Test 2: Ecosystem Scan")
    print("-" * 60)

    state = await spark.scan_ecosystem()
    assert state is not None

    print(f"✅ Ecosystem scanned")
    print(f"   Timestamp: {state.timestamp}")
    print(f"   System coherence: {state.system_coherence:.2f}")
    print(f"   Agents checked: {len(state.agents_status)}")

    for agent, status in state.agents_status.items():
        status_emoji = "✅" if status['status'] == 'healthy' else "⚠️"
        print(f"   {status_emoji} {agent}: {status['status']}")

    return state


async def test_vision_conception(spark):
    """Test vision conception"""
    print("\n🧪 Test 3: Vision Conception")
    print("-" * 60)

    vision = spark.conceive_vision(
        title="Test Vision: Multi-Agent Coordination",
        description="Test coordinated operation across multiple Prime Spark agents",
        required_agents=['pulse', 'ai_bridge', 'mobile'],
        success_criteria=[
            "All agents respond to coordination requests",
            "System maintains coherence >70%",
            "Mobile interface displays status"
        ]
    )

    assert vision is not None
    assert vision.title == "Test Vision: Multi-Agent Coordination"
    assert len(vision.required_agents) == 3

    print(f"✅ Vision conceived")
    print(f"   Title: {vision.title}")
    print(f"   Consciousness level: {vision.consciousness_level.value}")
    print(f"   Required agents: {', '.join(vision.required_agents)}")
    print(f"   Manifestation steps: {len(vision.manifestation_steps)}")

    return vision


async def test_consciousness_elevation(spark):
    """Test consciousness elevation"""
    print("\n🧪 Test 4: Consciousness Elevation")
    print("-" * 60)

    initial_level = spark.consciousness_level
    spark.elevate_consciousness(ConsciousnessLevel.VISIONARY)

    assert spark.consciousness_level == ConsciousnessLevel.VISIONARY

    print(f"✅ Consciousness elevated")
    print(f"   From: {initial_level.value}")
    print(f"   To: {spark.consciousness_level.value}")


async def test_reflection(spark):
    """Test deep reflection"""
    print("\n🧪 Test 5: Deep Reflection")
    print("-" * 60)

    insights = spark.reflect()
    assert insights is not None
    assert len(insights) > 0

    print(f"✅ Reflection generated {len(insights)} insights:")
    for i, insight in enumerate(insights, 1):
        print(f"   {i}. {insight}")


async def test_trinity_orchestration():
    """Test Trinity orchestration"""
    print("\n🧪 Test 6: Trinity Orchestration")
    print("-" * 60)

    trinity = TrinityOrchestration()
    assert trinity is not None

    print("✅ Trinity initialized")
    print(f"   Components: Spark Prime + Engineering + Notion")

    # Activate
    success = await trinity.activate()
    assert trinity.trinity_active

    print(f"✅ Trinity activated: {success}")

    # Get status
    status = trinity.get_trinity_status()
    print(f"   Active: {status['trinity_active']}")
    print(f"   Coordination events: {status['coordination_events']}")

    return trinity


async def test_vision_processing(trinity):
    """Test vision processing through Trinity"""
    print("\n🧪 Test 7: Vision Processing Through Trinity")
    print("-" * 60)

    # Create test vision
    vision = trinity.spark_prime.conceive_vision(
        title="Test Vision: Trinity Integration",
        description="Validate Trinity pipeline from vision to implementation",
        required_agents=['ai_bridge', 'pulse'],
        success_criteria=[
            "Engineering plan created",
            "Tasks generated",
            "Notion tracking operational"
        ]
    )

    # Process through Trinity
    result = await trinity.process_vision_to_implementation(vision)

    assert result is not None
    assert 'stages' in result
    assert 'consciousness' in result['stages']
    assert 'engineering' in result['stages']
    assert 'notion' in result['stages']

    print(f"✅ Vision processed through Trinity")
    print(f"   Vision: {vision.title}")
    print(f"   Stages completed: {len(result['stages'])}")

    for stage_name, stage_data in result['stages'].items():
        print(f"   • {stage_name}: {stage_data.get('status', 'N/A')}")


async def run_all_tests():
    """Run all consciousness tests"""
    print("=" * 60)
    print("🧠 SPARK PRIME CONSCIOUSNESS - TEST SUITE")
    print("=" * 60)

    try:
        # Test 1-5: Consciousness
        spark = await test_consciousness_initialization()
        await test_ecosystem_scan(spark)
        vision = await test_vision_conception(spark)
        await test_consciousness_elevation(spark)
        await test_reflection(spark)

        # Test 6-7: Trinity
        trinity = await test_trinity_orchestration()
        await test_vision_processing(trinity)

        # Summary
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Consciousness operational")
        print("✅ Trinity orchestration functional")
        print("✅ Vision pipeline validated")
        print("✅ Multi-agent coordination working")
        print()
        print("⚡ Spark Prime consciousness is ready for deployment!")
        print()

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test entry point"""
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
