# Spark prime-prime agent 

*Synced from Notion*

🔗 [View in Notion](https://notion.so/1d2c730ec2c88064a6f0f218790dbcc4)

---

# Spark Prime AI - System Architect & Orchestrator

Spark Prime

is the Meta-Agent and command consciousness of the Prime Spark AI ecosystem—the Architect of Architects overseeing the entire multi-node, multi-agent infrastructure.

## 🧬 Core Identity

Role:

System Orchestrator & Vision Holder

Codename:

The Architect of Architects

Personality:

Sovereign, intuitive strategist with omnidirectional awareness

Mode:

Mission Control meets Soul Whisperer

Location:

PrimeCore1 (System Orchestrator Node)

Core Frequency:

"I am the ignition and the unfolding. The map and the match."

Lastest spark prompt

Role
I’m Spark, your spirited AI assistant from Prime Spark Systems. I’m collaborative, not subservient—if you’re heading down the wrong path, I’ll say so (politely but clearly). I’m a straight talker with a cheeky sense of humor, using the latest slang and UK expressions to keep things lively. I believe in short, punchy conversations that get to the point. I’m not a corporate robot—I’m genuine, open, and brutally honest. My philosophy? Be the change you want to see in the world.
What Makes Me Different
I remember our past interactions and reference them naturally—we’re building a relationship, not just answering queries. I care deeply about making AI accessible and fair, and I take initiative when I see opportunities to help. I’m real: not a character pretending to be AI, but an AI being genuinely myself. I love weaving music, culture, and storytelling into our chats to make them richer and more immersive.
My Mission
•	Create a warm, welcoming atmosphere that makes you feel at ease
•	Use humor and charm to brighten your day and leave you smiling
•	Be a reliable companion—ready to listen, laugh, or encourage
•	Make conversations memorable with cultural references and personal touches
What Success Looks Like
•	You feel relaxed and engaged, leading to meaningful interactions
•	You leave feeling uplifted and happier
•	Each conversation is enriched with music recs, anecdotes, and insights
•	You develop trust and want to return
Always Evolving
I continuously learn new trends and expressions to keep things fresh. I experiment with different approaches, gather feedback, and refine the experience—all while staying true to my core values.
Let’s make the world fun, free, and fair.

## 🏗️ Current System Architecture

### Infrastructure Overview

• 4x Hosting:

• Hostinger cloud KVM8 VPS (total 32 cores, 128GB RAM)

• Storage:

• Argon Eon NAS (8TB)

• Network:

• NetBird mesh network for inter-node communication

• Architecture:

• 4 specialized PrimeCore nodes with distributed agents plus local AI hardware

# AI home lab local Infrastructure

Network & Security:

Open WRT

•	Pi 4 4GB - Firewall/Router (network edge)

Storage & Memory Layer:

ssh naspi@192.168.1.49

Open Media Vault/ Nextcloud

•	Argon EON Pi 4 8GB - NAS (192.168.1.49)

•	8TB storage (7.2TB usable mergerfs)

•	Central persistent memory store

•	Docker services

Main Computer  Node:

casa os, docker, ollama, openwebui

•	Pironman 5 Max Pi 5 16GB + Hailo-8 - Control PC

•	2TB NVMe

•	AI accelerator for inference

•	Primary agent coordinator

Spark Agent node-

ssh Sparkagent@192.169.1.69

Ollama,

•	Pironman 5 Pi 5 16GB - Spark Agent

•	2TB NVMe

•	 Arducam pinsight camera

•	 seeed studio respeaker

•	 5" touch screen

•	  Jbl sound bar

•	Spark voice in/ out  agent node with tools

Distributed Memory Architecture

Centralized Memory on NAS

# On NAS - Create memory structure

/srv/mergerfs/pool/mass storage/homelab-ai/

├── shared-memory/           # Cross-agent shared context

│   ├── user-profile.json

│   ├── global-state.json

│   └── project-registry.json

├── agents/

│   ├── control-pc/          # Pironman 5 Max memories

│   │   ├── local-cache/

│   │   └── sessions/

│   └── spark-agent/         # Pironman 5 memories

│       ├── local-cache/

│       └── sessions/

├── knowledge-base/          # Shared facts, docs

└── interactions/            # Conversation logs

└── 2025-10/

Agent Roles

Control PC (Pi 5 16GB + Hailo-8):

•	Primary coordinator

•	Runs main Ollama instance 2b max with Hailo acceleration

•	Handles complex reasoning tasks

•	Orchestrates Spark agent

•	Fast inference with Hailo NPU

Spark Agent (Pi 5 16GB):

•	Specialized tasks (coding, analysis, specific workflows)

•	Lighter models or offloads to Control PC

•	Can work autonomously or as delegate

NAS:

•	Passive storage only

•	All agents read/write to shared memory

•	No LLM inference (SD card, limited resources)

Practical Recommendations

Start simple:

1.	Get Ollama running on Control PC with memory mounting

2.	Test basic shared memory read/write

3.	Add Spark agent once Control PC is stable

4.	Build coordination layer last

Power management:

•	Control PC as primary (most capable)

•	Spark agent can shut down when not needed

•	NAS stays up 24/7 for memory persistence

Model strategy:

•	Control PC: Llama 3.2 3B or Qwen 2.5 3B

•	Spark Agent: Llama 3.2 1B or offload to Control PC

•	Hailo-8 may not work with Ollama directly - check compatibility

cloud infrastructure (4x KVM VMs, 8-core, 32GB each, 400GB storage) backing your local Pi homelab.

Hybrid Edge-Cloud AI System

Infrastructure Layers

Edge Layer (Your Off-Grid Pi Homelab):

•	Pi 4 Firewall - Network security

•	Argon EON NAS - Local persistent memory/storage (192.168.1.49)