#!/usr/bin/env python3
"""
Prime Spark Voice Command Hub

Voice-controlled agent interaction using Whisper (STT) and Piper (TTS).
Provides hands-free control of all Prime Spark agents with natural language commands.

Author: Prime Spark Engineering Team
Version: 1.0.0
"""

import os
import json
import asyncio
import logging
import hashlib
import wave
import io
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

import redis
import requests
import numpy as np
import pyaudio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Whisper import (faster-whisper for Pi 5 optimization)
try:
    from faster_whisper import WhisperModel
    WHISPER_BACKEND = "faster-whisper"
except ImportError:
    try:
        import whisper
        WHISPER_BACKEND = "openai-whisper"
    except ImportError:
        WHISPER_BACKEND = None
        logging.warning("No Whisper installation found. Install with: pip install faster-whisper")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================

class Config:
    """Voice Command Hub Configuration"""

    # Voice Hub Configuration
    HUB_API_KEY = os.getenv("HUB_API_KEY", "prime-spark-voice-key")

    # Whisper Configuration
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # cpu or cuda
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # int8, float16, float32
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

    # Piper TTS Configuration
    PIPER_MODEL = os.getenv("PIPER_MODEL", "en_US-lessac-medium")
    PIPER_VOICE_PATH = os.getenv("PIPER_VOICE_PATH", "/opt/piper/voices")

    # Audio Configuration
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))
    CHANNELS = int(os.getenv("CHANNELS", 1))
    FORMAT = pyaudio.paInt16

    # ReSpeaker Configuration
    RESPEAKER_INDEX = int(os.getenv("RESPEAKER_INDEX", -1))  # -1 for auto-detect

    # Wake Word
    WAKE_WORDS = os.getenv("WAKE_WORDS", "hey spark,hey prime").split(",")

    # Command Configuration
    MAX_AUDIO_DURATION = int(os.getenv("MAX_AUDIO_DURATION", 30))  # seconds
    COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", 5))  # seconds
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))

    # Prime Spark Agents
    PULSE_API_URL = os.getenv("PULSE_API_URL", "http://localhost:8001")
    AI_BRIDGE_API_URL = os.getenv("AI_BRIDGE_API_URL", "http://localhost:8002")
    MOBILE_API_URL = os.getenv("MOBILE_API_URL", "http://localhost:8003")
    N8N_HUB_API_URL = os.getenv("N8N_HUB_API_URL", "http://localhost:8004")

    # NLU Configuration (using Ollama for intent classification)
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    NLU_MODEL = os.getenv("NLU_MODEL", "llama3.2:latest")

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 4))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # Cache Configuration
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
    CONVERSATION_TTL = int(os.getenv("CONVERSATION_TTL", 600))  # 10 minutes


config = Config()

# ==================== Models ====================

class CommandIntent(str, Enum):
    """Command intent types"""
    STATUS_CHECK = "status_check"
    AGENT_CONTROL = "agent_control"
    WORKFLOW_TRIGGER = "workflow_trigger"
    ANALYSIS_REQUEST = "analysis_request"
    TASK_CREATION = "task_creation"
    INFORMATION_QUERY = "information_query"
    HELP = "help"
    UNKNOWN = "unknown"


class AgentTarget(str, Enum):
    """Target agents"""
    PULSE = "pulse"
    AI_BRIDGE = "ai_bridge"
    MOBILE = "mobile"
    N8N_HUB = "n8n_hub"
    ENGINEERING = "engineering"
    ALL = "all"


class CommandAction(str, Enum):
    """Command actions"""
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"
    HEALTH = "health"
    TRIGGER = "trigger"
    ANALYZE = "analyze"
    CREATE = "create"
    LIST = "list"
    HELP = "help"


class VoiceCommand(BaseModel):
    """Voice command model"""
    transcript: str
    intent: CommandIntent
    action: Optional[CommandAction] = None
    target: Optional[AgentTarget] = None
    parameters: Dict[str, Any] = {}
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.now)


class CommandResult(BaseModel):
    """Command execution result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    spoken_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """Conversation context for multi-turn interactions"""
    session_id: str
    history: List[Dict[str, Any]] = []
    last_intent: Optional[CommandIntent] = None
    last_target: Optional[AgentTarget] = None
    awaiting_confirmation: bool = False
    confirmation_action: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ==================== Voice Command Hub ====================

class VoiceCommandHub:
    """
    Voice Command Hub

    Manages voice-controlled agent interaction:
    - Speech-to-text with Whisper
    - Text-to-speech with Piper
    - Natural language command parsing
    - Agent command routing
    - Conversation management
    """

    def __init__(self):
        """Initialize Voice Command Hub"""
        self.config = config

        # Initialize Redis
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

        # Initialize Whisper
        self.whisper_model = None
        self._init_whisper()

        # Initialize audio
        self.audio = pyaudio.PyAudio()
        self.respeaker_device_index = self._find_respeaker()

        # Conversation contexts
        self.conversations: Dict[str, ConversationContext] = {}

        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []

        # Command patterns for quick matching
        self.command_patterns = self._build_command_patterns()

        logger.info("🎤 Voice Command Hub initialized")

    def _init_whisper(self):
        """Initialize Whisper model"""
        if not WHISPER_BACKEND:
            logger.error("❌ Whisper not available")
            return

        try:
            if WHISPER_BACKEND == "faster-whisper":
                self.whisper_model = WhisperModel(
                    config.WHISPER_MODEL,
                    device=config.WHISPER_DEVICE,
                    compute_type=config.WHISPER_COMPUTE_TYPE
                )
                logger.info(f"✅ Whisper initialized (faster-whisper, model: {config.WHISPER_MODEL})")
            else:
                self.whisper_model = whisper.load_model(config.WHISPER_MODEL)
                logger.info(f"✅ Whisper initialized (openai-whisper, model: {config.WHISPER_MODEL})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Whisper: {e}")
            self.whisper_model = None

    def _find_respeaker(self) -> Optional[int]:
        """Find ReSpeaker USB 4 Mic Array device index"""
        if config.RESPEAKER_INDEX >= 0:
            return config.RESPEAKER_INDEX

        # Search for ReSpeaker
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            name = info.get('name', '').lower()
            if 'respeaker' in name or 'usb audio' in name:
                logger.info(f"✅ Found ReSpeaker at index {i}: {info['name']}")
                return i

        logger.warning("⚠️ ReSpeaker not found, using default input device")
        return None

    def _build_command_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for command matching"""
        return {
            'status': [
                r'check.*status',
                r'show.*status',
                r'what.*status',
                r'how.*doing'
            ],
            'health': [
                r'health\s+check',
                r'are.*healthy',
                r'system.*health'
            ],
            'trigger': [
                r'trigger.*workflow',
                r'run.*workflow',
                r'execute.*workflow',
                r'start.*workflow'
            ],
            'analyze': [
                r'analyze.*page',
                r'check.*page',
                r'summarize.*page'
            ],
            'control': [
                r'(start|stop|restart)\s+(\w+)\s+agent',
                r'(start|stop|restart)\s+agent'
            ],
            'query': [
                r'what.*cpu',
                r'what.*memory',
                r'how.*much',
                r'show.*me'
            ]
        }

    # ==================== Speech Recognition ====================

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Transcribe audio to text using Whisper

        Args:
            audio_data: Audio bytes (WAV format)
            language: Language code (default: auto-detect)

        Returns:
            Tuple of (transcript, confidence)
        """
        if not self.whisper_model:
            raise HTTPException(status_code=503, detail="Whisper model not available")

        try:
            # Save audio to temporary file (Whisper needs file input)
            audio_path = f"/tmp/voice_input_{datetime.now().timestamp()}.wav"
            with open(audio_path, 'wb') as f:
                f.write(audio_data)

            # Transcribe
            if WHISPER_BACKEND == "faster-whisper":
                segments, info = self.whisper_model.transcribe(
                    audio_path,
                    language=language or config.WHISPER_LANGUAGE,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )

                transcript = " ".join([seg.text for seg in segments])
                confidence = info.language_probability if hasattr(info, 'language_probability') else 1.0
            else:
                result = self.whisper_model.transcribe(
                    audio_path,
                    language=language or config.WHISPER_LANGUAGE
                )
                transcript = result['text']
                confidence = 1.0  # openai-whisper doesn't provide confidence

            # Cleanup
            os.remove(audio_path)

            logger.info(f"🎤 Transcribed: \"{transcript}\" (confidence: {confidence:.2f})")
            return transcript.strip(), confidence

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

    async def listen_for_command(self, duration: int = 5) -> bytes:
        """
        Listen for voice command from microphone

        Args:
            duration: Recording duration in seconds

        Returns:
            Audio data as WAV bytes
        """
        logger.info(f"👂 Listening for {duration} seconds...")

        # Open audio stream
        stream = self.audio.open(
            format=config.FORMAT,
            channels=config.CHANNELS,
            rate=config.SAMPLE_RATE,
            input=True,
            input_device_index=self.respeaker_device_index,
            frames_per_buffer=config.CHUNK_SIZE
        )

        # Record audio
        frames = []
        for _ in range(0, int(config.SAMPLE_RATE / config.CHUNK_SIZE * duration)):
            data = stream.read(config.CHUNK_SIZE)
            frames.append(data)

        # Stop stream
        stream.stop_stream()
        stream.close()

        # Convert to WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(config.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(config.FORMAT))
            wf.setframerate(config.SAMPLE_RATE)
            wf.writeframes(b''.join(frames))

        wav_buffer.seek(0)
        return wav_buffer.read()

    # ==================== Text-to-Speech ====================

    async def synthesize_speech(self, text: str) -> bytes:
        """
        Synthesize speech from text using Piper

        Args:
            text: Text to synthesize

        Returns:
            Audio data as WAV bytes
        """
        try:
            # Check if Piper is available
            piper_cmd = "piper"
            model_path = f"{config.PIPER_VOICE_PATH}/{config.PIPER_MODEL}.onnx"

            if not os.path.exists(model_path):
                logger.warning(f"⚠️ Piper model not found: {model_path}")
                logger.info("Using fallback TTS (espeak)")
                # Fallback to espeak if Piper not available
                import subprocess
                result = subprocess.run(
                    ["espeak", "-w", "/tmp/tts_output.wav", text],
                    capture_output=True
                )
                with open("/tmp/tts_output.wav", "rb") as f:
                    return f.read()

            # Use Piper for TTS
            import subprocess
            output_path = f"/tmp/tts_{datetime.now().timestamp()}.wav"

            result = subprocess.run(
                [piper_cmd, "--model", model_path, "--output_file", output_path],
                input=text.encode(),
                capture_output=True
            )

            if result.returncode != 0:
                raise Exception(f"Piper failed: {result.stderr.decode()}")

            # Read audio
            with open(output_path, "rb") as f:
                audio_data = f.read()

            # Cleanup
            os.remove(output_path)

            logger.info(f"🔊 Synthesized speech: \"{text[:50]}...\"")
            return audio_data

        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

    async def speak(self, text: str):
        """
        Speak text out loud (synthesize and play)

        Args:
            text: Text to speak
        """
        try:
            audio_data = await self.synthesize_speech(text)

            # Play audio
            wav_buffer = io.BytesIO(audio_data)
            with wave.open(wav_buffer, 'rb') as wf:
                stream = self.audio.open(
                    format=self.audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )

                data = wf.readframes(config.CHUNK_SIZE)
                while data:
                    stream.write(data)
                    data = wf.readframes(config.CHUNK_SIZE)

                stream.stop_stream()
                stream.close()

        except Exception as e:
            logger.error(f"❌ Failed to speak: {e}")

    # ==================== Command Parsing ====================

    async def parse_command(self, transcript: str, context: Optional[ConversationContext] = None) -> VoiceCommand:
        """
        Parse natural language command

        Args:
            transcript: Transcribed text
            context: Conversation context for multi-turn

        Returns:
            VoiceCommand object
        """
        transcript_lower = transcript.lower().strip()

        # Check for help
        if any(word in transcript_lower for word in ['help', 'what can you do', 'commands']):
            return VoiceCommand(
                transcript=transcript,
                intent=CommandIntent.HELP,
                action=CommandAction.HELP,
                confidence=1.0
            )

        # Try pattern matching first (fast)
        for pattern_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, transcript_lower):
                    return await self._parse_by_pattern(transcript, pattern_type, pattern)

        # Fallback to LLM-based NLU (slower but more flexible)
        return await self._parse_with_llm(transcript, context)

    async def _parse_by_pattern(self, transcript: str, pattern_type: str, pattern: str) -> VoiceCommand:
        """Parse command using regex patterns"""
        transcript_lower = transcript.lower()

        if pattern_type == 'status':
            # Extract target agent
            target = self._extract_agent_target(transcript_lower)
            return VoiceCommand(
                transcript=transcript,
                intent=CommandIntent.STATUS_CHECK,
                action=CommandAction.STATUS,
                target=target,
                confidence=0.9
            )

        elif pattern_type == 'health':
            target = self._extract_agent_target(transcript_lower)
            return VoiceCommand(
                transcript=transcript,
                intent=CommandIntent.STATUS_CHECK,
                action=CommandAction.HEALTH,
                target=target,
                confidence=0.9
            )

        elif pattern_type == 'trigger':
            # Extract workflow name
            workflow_match = re.search(r'workflow\s+(\w+)', transcript_lower)
            workflow_name = workflow_match.group(1) if workflow_match else None

            return VoiceCommand(
                transcript=transcript,
                intent=CommandIntent.WORKFLOW_TRIGGER,
                action=CommandAction.TRIGGER,
                target=AgentTarget.N8N_HUB,
                parameters={'workflow_name': workflow_name} if workflow_name else {},
                confidence=0.85
            )

        elif pattern_type == 'analyze':
            # Extract page ID or title
            page_match = re.search(r'page\s+(\w+)', transcript_lower)
            page_id = page_match.group(1) if page_match else None

            return VoiceCommand(
                transcript=transcript,
                intent=CommandIntent.ANALYSIS_REQUEST,
                action=CommandAction.ANALYZE,
                target=AgentTarget.AI_BRIDGE,
                parameters={'page_id': page_id} if page_id else {},
                confidence=0.85
            )

        elif pattern_type == 'control':
            # Extract action and agent
            control_match = re.search(r'(start|stop|restart)\s+(?:(\w+)\s+)?agent', transcript_lower)
            if control_match:
                action_str = control_match.group(1)
                agent_name = control_match.group(2)

                action = CommandAction(action_str)
                target = AgentTarget(agent_name) if agent_name and agent_name in ['pulse', 'mobile'] else None

                return VoiceCommand(
                    transcript=transcript,
                    intent=CommandIntent.AGENT_CONTROL,
                    action=action,
                    target=target,
                    confidence=0.9
                )

        elif pattern_type == 'query':
            return VoiceCommand(
                transcript=transcript,
                intent=CommandIntent.INFORMATION_QUERY,
                parameters={'query': transcript},
                confidence=0.7
            )

        # Default
        return VoiceCommand(
            transcript=transcript,
            intent=CommandIntent.UNKNOWN,
            confidence=0.5
        )

    def _extract_agent_target(self, transcript: str) -> AgentTarget:
        """Extract agent target from transcript"""
        if 'pulse' in transcript:
            return AgentTarget.PULSE
        elif 'ai bridge' in transcript or 'bridge' in transcript:
            return AgentTarget.AI_BRIDGE
        elif 'mobile' in transcript:
            return AgentTarget.MOBILE
        elif 'n8n' in transcript or 'workflow' in transcript:
            return AgentTarget.N8N_HUB
        elif 'engineering' in transcript:
            return AgentTarget.ENGINEERING
        elif 'all' in transcript or 'everything' in transcript:
            return AgentTarget.ALL
        else:
            return AgentTarget.ALL

    async def _parse_with_llm(self, transcript: str, context: Optional[ConversationContext]) -> VoiceCommand:
        """Parse command using LLM for complex cases"""
        try:
            # Build prompt for intent classification
            prompt = f"""You are a voice command parser for Prime Spark AI agents. Parse this command:

Command: "{transcript}"

Available intents:
- status_check: Check agent status or health
- agent_control: Start, stop, or restart an agent
- workflow_trigger: Trigger an N8N workflow
- analysis_request: Analyze content (Notion pages, etc.)
- task_creation: Create a task for the engineering team
- information_query: Answer questions about the system
- help: Get help or list commands

Available agents:
- pulse: Infrastructure monitoring
- ai_bridge: AI-powered content analysis
- mobile: Mobile command center
- n8n_hub: Workflow orchestration
- engineering: Engineering team
- all: All agents

Actions: start, stop, restart, status, health, trigger, analyze, create, list, help

Respond with JSON only:
{{
  "intent": "<intent>",
  "action": "<action or null>",
  "target": "<agent or null>",
  "parameters": {{}},
  "confidence": 0.0-1.0
}}"""

            # Call Ollama for NLU
            response = requests.post(
                f"{config.OLLAMA_URL}/api/generate",
                json={
                    "model": config.NLU_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                parsed = json.loads(result['response'])

                return VoiceCommand(
                    transcript=transcript,
                    intent=CommandIntent(parsed.get('intent', 'unknown')),
                    action=CommandAction(parsed['action']) if parsed.get('action') else None,
                    target=AgentTarget(parsed['target']) if parsed.get('target') else None,
                    parameters=parsed.get('parameters', {}),
                    confidence=parsed.get('confidence', 0.6)
                )

        except Exception as e:
            logger.warning(f"⚠️ LLM parsing failed: {e}")

        # Fallback to unknown intent
        return VoiceCommand(
            transcript=transcript,
            intent=CommandIntent.UNKNOWN,
            confidence=0.3
        )

    # ==================== Command Execution ====================

    async def execute_command(self, command: VoiceCommand) -> CommandResult:
        """
        Execute parsed voice command

        Args:
            command: Parsed voice command

        Returns:
            CommandResult with execution status
        """
        logger.info(f"⚡ Executing command: {command.intent.value} -> {command.action}")

        try:
            if command.intent == CommandIntent.HELP:
                return await self._handle_help()

            elif command.intent == CommandIntent.STATUS_CHECK:
                return await self._handle_status_check(command)

            elif command.intent == CommandIntent.AGENT_CONTROL:
                return await self._handle_agent_control(command)

            elif command.intent == CommandIntent.WORKFLOW_TRIGGER:
                return await self._handle_workflow_trigger(command)

            elif command.intent == CommandIntent.ANALYSIS_REQUEST:
                return await self._handle_analysis_request(command)

            elif command.intent == CommandIntent.TASK_CREATION:
                return await self._handle_task_creation(command)

            elif command.intent == CommandIntent.INFORMATION_QUERY:
                return await self._handle_information_query(command)

            else:
                return CommandResult(
                    success=False,
                    message="I didn't understand that command. Say 'help' for available commands.",
                    spoken_response="I didn't understand. Say help for available commands."
                )

        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return CommandResult(
                success=False,
                message=f"Command execution error: {str(e)}",
                spoken_response="Sorry, I encountered an error executing that command."
            )

    async def _handle_help(self) -> CommandResult:
        """Handle help command"""
        help_text = """Available voice commands:

System Status:
- "Check system status"
- "Show Pulse agent health"
- "What's the CPU usage?"

Agent Control:
- "Start Pulse agent"
- "Stop mobile agent"
- "Restart AI Bridge"

Workflows:
- "Trigger deployment workflow"
- "Run health check workflows"

Analysis:
- "Analyze latest Notion page"

Ask 'help' anytime for this list."""

        return CommandResult(
            success=True,
            message=help_text,
            spoken_response="I can check status, control agents, trigger workflows, and analyze content. Say help anytime for the full list."
        )

    async def _handle_status_check(self, command: VoiceCommand) -> CommandResult:
        """Handle status check commands"""
        target = command.target or AgentTarget.ALL

        if target == AgentTarget.PULSE or target == AgentTarget.ALL:
            try:
                response = requests.get(f"{config.PULSE_API_URL}/pulse/health", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    message = f"Pulse agent is {data.get('status', 'unknown')}"
                    return CommandResult(
                        success=True,
                        message=message,
                        data=data,
                        spoken_response=message
                    )
            except:
                pass

        return CommandResult(
            success=False,
            message="Unable to reach agents",
            spoken_response="Unable to reach agents"
        )

    async def _handle_agent_control(self, command: VoiceCommand) -> CommandResult:
        """Handle agent control commands"""
        # Placeholder - would integrate with actual agent control
        return CommandResult(
            success=True,
            message=f"Command received: {command.action.value} {command.target.value if command.target else 'agent'}",
            spoken_response=f"Understood. {command.action.value} command sent."
        )

    async def _handle_workflow_trigger(self, command: VoiceCommand) -> CommandResult:
        """Handle workflow trigger commands"""
        workflow_name = command.parameters.get('workflow_name')

        if not workflow_name:
            return CommandResult(
                success=False,
                message="Please specify which workflow to trigger",
                spoken_response="Which workflow should I trigger?"
            )

        # Trigger via N8N Hub
        try:
            response = requests.post(
                f"{config.N8N_HUB_API_URL}/api/n8n/execute/{workflow_name}",
                headers={"X-API-Key": "prime-spark-n8n-key"},
                json={"workflow_id": workflow_name, "agent_id": "voice"},
                timeout=5
            )

            if response.status_code == 200:
                return CommandResult(
                    success=True,
                    message=f"Workflow '{workflow_name}' triggered",
                    spoken_response=f"Workflow {workflow_name} started"
                )
        except:
            pass

        return CommandResult(
            success=False,
            message="Failed to trigger workflow",
            spoken_response="Unable to trigger workflow"
        )

    async def _handle_analysis_request(self, command: VoiceCommand) -> CommandResult:
        """Handle analysis request commands"""
        return CommandResult(
            success=True,
            message="Analysis request received",
            spoken_response="Starting analysis"
        )

    async def _handle_task_creation(self, command: VoiceCommand) -> CommandResult:
        """Handle task creation commands"""
        return CommandResult(
            success=True,
            message="Task creation received",
            spoken_response="Task created"
        )

    async def _handle_information_query(self, command: VoiceCommand) -> CommandResult:
        """Handle information query commands"""
        # Use LLM to answer questions
        return CommandResult(
            success=True,
            message="Query received",
            spoken_response="Let me check that for you"
        )

    # ==================== Conversation Management ====================

    def _get_conversation(self, session_id: str) -> ConversationContext:
        """Get or create conversation context"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(session_id=session_id)
        return self.conversations[session_id]

    # ==================== Health & Metrics ====================

    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "whisper_available": self.whisper_model is not None,
            "respeaker_found": self.respeaker_device_index is not None,
            "redis": "connected" if self.redis_client else "disconnected",
            "conversations": len(self.conversations),
            "websocket_connections": len(self.websocket_connections)
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics"""
        return {
            "total_conversations": len(self.conversations),
            "active_websockets": len(self.websocket_connections),
            "whisper_backend": WHISPER_BACKEND,
            "whisper_model": config.WHISPER_MODEL
        }


# ==================== FastAPI Application ====================

app = FastAPI(
    title="Prime Spark Voice Command Hub",
    description="Voice-controlled agent interaction with Whisper and Piper",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
hub = VoiceCommandHub()

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Prime Spark Voice Command Hub",
        "version": "1.0.0",
        "status": "listening",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check"""
    return await hub.health_check()

@app.get("/metrics")
async def metrics():
    """Metrics"""
    return await hub.get_metrics()

# ==================== Voice Commands ====================

@app.post("/api/voice/transcribe")
async def transcribe(file: UploadFile = File(...), api_key: str = Depends(verify_api_key)):
    """Transcribe audio file"""
    audio_data = await file.read()
    transcript, confidence = await hub.transcribe_audio(audio_data)

    return {
        "transcript": transcript,
        "confidence": confidence
    }

@app.post("/api/voice/command")
async def execute_voice_command(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Execute voice command from audio file"""
    # Transcribe
    audio_data = await file.read()
    transcript, confidence = await hub.transcribe_audio(audio_data)

    # Parse
    context = hub._get_conversation(session_id) if session_id else None
    command = await hub.parse_command(transcript, context)

    # Execute
    result = await hub.execute_command(command)

    return {
        "transcript": transcript,
        "confidence": confidence,
        "command": command.dict(),
        "result": result.dict()
    }

@app.post("/api/voice/speak")
async def speak_text(text: str, api_key: str = Depends(verify_api_key)):
    """Synthesize speech from text"""
    audio_data = await hub.synthesize_speech(text)

    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav"
    )

# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
