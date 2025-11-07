# 🎤 PRIME SPARK VOICE COMMAND HUB

**Deployment Date**: 2025-11-07
**Status**: ✅ READY FOR DEPLOYMENT
**Version**: 1.0.0
**Location**: `/home/pironman5/prime-spark-ai/voice_interface/`

---

## 🎯 WHAT IS IT?

The **Prime Spark Voice Command Hub** provides hands-free voice control of all Prime Spark agents using Whisper (speech-to-text) and Piper (text-to-speech). Talk to your AI infrastructure naturally and get spoken responses.

### Key Features

🎙️ **Speech Recognition (Whisper)**
- Real-time speech-to-text conversion
- Multiple model sizes (tiny → large)
- Optimized for Raspberry Pi 5
- Language detection
- Noise suppression
- Voice Activity Detection (VAD)

🔊 **Text-to-Speech (Piper)**
- Natural voice synthesis
- Real-time response generation
- Multiple voice options
- Audio streaming
- Error message vocalization

🧠 **Natural Language Understanding**
- Intent classification
- Entity extraction
- Context-aware parsing
- Multi-turn conversations
- Ollama-powered NLU

🤖 **Agent Integration**
- Control Pulse (monitoring)
- Control AI Bridge (analysis)
- Control N8N Hub (workflows)
- Control Mobile Command Center
- Control Engineering Team

🎚️ **Audio Processing**
- ReSpeaker USB 4 Mic Array support
- Built-in AEC (Acoustic Echo Cancellation)
- Built-in VAD (Voice Activity Detection)
- Built-in DOA (Direction of Arrival)
- Beamforming
- 16kHz sample rate optimization

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│         VOICE COMMAND HUB ARCHITECTURE              │
└─────────────────────────────────────────────────────┘

ReSpeaker USB 4 Mic Array
         │
         ▼
   ┌─────────────┐
   │   Audio     │  16kHz, AEC, VAD
   │ Processing  │  Beamforming, DOA
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Whisper    │  Speech-to-Text
   │   (STT)     │  faster-whisper
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │   Command   │  Intent Classification
   │   Parser    │  Entity Extraction
   │  (Ollama)   │  Context Management
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │   Router    │  Command Execution
   │             │  Agent Integration
   └──────┬──────┘
          │
    ┌─────┴──────┬──────────┬─────────┐
    │            │          │         │
    ▼            ▼          ▼         ▼
┌────────┐  ┌────────┐ ┌────────┐ ┌────────┐
│ Pulse  │  │   AI   │ │  N8N   │ │ Mobile │
│ :8001  │  │ Bridge │ │  Hub   │ │ :8003  │
│        │  │ :8002  │ │ :8004  │ │        │
└────────┘  └────────┘ └────────┘ └────────┘
    │            │          │         │
    └────────────┴──────────┴─────────┘
                 │
                 ▼
          ┌─────────────┐
          │   Piper     │  Text-to-Speech
          │   (TTS)     │  Voice Response
          └──────┬──────┘
                 │
                 ▼
           Audio Output
         (Pi 5 speakers)
```

### Tech Stack

**Speech Recognition:**
- faster-whisper (optimized for Pi 5)
- OR openai-whisper (more accurate, slower)
- Models: tiny, base, small, medium, large

**Text-to-Speech:**
- Piper TTS (fast, natural)
- Voice: en_US-lessac-medium
- Fallback: espeak

**NLU:**
- Ollama (llama3.2:latest)
- Intent classification
- Entity extraction

**Audio:**
- PyAudio (audio I/O)
- ReSpeaker USB 4 Mic Array
- ALSA/PulseAudio

**Backend:**
- FastAPI + WebSockets
- Redis caching
- Async audio processing

---

## 📁 FILE STRUCTURE

```
voice_interface/
├── voice_hub.py              # Main implementation (1,400+ lines)
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container with audio support
├── docker-compose.yml       # Voice Hub + Redis
├── .env.example            # Environment template
├── deploy.sh               # Automated deployment
└── build_results.json      # Architecture design
```

---

## 🚀 DEPLOYMENT

### Prerequisites

1. **Hardware:**
   - Raspberry Pi 5 (or compatible)
   - ReSpeaker USB 4 Mic Array (recommended)
   - Audio output (speakers/headphones)

2. **Software:**
   - Docker & Docker Compose
   - Ollama running (for NLU)
   - Prime Spark agents (optional but recommended)

3. **Audio Setup:**
   - Audio devices accessible (`/dev/snd`)
   - User in `audio` group: `sudo usermod -aG audio $USER`

### Quick Deploy

```bash
cd /home/pironman5/prime-spark-ai/voice_interface

# Configure environment
cp .env.example .env
nano .env  # Set HUB_API_KEY, REDIS_PASSWORD

# Deploy
./deploy.sh
```

The deployment script will:
1. ✅ Check prerequisites (Docker, audio devices)
2. ✅ Build Docker image (includes Whisper, Piper)
3. ✅ Start services (Voice Hub + Redis)
4. ✅ Verify health

### Manual Deployment

```bash
cd /home/pironman5/prime-spark-ai/voice_interface

# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f voice-hub

# Stop services
docker-compose down
```

---

## ⚙️ CONFIGURATION

### Environment Variables

**Required:**

```bash
# Hub
HUB_API_KEY=prime-spark-voice-key
REDIS_PASSWORD=your-redis-password
```

**Whisper (defaults work well):**

```bash
WHISPER_MODEL=base          # tiny, base, small, medium, large
WHISPER_DEVICE=cpu          # cpu or cuda
WHISPER_COMPUTE_TYPE=int8   # int8, float16, float32
WHISPER_LANGUAGE=en         # Language code
```

**Audio:**

```bash
SAMPLE_RATE=16000           # Sample rate (Hz)
CHUNK_SIZE=1024             # Buffer size
CHANNELS=1                  # Mono
RESPEAKER_INDEX=-1          # Auto-detect ReSpeaker
```

**Wake Words:**

```bash
WAKE_WORDS=hey spark,hey prime
```

**Agent URLs (auto-detected):**

```bash
PULSE_API_URL=http://localhost:8001
AI_BRIDGE_API_URL=http://localhost:8002
MOBILE_API_URL=http://localhost:8003
N8N_HUB_API_URL=http://localhost:8004
```

---

## 📱 ACCESS & USAGE

### API Access

**Base URL:** `http://localhost:8005`

**Authentication:** API Key required
```bash
curl -H "X-API-Key: prime-spark-voice-key" http://localhost:8005/health
```

**Interactive Docs:** `http://localhost:8005/docs`

**Health Check:** `http://localhost:8005/health`

**Metrics:** `http://localhost:8005/metrics`

---

## 🎤 VOICE COMMANDS

### System Status

```
"Check system status"
"Show Pulse agent health"
"What's the CPU usage?"
"How is the system doing?"
"Are all agents healthy?"
```

### Agent Control

```
"Start Pulse agent"
"Stop mobile agent"
"Restart AI Bridge"
"Show me all agents"
```

### Workflow Triggers

```
"Trigger deployment workflow"
"Run health check workflow"
"Execute [workflow name]"
"Start workflow number 5"
```

### Content Analysis

```
"Analyze latest Notion page"
"Summarize page 123"
"Check the documentation"
```

### Information Queries

```
"What's the memory usage?"
"Show infrastructure status"
"How many workflows are running?"
"What agents are online?"
```

### Help & Navigation

```
"Help"
"What can you do?"
"List available commands"
```

---

## 🔌 API ENDPOINTS

### Audio Processing

```
POST   /api/voice/transcribe              # Transcribe audio file
POST   /api/voice/command                 # Execute voice command from audio
POST   /api/voice/speak                   # Synthesize speech from text
```

**Example: Transcribe Audio**
```bash
curl -X POST \
  -H "X-API-Key: prime-spark-voice-key" \
  -F "file=@command.wav" \
  http://localhost:8005/api/voice/transcribe
```

**Response:**
```json
{
  "transcript": "check system status",
  "confidence": 0.95
}
```

**Example: Execute Voice Command**
```bash
curl -X POST \
  -H "X-API-Key: prime-spark-voice-key" \
  -F "file=@command.wav" \
  "http://localhost:8005/api/voice/command?session_id=user123"
```

**Response:**
```json
{
  "transcript": "check system status",
  "confidence": 0.95,
  "command": {
    "intent": "status_check",
    "action": "status",
    "target": "all",
    "confidence": 0.9
  },
  "result": {
    "success": true,
    "message": "All systems operational",
    "spoken_response": "All systems are operational"
  }
}
```

**Example: Synthesize Speech**
```bash
curl -X POST \
  -H "X-API-Key: prime-spark-voice-key" \
  "http://localhost:8005/api/voice/speak?text=Hello from Prime Spark" \
  --output response.wav
```

### WebSocket

```
WS     /ws/voice/stream                  # Real-time audio streaming
WS     /ws/voice/responses               # Real-time responses
```

---

## 🧠 COMMAND PARSING

The Voice Command Hub uses a hybrid parsing approach:

### 1. Pattern Matching (Fast)
For common commands, regex patterns provide instant recognition:
- "check status" → status_check intent
- "trigger workflow" → workflow_trigger intent
- "start agent" → agent_control intent

### 2. LLM-Based NLU (Flexible)
For complex or ambiguous commands, Ollama provides deep understanding:
- Context-aware interpretation
- Entity extraction (agent names, workflow IDs)
- Multi-step command planning
- Conversational follow-ups

### Intent Types

| Intent | Description | Example |
|--------|-------------|---------|
| `status_check` | Check agent/system status | "Check Pulse health" |
| `agent_control` | Start/stop/restart agents | "Restart AI Bridge" |
| `workflow_trigger` | Execute N8N workflows | "Trigger deployment" |
| `analysis_request` | Analyze content | "Summarize page 123" |
| `task_creation` | Create engineering tasks | "Create task: optimize" |
| `information_query` | Answer questions | "What's CPU usage?" |
| `help` | Get help | "What can you do?" |

---

## 🔗 AGENT INTEGRATION

### Pulse Agent Integration

```python
# Voice command: "Check Pulse health"

# Voice Hub calls:
response = requests.get("http://localhost:8001/pulse/health")

# Speaks response:
"Pulse agent is healthy. CPU usage 45%, memory 62%."
```

### AI Bridge Integration

```python
# Voice command: "Analyze latest Notion page"

# Voice Hub calls:
response = requests.post(
    "http://localhost:8002/bridge/analyze",
    json={"page_id": "latest"}
)

# Speaks response:
"Analysis complete. Found 5 key insights and 12 action items."
```

### N8N Hub Integration

```python
# Voice command: "Trigger deployment workflow"

# Voice Hub calls:
response = requests.post(
    "http://localhost:8004/api/n8n/execute/deployment",
    headers={"X-API-Key": "prime-spark-n8n-key"},
    json={"workflow_id": "deployment", "agent_id": "voice"}
)

# Speaks response:
"Deployment workflow started. Execution ID: exec_20251107_123456"
```

### Mobile Command Center Integration

```python
# Voice command: "Show all agents"

# Voice Hub calls:
response = requests.get(
    "http://localhost:8003/api/agents",
    headers={"Authorization": f"Bearer {jwt_token}"}
)

# Speaks response:
"5 agents online: Pulse is healthy, AI Bridge is healthy..."
```

---

## 🧪 TESTING

### Health Check

```bash
curl http://localhost:8005/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "whisper_available": true,
  "respeaker_found": true,
  "redis": "connected",
  "conversations": 0,
  "websocket_connections": 0
}
```

### Test Transcription

1. **Record audio:**
```bash
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_command.wav
# Say: "Check system status"
```

2. **Transcribe:**
```bash
curl -X POST \
  -H "X-API-Key: prime-spark-voice-key" \
  -F "file=@test_command.wav" \
  http://localhost:8005/api/voice/transcribe
```

3. **Expected:**
```json
{
  "transcript": "check system status",
  "confidence": 0.92
}
```

### Test Command Execution

```bash
curl -X POST \
  -H "X-API-Key: prime-spark-voice-key" \
  -F "file=@test_command.wav" \
  http://localhost:8005/api/voice/command
```

**Expected:**
```json
{
  "transcript": "check system status",
  "confidence": 0.92,
  "command": {
    "intent": "status_check",
    "action": "status",
    "target": "all"
  },
  "result": {
    "success": true,
    "message": "All systems operational",
    "spoken_response": "All systems are operational"
  }
}
```

### Test Text-to-Speech

```bash
curl -X POST \
  -H "X-API-Key: prime-spark-voice-key" \
  "http://localhost:8005/api/voice/speak?text=Hello%20from%20Prime%20Spark" \
  --output test_speech.wav

# Play audio
aplay test_speech.wav
```

---

## 🐛 TROUBLESHOOTING

### Voice Hub Not Starting

```bash
# Check logs
docker-compose logs voice-hub

# Common issues:
# 1. Audio devices not accessible
ls -l /dev/snd

# 2. User not in audio group
sudo usermod -aG audio $USER
# Logout and login again

# 3. Port 8005 already in use
sudo lsof -i :8005

# 4. Redis not connecting
docker-compose logs voice-redis
```

### Whisper Model Not Loading

**Problem:** "Whisper model not available" error

**Solutions:**
```bash
# 1. Check Whisper installation in container
docker-compose exec voice-hub python -c "import faster_whisper"

# 2. Check model download
docker-compose logs voice-hub | grep -i whisper

# 3. Try smaller model
# Edit .env: WHISPER_MODEL=tiny
docker-compose restart voice-hub

# 4. Clear model cache
docker-compose down
docker volume rm voice_interface_voice-recordings
docker-compose up -d
```

### Audio Devices Not Found

**Problem:** "ReSpeaker not found" or "No audio devices"

**Solutions:**
```bash
# 1. Check if ReSpeaker is connected
lsusb | grep -i audio

# 2. Check ALSA devices
aplay -l
arecord -l

# 3. Test recording manually
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav
aplay test.wav

# 4. Check Docker has audio access
docker-compose exec voice-hub ls -l /dev/snd

# 5. Restart container with --privileged
# (already in docker-compose.yml)
docker-compose restart voice-hub
```

### Transcription Fails or Poor Quality

**Problem:** Low confidence or incorrect transcription

**Solutions:**
```bash
# 1. Reduce background noise
# Move to quieter environment

# 2. Speak closer to microphone
# ReSpeaker optimal distance: 1-2 meters

# 3. Use larger Whisper model
# Edit .env: WHISPER_MODEL=small or medium
docker-compose restart voice-hub

# 4. Check audio quality
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 quality_test.wav
aplay quality_test.wav
# Should sound clear

# 5. Adjust VAD sensitivity
# (configured in whisper transcribe call)
```

### Piper TTS Not Working

**Problem:** "Piper model not found" or TTS fails

**Solutions:**
```bash
# 1. Check Piper installation
docker-compose exec voice-hub which piper
docker-compose exec voice-hub piper --version

# 2. Check voice model exists
docker-compose exec voice-hub ls -l /opt/piper/voices/

# 3. Test Piper manually
docker-compose exec voice-hub sh -c \
  'echo "Hello test" | piper --model /opt/piper/voices/en_US-lessac-medium.onnx --output_file /tmp/test.wav'

# 4. Use fallback TTS (espeak)
# Edit voice_hub.py: fallback is automatic

# 5. Download voice model manually
docker-compose exec voice-hub sh -c \
  'cd /opt/piper/voices && wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx'
```

### Command Not Recognized

**Problem:** Valid command not parsed correctly

**Solutions:**
```bash
# 1. Check Ollama is running
curl http://localhost:11434/api/tags

# 2. Test NLU directly
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:latest", "prompt": "Parse: check system status", "stream": false}'

# 3. Check command patterns
# View voice_hub.py:_build_command_patterns()

# 4. Add custom pattern
# Edit voice_hub.py and add to command_patterns

# 5. View parsing logs
docker-compose logs voice-hub | grep -i parse
```

---

## 🔐 SECURITY

### API Key Authentication

All API endpoints require API key:

```bash
curl -H "X-API-Key: prime-spark-voice-key" http://localhost:8005/api/voice/...
```

**Change Default API Key:**
```bash
# Edit .env
HUB_API_KEY=your-secure-key-here

# Restart
docker-compose restart voice-hub
```

### Audio Data Privacy

- Audio is processed locally (no cloud)
- Whisper runs on-device
- No audio sent to external services
- Temporary files deleted after processing

### Command Authorization

Consider implementing:
- User authentication
- Command whitelisting
- Critical command confirmation
- Audit logging

### Production Checklist

- [ ] Change default API keys
- [ ] Configure HTTPS/SSL (use reverse proxy)
- [ ] Restrict network access
- [ ] Enable command logging
- [ ] Set up monitoring
- [ ] Configure rate limiting
- [ ] Test emergency stop commands
- [ ] Document authorized commands
- [ ] Train users on voice commands
- [ ] Set up backup audio input

---

## 📈 MONITORING

### Application Logs

```bash
# View all logs
docker-compose logs -f

# Voice Hub only
docker-compose logs -f voice-hub

# Filter for errors
docker-compose logs voice-hub | grep -i error

# Filter for voice commands
docker-compose logs voice-hub | grep -i "Transcribed:"
```

### Metrics

```bash
# Get current metrics
curl http://localhost:8005/metrics
```

**Response:**
```json
{
  "total_conversations": 5,
  "active_websockets": 1,
  "whisper_backend": "faster-whisper",
  "whisper_model": "base"
}
```

### Audio Device Status

```bash
# List audio devices
aplay -l
arecord -l

# Test microphone
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav
aplay test.wav

# Test speakers
speaker-test -t wav -c 2
```

---

## 💡 USE CASES

### 1. Hands-Free Monitoring

Working on other tasks while monitoring infrastructure:

```
You: "Hey Spark, check system status"
Hub: "All systems operational. Pulse is healthy, AI Bridge is healthy, N8N Hub has 3 workflows running."

You: "What's the CPU usage on Pi 5?"
Hub: "CPU usage is 42 percent on Pi 5."

You: "Alert me if it goes above 80%"
Hub: "I'll watch CPU usage and alert you."
```

### 2. Voice-Driven Workflow Execution

Trigger workflows while mobile:

```
You: "Hey Spark, trigger deployment workflow"
Hub: "Deploying to staging. Execution ID exec_20251107_123456."

[2 minutes later]
Hub: "Deployment complete. All tests passed. Ready for production."

You: "Deploy to production"
Hub: "Deploying to production now."
```

### 3. Accessibility

For users with mobility limitations:

```
You: "Hey Spark, show me all agents"
Hub: "5 agents online: Pulse is healthy, AI Bridge is healthy, N8N Hub is healthy, Mobile Center is healthy, Engineering Team is idle."

You: "Restart AI Bridge"
Hub: "Restarting AI Bridge agent. Standby."

[30 seconds later]
Hub: "AI Bridge restarted successfully. Agent is healthy."
```

### 4. Multi-Tasking During Troubleshooting

Investigating issues hands-free:

```
You: "Hey Spark, what's the error rate?"
Hub: "Error rate is 2 percent over the last hour."

You: "Show me Pulse logs for the last 10 minutes"
Hub: "Found 15 log entries. 2 warnings, no errors."

You: "Run all health checks"
Hub: "Running health checks on all agents. This will take about 2 minutes."

[2 minutes later]
Hub: "Health checks complete. All agents passed except PrimeCore 3. High memory usage detected."

You: "Trigger memory cleanup workflow"
Hub: "Memory cleanup workflow started on PrimeCore 3."
```

### 5. Conversational Agent Control

Natural multi-turn conversations:

```
You: "Hey Spark, I need to deploy the new feature"
Hub: "Which environment? Staging or production?"

You: "Staging first"
Hub: "Deploying to staging. Shall I run tests after deployment?"

You: "Yes"
Hub: "Deployment to staging started with post-deployment tests. I'll notify you when complete."

[5 minutes later]
Hub: "Staging deployment complete. All tests passed. Ready for production deployment?"

You: "Yes, deploy to production"
Hub: "Deploying to production now."
```

---

## 🎯 ROADMAP

### Phase 2 (Coming Soon)

- [ ] Wake word detection (Porcupine, Snowboy)
- [ ] Voice authentication/speaker recognition
- [ ] Multi-user support
- [ ] Custom wake words
- [ ] Whisper Hailo-8 acceleration
- [ ] Conversation memory across sessions
- [ ] Voice command macros
- [ ] Interrupt/cancel support
- [ ] Background listening mode
- [ ] LED feedback (ReSpeaker LEDs)

### Phase 3 (Future)

- [ ] Multiple language support
- [ ] Emotion detection
- [ ] Voice activity playback
- [ ] Voice command history UI
- [ ] Mobile app integration
- [ ] Bluetooth audio support
- [ ] Voice biometrics
- [ ] Advanced NLU models
- [ ] Voice-controlled vim mode
- [ ] Voice coding assistant

---

## 📞 SUPPORT

### Common Commands

```bash
# Restart Voice Hub
docker-compose restart voice-hub

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Shell into container
docker-compose exec voice-hub bash

# Test audio in container
docker-compose exec voice-hub arecord -l
docker-compose exec voice-hub aplay -l

# Clear Redis cache
docker-compose exec voice-redis redis-cli -a PASSWORD FLUSHDB
```

### Quick Diagnostics

```bash
echo "=== Voice Hub Health ==="
curl -s http://localhost:8005/health | jq

echo -e "\n=== Container Status ==="
docker-compose ps

echo -e "\n=== Audio Devices ==="
ls -l /dev/snd

echo -e "\n=== ReSpeaker Detection ==="
lsusb | grep -i audio

echo -e "\n=== Recent Logs ==="
docker-compose logs --tail=20 voice-hub
```

---

## ✨ ALIGNMENT WITH PRIME SPARK VALUES

The Voice Command Hub embodies Prime Spark principles:

1. **Soul Before System** ✅
   - Natural voice interaction
   - Accessibility-first design
   - Human-centered UX

2. **Vision as Directive** ✅
   - Future-ready voice AI
   - Multimodal interaction
   - Hands-free operation

3. **Decentralize the Power** ✅
   - Control from anywhere
   - No centralized bottleneck
   - Distributed voice processing

4. **Creative Flow is Sacred** ✅
   - Frictionless interaction
   - No typing required
   - Intuitive commands

5. **Agents Are Archetypes** ✅
   - Voice Hub = "The Voice"
   - Conversational agent interface
   - Natural communication

---

## 🎯 READY TO USE!

The Voice Command Hub is **ready for deployment**!

### Quick Start

```bash
cd /home/pironman5/prime-spark-ai/voice_interface
./deploy.sh
```

Then say:
- **"Hey Spark, check system status"**
- **"Hey Spark, help"**

Access:
- **API**: http://localhost:8005
- **Docs**: http://localhost:8005/docs
- **Health**: http://localhost:8005/health

### First Steps

1. Deploy Voice Hub
2. Connect ReSpeaker microphone
3. Test audio: `arecord -l`
4. Say "Hey Spark, help"
5. Try voice commands
6. Integrate with agents

---

**Status**: 🟢 READY FOR DEPLOYMENT
**Version**: 1.0.0
**Built by**: Prime Spark Engineering Team
**Deployed**: 2025-11-07
**Location**: Raspberry Pi 5 @ `/home/pironman5/prime-spark-ai/voice_interface/`

⚡ **"Talk to your AI infrastructure naturally!"** ⚡
