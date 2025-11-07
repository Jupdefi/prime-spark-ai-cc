# Primecore1-orchestration

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c880a3bf4cf4b0a8da956b)

---

# Primecore1 User Guide

Main interface-

http://141.136.35.51:8080/dashboard/

🎯

System Overview

PrimeCore1 is your complete AI infrastructure platform running on Ubuntu 24.04.2 LTS with 8 cores, 32GB RAM, and 400GB storage. It provides a comprehensive suite of AI services, development tools, and data management capabilities.

Server Details:

• URL: primecore1.site

• IP: 141.136.35.51

• Network: Docker network primecore1 (172.20.0.0/16)

🌐

Service Access Points

Primary AI Interfaces

AI Services

Data & Storage

Infrastructure & Monitoring

📁

Updated Root Structure

/root-primecore1/

├── infrastructure/  # Core infrastructure

│   ├── caddy/        # NEW: Simple reverse proxy

│   ├── vault/               # Secrets management

│   ├── consul/              # Service discovery

│   ├── monitoring/      # Prometheus + Grafana

│   └── networking/      # Docker network config

├── data-layer/       # Data storage and manag

├── ai-services/             # AI and ML services

│   ├── autogen-studio/     # NEW: Multi-agent

│   ├── ollama/             # LLM server

│   ├── openwebui/          # Primary AI interface

│   └── n8n                    # automation

├── control/        # Management and autom

├── userspace/          # User projects and data

├── DEPLOYMENT_COMPLETE.md

└── ACCESS_POINTS.md         # Service access information

🏗️

Updated Infrastructure Layer

Caddy (Reverse Proxy)

/root-primecore1/infrastructure/caddy/

├── docker-compose.yml       # Simple Caddy configuration

├── Caddyfile               # Routing rules

└── logs/                   # Access logs

Key Benefits:

• ✅ Simple configuration (no complex SSL setup)

• ✅ Automatic HTTPS (when needed)

• ✅ Path-based routing

• ✅ Better performance than Traefik

Other Infrastructure Components

/root-primecore1/infrastructure/

├── vault/

│   ├── docker-compose.yml       # HashiCorp Vault

│   ├── vault.hcl               # Vault configuration

│   └── vault-keys.json         # Vault initialization keys (secure!)

├── consul/

│   ├── docker-compose.yml       # Service discovery

│   └── consul.hcl              # Consul configuration

├── monitoring/

│   ├── docker-compose.yml       # Prometheus + Grafana

│   └── prometheus.yml          # Metrics configuration

└── networking/

└── network-config.yml       # Docker network definitions

🤖

Enhanced AI Services Layer

New AutoGen Studio

/root-primecore1/ai-services/autogen-studio/

├── docker-compose.yml       # Multi-agent platform

├── workspace/              # Agent configurations

├── sessions/              # Chat sessions

└── skills/                # Custom agent skills

Capabilities:

• 🤖

• Multi-agent workflows

• - Coordinate multiple AI agents

• 🔧

• Local LLM integration

• - Uses your Ollama models

• 🎨

• Visual workflow builder

• - Drag & drop agent design

• 💬

• Real-time collaboration

• - Multiple agents working together

Core AI Services

/root-primecore1/ai-services/

├── ollama/

│   └── docker-compose.yml       # LLM server (OpenAI API compatible)

├── openwebui/

│   └── docker-compose.yml     # Primary AI

├── whisper/

│   └── docker-compose.yml    # Speech-to-text

├── n8n/

│   └── docker-compose.yml     # Workflow auto

├── mlflow/

│   ├── docker-compose.yml       # ML experiment tracking

│   └── mlruns/                 # Experiment data

├── minio/

│   └── docker-compose.yml    # Object storage

└── llamaparse/

├── docker-compose.yml     # Document pdf

├── app/

│   └── main.py       # LlamaParse application

├── uploads/                # Document uploads

└── output/                 # Processed documents

🧠

Available AI Models

Large Language Models (via Ollama)

# Available models - optimized selection

mistral:7b-instruct     # Best for: General chat, reasoning

deepseek-coder:6.7b    # Best for: Programming, code generation

llama3.2:3b            # Best for: Quick responses, lightweight

phi:2.7b               # Best for: Fast inference, efficiency