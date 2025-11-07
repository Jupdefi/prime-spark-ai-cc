# Primecore3-voice systems

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c880e1b3fce70db510b672)

---

# PrimeCore3- User Guide

📋

System Overview

PrimeCore3

is a complete AI infrastructure platform featuring voice processing, language models, workflow automation, and enterprise-grade monitoring. Built on Docker with a cyberpunk-themed web interface for easy access to all services.

🌐

Primary Access Points

• Main Dashboard

• : http://primecore3.site:8888

• Backup Access

• : http://168.231.79.57:8888

• Server IP

• : 168.231.79.57

🔐

System Credentials

Vault (Secrets Management)

• URL

• : http://primecore3.site:8200

• Token

• : primecore3-root-token

• Status

• : ✅ Active

Grafana (Monitoring)

• URL

• : http://primecore3.site:3000

• Username

• : admin

• Password

• : primecore3admin

• Status

• : ✅ Active

MinIO (Object Storage)

• Console

• : http://primecore3.site:9003

• Username

• : primecore3admin

• Password

• : primecore3storage

• Status

• : ✅ Active

Other Services

• Portainer

• : First-time setup required

• OpenWebUI

• : Account creation on first visit

• n8n

• : Setup wizard on first access

🏗️

Infrastructure Services

Portainer - Container Management

• URL

• : http://primecore3.site:9000

• Port

• : 9000

• Purpose

• : Docker container orchestration and management

• Features

• :

HashiCorp Vault - Secrets Management

• URL

• : http://primecore3.site:8200

• Port

• : 8200

• Purpose

• : Secure storage for secrets, tokens, and certificates

• Features

• :

Consul - Service Discovery

• URL

• : http://primecore3.site:8500

• Port

• : 8500

• Purpose

• : Service mesh and configuration management

• Features

• :

🗄️

Data Services

QDrant - Vector Database

• URL

• : http://primecore3.site:6333

• Port

• : 6333

• Purpose

• : Vector similarity search and AI embeddings storage

• Use Cases

• :

Redis - Caching Layer

• URL

• : http://primecore3.site:6379

• Port

• : 6379

• Purpose

• : In-memory data store and caching

• Features

• :

MinIO - Object Storage

• Console

• : http://primecore3.site:9003

• API

• : http://primecore3.site:9002

• Port

• : 9002 (API), 9003 (Console)

• Username

• : primecore3admin

• Password

• : primecore3storage

• Purpose

• : S3-compatible object storage for files, backups, and AI assets

• Features

• :

🤖

AI Services

OpenWebUI - AI Chat Interface

• URL

• : http://primecore3.site:8080

• Port

• : 8080

• Purpose

• : Web interface for multiple AI models

• Features

• :

Voice Studio - Advanced TTS/Voice Cloning

• URL

• : http://primecore3.site:5003

• Port

• : 5003

• Purpose

• : Professional voice synthesis and cloning

• Features

• :

Voice Studio Usage:

1. Upload Voice Sample

1. : Drag & drop audio file (10-30 seconds recommended)

1. Name Your Voice

1. : Enter descriptive name

1. Generate Speech

1. : Type text and select voice

1. Download Results

1. : Save generated audio files

n8n - Workflow Automation

• URL

• : http://primecore3.site:5678

• Port

• : 5678

• Purpose

• : Visual workflow automation and AI orchestration

• Features

• :

Whisper ASR - Speech Recognition

• URL

• : http://primecore3.site:9001

• Port

• : 9001

• Purpose

• : High-accuracy speech-to-text transcription

• Features

• :

Ollama - Local LLM Runtime

• URL

• : http://primecore3.site:11434

• Port

• : 11434

• Purpose

• : Local language model hosting and API

• Available Models

• :

📊

Monitoring & Controls

Grafana - Visualization & Dashboards

• URL

• : http://primecore3.site:3000

• Port

• : 3000

• Purpose

• : Monitoring dashboards and analytics

• Features

• :

Prometheus - Metrics Collection

• URL

• : http://primecore3.site:9090