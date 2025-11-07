#!/usr/bin/env python3
"""
Build Prime Spark Voice Command System

Uses the Engineering Team to design and implement voice-controlled
agent interaction using Whisper (STT) and Piper (TTS).
"""

import os
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from agents.engineering_team.orchestrator import EngineeringTeamOrchestrator
from dotenv import load_dotenv

load_dotenv()


def main():
    print("\n" + "="*70)
    print("🎤 BUILDING PRIME SPARK VOICE COMMAND SYSTEM")
    print("="*70 + "\n")

    team = EngineeringTeamOrchestrator()

    voice_project = {
        'name': 'Prime Spark Voice Command Hub',
        'description': '''
Build a comprehensive voice command system for hands-free control of
Prime Spark agents using Whisper (speech-to-text) and Piper (text-to-speech).

The Voice Command Hub should provide:

1. SPEECH RECOGNITION (WHISPER)
   - Real-time speech-to-text conversion
   - Support for Whisper models (tiny, base, small, medium, large)
   - Language detection
   - Noise suppression integration
   - Continuous listening mode
   - Wake word detection
   - Voice Activity Detection (VAD)
   - Multi-microphone support (ReSpeaker USB 4 Mic Array)

2. TEXT-TO-SPEECH (PIPER)
   - Natural voice synthesis
   - Multiple voice options
   - Emotion and tone control
   - Real-time response generation
   - Audio streaming
   - Voice feedback for commands
   - Error message vocalization

3. COMMAND PARSING & ROUTING
   - Natural language command interpretation
   - Intent classification
   - Entity extraction (agent names, actions, parameters)
   - Command validation
   - Ambiguity resolution
   - Context-aware parsing
   - Multi-step command support

4. AGENT INTEGRATION
   - Voice control for Pulse agent (status checks)
   - Voice control for AI Bridge (content analysis)
   - Voice control for N8N Hub (workflow triggers)
   - Voice control for Mobile Command Center
   - Voice control for Engineering Team (task creation)
   - Agent response vocalization
   - Status updates via voice

5. AUDIO PROCESSING
   - ReSpeaker USB 4 Mic Array integration
   - Built-in AEC (Acoustic Echo Cancellation)
   - Built-in VAD (Voice Activity Detection)
   - Built-in DOA (Direction of Arrival)
   - Beamforming
   - Noise suppression
   - Audio preprocessing
   - Sample rate optimization (16kHz)

6. VOICE COMMANDS
   - "Check system status"
   - "Show me Pulse agent health"
   - "Trigger workflow [name]"
   - "Analyze Notion page [id]"
   - "Create task: [description]"
   - "Deploy [component]"
   - "What's the CPU usage?"
   - "Run all health checks"
   - "Stop [agent]"
   - "Start [agent]"

7. CONVERSATION MODE
   - Multi-turn conversations
   - Context retention
   - Clarification questions
   - Confirmation requests
   - Help and guidance
   - Voice-based navigation

8. SECURITY & PRIVACY
   - Voice authentication (optional)
   - Command authorization
   - Audio data privacy
   - Secure API communication
   - Rate limiting
   - Command logging

Hardware Integration:
- ReSpeaker USB 4 Mic Array
- Raspberry Pi 5 audio output
- Hailo-8 AI accelerator (optional for Whisper acceleration)
- Pi 5 GPIO for LED indicators

Agent Integration Points:
- Pulse API: http://localhost:8001
- AI Bridge API: http://localhost:8002
- Mobile API: http://localhost:8003
- N8N Hub API: http://localhost:8004

Use Cases:
- Hands-free infrastructure monitoring
- Voice-activated workflow execution
- Conversational agent control
- Accessibility for users with mobility limitations
- Multi-tasking while monitoring systems
- Voice-guided troubleshooting
        ''',
        'requirements': [
            'Integrate Whisper for speech-to-text',
            'Integrate Piper for text-to-speech',
            'ReSpeaker USB 4 Mic Array support',
            'Real-time audio streaming',
            'Voice Activity Detection (VAD)',
            'Wake word detection',
            'Natural language command parsing',
            'Intent classification and routing',
            'Agent command execution',
            'Voice response generation',
            'Multi-turn conversation support',
            'Context-aware command interpretation',
            'Error handling with voice feedback',
            'Audio preprocessing pipeline',
            'Continuous listening mode',
            'Command history tracking',
            'Voice authentication (optional)',
            'WebSocket for real-time audio',
            'REST API for commands',
            'Integration with all Prime Spark agents'
        ],
        'endpoints': [
            # Audio Input
            '/api/voice/listen',
            '/api/voice/transcribe',
            '/api/voice/stop-listening',

            # Text-to-Speech
            '/api/voice/speak',
            '/api/voice/synthesize',

            # Commands
            '/api/voice/command',
            '/api/voice/command/parse',
            '/api/voice/command/execute',
            '/api/voice/command/history',

            # Agent Control
            '/api/voice/agents/status',
            '/api/voice/agents/{agent_id}/control',
            '/api/voice/workflows/trigger',

            # Conversation
            '/api/voice/conversation/start',
            '/api/voice/conversation/continue',
            '/api/voice/conversation/end',
            '/api/voice/conversation/context',

            # Configuration
            '/api/voice/config/whisper',
            '/api/voice/config/piper',
            '/api/voice/config/microphone',

            # WebSocket
            '/ws/voice/stream',
            '/ws/voice/responses',

            # Health & Metrics
            '/api/voice/health',
            '/api/voice/metrics'
        ],
        'priority': 'high',
        'target_deployment': 'Pi 5 (edge)',
        'tech_constraints': {
            'whisper_model': 'base or small (Pi 5 optimized)',
            'piper_voice': 'en_US-lessac-medium',
            'microphone': 'ReSpeaker USB 4 Mic Array',
            'sample_rate': '16000 Hz',
            'audio_format': 'WAV/PCM',
            'wake_word': 'hey spark or hey prime',
            'max_audio_length': '30 seconds',
            'response_timeout': '5 seconds',
            'hailo_acceleration': 'optional for Whisper'
        },
        'integration_points': {
            'pulse_api': 'http://localhost:8001',
            'ai_bridge_api': 'http://localhost:8002',
            'mobile_api': 'http://localhost:8003',
            'n8n_hub_api': 'http://localhost:8004',
            'engineering_team': 'Python API',
            'whisper': 'openai-whisper or faster-whisper',
            'piper': 'piper-tts',
            'respeaker': '/dev/snd/pcmC* (ALSA)',
            'ollama': 'http://localhost:11434 (for NLU)'
        },
        'example_commands': [
            "Hey Spark, check system status",
            "Show me Pulse agent health",
            "What's the CPU usage on Pi 5?",
            "Trigger the deployment workflow",
            "Analyze the latest Notion page",
            "Create a task to optimize database",
            "Start the AI Bridge agent",
            "Run all health checks",
            "Deploy mobile command center",
            "What workflows are running?",
            "Stop listening",
            "Help me with voice commands"
        ]
    }

    print("📋 Project Specification:")
    print(f"   Name: {voice_project['name']}")
    print(f"   Priority: {voice_project['priority']}")
    print(f"   Requirements: {len(voice_project['requirements'])}")
    print(f"   API Endpoints: {len(voice_project['endpoints'])}")
    print(f"   Voice Commands: 12+ example commands")
    print(f"   Hardware: ReSpeaker USB 4 Mic Array + Pi 5")
    print()

    print("🚀 Engineering team executing project...")
    print()

    results = team.execute_project(voice_project)

    print("\n" + "="*70)
    print("📊 VOICE COMMAND SYSTEM BUILD RESULTS")
    print("="*70)
    print(f"Status: {results['status'].upper()}")
    print(f"Project ID: {results['project_id']}")
    print()

    for phase_name, phase_data in results['phases'].items():
        print(f"\n{phase_name.upper()}:")
        for task_name, task_result in phase_data.items():
            status = task_result.get('status', 'unknown')
            status_icon = "✅" if status == "success" else "❌"
            print(f"  {status_icon} {task_name}: {status}")

    print("\n" + "="*70)
    print("🎤 VOICE COMMAND SYSTEM BUILT!")
    print("="*70)

    results_file = Path("/home/pironman5/prime-spark-ai/voice_interface/build_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved: {results_file}")

    print("\n" + "="*70)
    print("📝 NEXT STEPS:")
    print("="*70)
    print("1. Review architecture in build_results.json")
    print("2. Install Whisper (openai-whisper or faster-whisper)")
    print("3. Install Piper TTS")
    print("4. Configure ReSpeaker USB 4 Mic Array")
    print("5. Implement voice command hub")
    print("6. Test speech recognition")
    print("7. Test text-to-speech")
    print("8. Integrate with all agents")
    print("9. Deploy to Pi 5")
    print("10. Test voice commands")
    print()


if __name__ == "__main__":
    main()
