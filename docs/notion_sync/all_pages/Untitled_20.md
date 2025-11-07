# Untitled_20

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c881bfba59c23c0e2875e8)

---

# 📡 Prime Spark Infrastructure Hub

Complete technical infrastructure documentation for your Prime Spark AI ecosystem

## 🎯

## System Overview

Your Prime Spark project runs on a

hybrid edge-cloud infrastructure

with seamless coordination between local and remote systems.

## 🔧

## Active Infrastructure

### 🍀 Raspberry Pi 5 (Edge)

Specifications:

• CPU

• : ARM Cortex-A76 (4 cores)

• RAM

• : 16GB

• OS

• : Pi OS (Debian-based)

• Network

• : Netbird mesh VPN

Services Running:

• Whisper + Piper (Voice AI)

• Docker containers

• Claude Code CLI

• Local AI models

Location

:

/home/pi/prime-spark-*

### ☁️ VPS (Cloud)

Provider

: Hostinger

Plan

: KVM 8

Specifications:

• CPU

• : 8 cores

• RAM

• : 32GB

• Storage

• : 400GB SSD

• OS

• : Ubuntu 24.04

• Location

• : Manchester, UK

Domain

:

primecore1.online

IP

:

46.202.194.118

Active Services (29+ containers):

### Infrastructure Stack

### (

### /root/infrastructure/

### )

• Traefik (reverse proxy)

• Redis (caching)

• RabbitMQ (message queue)

### AI Workbench

### (

### /root/ai-workbench/

### )

• Ollama (LLM server)

• Open-WebUI (AI interface)

• N8N (automation)

• Code-Server (web IDE)

• Edge-TTS (text-to-speech)

### Data Stack

### (

### /root/supabase-stack/

### )

• Supabase (database + auth)

• PostgreSQL + pgvector

• Qdrant (vector database)

• Nextcloud (file storage)

• MariaDB

## 🌐

## Network Architecture

```javascript
iPhone (Mobile)
    │
    ↓
Notion (Deployment Hub)
    │
    ↑↓
    ├───> Pi 5 (Edge) ←─ Netbird mesh
    │
    └───> VPS (Cloud) ←─ primecore1.online
```

## 🚀

## Deployment System

### Claude Code Services

### (Notion-based)

Workflow:

1. Create MCP/script in Claude chat

1. I write directly to Notion

1. You review on iPhone

1. Pi pulls from Notion API

1. Auto-deploys to infrastructure

Databases:

• MCP Servers

• Deployment Scripts

• Documentation & Guides

Link:

🤖 Claude Code Services

## 📊

## Service URLs

### VPS Services:

• Dashboard

• :

• http://46.202.194.118:9999

• Open-WebUI

• :

• http://primecore1.online:8080

• N8N

• :

• http://primecore1.online:8085

• Nextcloud

• :

• http://primecore1.online:8090

• Code-Server

• :

• http://primecore1.online:8443

### Monitoring:

• Portainer

• : (if installed)

• System Stats

• : Dashboard at :9999

## 🛡️

## Security & Access

• Netbird VPN

• : Secure mesh network

• SSH Access

• : Via key authentication

• API Tokens

• : Notion, OpenRouter, etc.

• Container Isolation

• : Docker networks

## 📝

## Management Scripts

## 🔄

## N8N Automation Workflows

N8N Dashboard

:

http://primecore1.online:8085

### Active Workflows

### 1. Notion Sync to Pi

Purpose

: Automatically sync new deployments from Claude Code Services to Pi 5

Trigger

: Notion database update (Claude Code Services)

Actions

:

1. Detect new "Ready to Deploy" MCP

1. Send webhook to Pi

1. Pi executes deployment script

1. Update status back to Notion

Status

: 🟡 Planned (not yet implemented)

### 2. Infrastructure Health Monitor