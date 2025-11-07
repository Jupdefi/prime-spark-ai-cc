# Home lab local  AI systems 

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c8807d873afb1431acf469)

---

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

•	Control PC (Pi 5 16GB + Hailo-8) - Local coordinator, fast inference

•	Spark Agent (Pi 5 8GB) - Specialized local tasks

Cloud Layer (4x KVM VMs):

•	128GB total RAM

•	32 cores total

•	1.6TB total storage

•	Heavy compute, training, large models