# Primecore2-memory 

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c880419bf1ed8d62a9966a)

---

# Primecore2 User Guide

Neural Infrastructure Control Matrix

Version:

1.0

Last Updated:

July 13, 2025

Server IP:

147.93.84.82

VPS Provider:

Hostinger

• NetBird: Native (host service), connected to mesh network

• IP: 100.98.113.7, FQDN: primesandbox.netbird.cloud

• Setup key: 37331438-20ED-41B8-889B-B44BA4CD4B16

🎯

QUICK ACCESS DASHBOARD

Main Dashboard:

http://147.93.84.82:8090

Core Service URLs

• Supabase Studio:

• http://147.93.84.82:8000

• Open WebUI:

• http://147.93.84.82:3000

• n8n Workflows:

• http://147.93.84.82:5678

• Nextcloud:

• http://147.93.84.82:8080

• Portainer:

• http://147.93.84.82:9000

• Prometheus:

• http://147.93.84.82:9090

• Grafana:

• http://147.93.84.82:3001

🏗️

SYSTEM ARCHITECTURE

Directory Structure

/primecore2/

├── infrastructure/          # Core infrastructure services

│   ├── caddy/              # Reverse proxy and SSL

│   ├── consul/             # Service discovery

│   └── vault/              # Secret management

├── infrastructure_data/     # Backup and data management

│   └── backups/            # Automated daily backups (2 AM)

├── data_layer/             # Database and storage services

│   ├── supabase/           # PostgreSQL + real-time features

│   ├── redis/              # In-memory cache

│   └── nextcloud/          # File storage and sharing

├── ai_services/            # AI and ML services

│   ├── ollama/             # Local LLM runtime

│   ├── open-webui/         # AI chat interface

│   └── n8n/                # Workflow automation

├── controls/               # Monitoring and observability

│   ├── prometheus/         # Metrics collection

│   └── grafana/            # Dashboard and visualization

└── web/                    # Web dashboard interface

└── index.html          # Main dashboard

Network Architecture

• Network Name:

• primecore2-network

• Type:

• Docker bridge network

• All services connected:

• Yes

• External access:

• Port-based routing

🔐

CREDENTIALS AND ACCESS

Default Credentials

n8n Workflow Automation

• URL: http://147.93.84.82:5678

• Username: admin

• Password: primecore2024!

Grafana Monitoring

• URL: http://147.93.84.82:3001

• Username: admin

• Password: primecore2024!

Supabase Studio

• URL: http://147.93.84.82:8000

• Access: Direct (no auth configured)

Important:

Change default passwords in production!

📋

SERVICE DESCRIPTIONS

Infrastructure Layer

🐳

Portainer (Port 9000)

Purpose:

Container management and orchestration

Usage:

• View all running containers

• Manage Docker services

• Monitor resource usage

• Deploy new services via GUI

🏛️

Consul (Port 8500)

Purpose:

Service discovery and configuration management

Usage:

• Service registration

• Health checking

• Key-value store for configuration

🔐

Vault (Port 8200)

Purpose:

Secrets and identity management

Usage:

• Store API keys and passwords

• Manage certificates

• Access control

🌐

NetBird

Purpose:

Zero-trust network access

Management:

Via primecore1 (managed externally)

Data Layer

🗄️

Supabase (Port 8000)

Purpose:

PostgreSQL database with real-time features

Usage:

• Database management via Studio

• Real-time subscriptions

• Row-level security

• Auto-generated APIs

⚡

Redis (Port 6379)

Purpose:

In-memory data store and caching

Usage:

• Session storage

• Cache layer

• Message queuing

• Real-time data

☁️

Nextcloud (Port 8080)

Purpose:

File sharing and collaboration

Usage:

• File upload/download

• Document collaboration

• Calendar and contacts

• App ecosystem

AI Services

💬

Open WebUI (Port 3000)

Purpose:

AI chat interface with multiple model support

Features:

• Multiple LLM model access