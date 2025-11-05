# Prime Spark AI - System Architecture

## Overview

Prime Spark AI is a hybrid edge-cloud AI platform designed for resilient, privacy-first AI operations across distributed infrastructure.

---

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRIME SPARK AI PLATFORM                           │
│                    Hybrid Edge-Cloud AI Infrastructure                   │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                            EDGE LAYER (Homelab)
═══════════════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────────────────┐
│  NETWORK EDGE                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Pi4 OpenWRT Router (192.168.1.1)                                   │ │
│  │  • NAT & Firewall                                                   │ │
│  │  • VPN Port Forwarding (UDP 51820)                                  │ │
│  │  • QoS & Traffic Shaping                                            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼

┌─────────────────────────────────────────────────────────────────────────┐
│  COMPUTE NODES                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  CONTROL PC (Pi5 16GB + Hailo-8) - 192.168.1.100 | VPN 10.8.0.2  │ │
│  │  ────────────────────────────────────────────────────────────────│ │
│  │  • Main Coordinator & Orchestrator                                │ │
│  │  • AI Inference (Hailo-8: 13-26 TOPS)                            │ │
│  │  • VPN Server (WireGuard Hub)                                     │ │
│  │  • Redis Cache (Tier 1)                                           │ │
│  │  • API Gateway                                                    │ │
│  │  • Agent Coordinator                                              │ │
│  │  • Power Manager                                                  │ │
│  │                                                                    │ │
│  │  Services Running:                                                 │ │
│  │  • FastAPI (port 8000)                                            │ │
│  │  • Redis (port 6379)                                              │ │
│  │  • Ollama (port 11434)                                            │ │
│  │  • Prometheus Node Exporter (port 9100)                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  SPARK AGENT (Pi5 8GB) - 192.168.1.92 | VPN 10.8.0.3             │ │
│  │  ─────────────────────────────────────────────────────────────────│ │
│  │  • Voice & Task Execution Agent                                   │ │
│  │  • ReSpeaker USB 4 Mic Array                                      │ │
│  │    - 4 microphones with beamforming                               │ │
│  │    - Built-in AEC, VAD, DOA, noise suppression                    │ │
│  │  • Local Task Processing                                          │ │
│  │  • Agent Worker Node                                              │ │
│  │                                                                    │ │
│  │  Services Running:                                                 │ │
│  │  • Agent Worker (port 8000)                                       │ │
│  │  • Voice Processing                                               │ │
│  │  • Prometheus Node Exporter (port 9100)                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  STORAGE LAYER                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Argon EON NAS (192.168.1.49)                                      │ │
│  │  ───────────────────────────────────────────────────────────────  │ │
│  │  • 8TB Total Storage (4x 2TB NVMe)                                │ │
│  │  • Tier 2 Persistent Memory                                       │ │
│  │  • Shared Edge Storage                                            │ │
│  │  • Model Repository                                               │ │
│  │  • NFS/SMB File Sharing                                           │ │
│  │                                                                    │ │
│  │  Mount Point: /mnt/nas                                            │ │
│  │  Directories:                                                     │ │
│  │  • /mnt/nas/prime-spark-cache/  - Application cache              │ │
│  │  • /mnt/nas/models/            - AI models                        │ │
│  │  • /mnt/nas/data/              - Application data                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                        VPN TUNNEL (WireGuard)
═══════════════════════════════════════════════════════════════════════════

                    Encrypted UDP Tunnel (Port 51820)
                    Subnet: 10.8.0.0/24
                    • End-to-end encryption
                    • Automatic reconnection
                    • Health monitoring
                    • Persistent keepalive (25s)

═══════════════════════════════════════════════════════════════════════════
                            CLOUD LAYER (KVM VMs)
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATION HUB                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  VM1: PrimeCore1 (141.136.35.51) | VPN 10.8.0.11                  │ │
│  │  ─────────────────────────────────────────────────────────────────│ │
│  │  • OpenWebUI                                                       │ │
│  │  • Voice Studio                                                    │ │
│  │  • AutoGen Multi-Agent Framework                                  │ │
│  │  • Cloud Orchestration                                            │ │
│  │  • API Gateway (Optional Traefik)                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  MEMORY & STORAGE LAYER                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  VM2: PrimeCore2 | VPN 10.8.0.12                                  │ │
│  │  ─────────────────────────────────────────────────────────────────│ │
│  │  • Supabase (PostgreSQL + Realtime)                               │ │
│  │    - Vector embeddings                                            │ │
│  │    - Authentication                                               │ │
│  │    - Realtime subscriptions                                       │ │
│  │  • Nextcloud                                                       │ │
│  │    - File sync & share                                            │ │
│  │    - Collaborative editing                                        │ │
│  │  • Tier 3 Cloud Memory                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  VOICE PROCESSING LAYER                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  VM3: PrimeCore3 | VPN 10.8.0.13                                  │ │
│  │  ─────────────────────────────────────────────────────────────────│ │
│  │  • Speech-to-Text Services                                        │ │
│  │  • Text-to-Speech Services                                        │ │
│  │  • Voice Processing Pipeline                                      │ │
│  │  • Audio Analytics                                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SERVICE HUB (15+ Services)                                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  VM4: PrimeCore4 (69.62.123.97) | VPN 10.8.0.14                   │ │
│  │  ─────────────────────────────────────────────────────────────────│ │
│  │  Core Services:                                                    │ │
│  │  • Ollama (LLM Inference) - port 11434                            │ │
│  │  • ComfyUI (Image Generation)                                     │ │
│  │  • Code Server (VS Code Web)                                      │ │
│  │  • MinIO (S3 Storage) - port 9000                                 │ │
│  │  • TimescaleDB (Analytics) - port 5432                            │ │
│  │  • Kafka (Streaming) - port 9092                                  │ │
│  │  • Kafka UI - port 8080                                           │ │
│  │  • Airflow Web - port 8081                                        │ │
│  │  • Prometheus - port 9090                                         │ │
│  │  • Grafana - port 3000                                            │ │
│  │  • MLflow - port 5000                                             │ │
│  │  • Additional services...                                         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                      APPLICATION LAYER (All Nodes)
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  UNIFIED API LAYER (FastAPI)                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Endpoints (port 8000):                                                  │
│  ├─ /health              - Health checks                                │
│  ├─ /api/auth/*          - Authentication                               │
│  ├─ /api/llm/*           - LLM inference                                │
│  ├─ /api/memory/*        - Memory operations                            │
│  ├─ /api/tasks/*         - Agent tasks                                  │
│  ├─ /api/agents/*        - Agent coordination                           │
│  ├─ /api/power/*         - Power management                             │
│  ├─ /api/vpn/*           - VPN status                                   │
│  └─ /api/routing/*       - Routing stats                                │
│                                                                          │
│  Features:                                                               │
│  • JWT Authentication                                                    │
│  • Request/Response caching                                             │
│  • Automatic routing (edge/cloud)                                       │
│  • Rate limiting                                                        │
│  • OpenAPI documentation                                                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  INTELLIGENT ROUTING LAYER                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Routing Strategies:                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  1. EDGE-FIRST (Default)                                           ││
│  │     • Try edge compute first                                        ││
│  │     • Fallback to cloud if unavailable                             ││
│  │     • Best for privacy & low latency                               ││
│  │                                                                     ││
│  │  2. CLOUD-FIRST                                                     ││
│  │     • Prioritize cloud compute                                      ││
│  │     • Fallback to edge if unavailable                              ││
│  │     • Best for heavy workloads                                      ││
│  │                                                                     ││
│  │  3. BALANCED                                                        ││
│  │     • Choose lowest latency endpoint                                ││
│  │     • Dynamic load distribution                                     ││
│  │     • Best for mixed workloads                                      ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  Decision Factors:                                                       │
│  • Endpoint health & latency                                            │
│  • Power mode (on-grid / off-grid)                                      │
│  • Model availability                                                    │
│  • Current load                                                         │
│  • Network conditions                                                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  THREE-TIER MEMORY ARCHITECTURE                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  TIER 1: LOCAL CACHE (Redis)                                       ││
│  │  ─────────────────────────────────────────────────────────────────││
│  │  • Location: Control PC, Spark Agent                               ││
│  │  • Access Time: < 1ms                                              ││
│  │  • Capacity: 2GB per node                                          ││
│  │  • TTL: 5min - 1hour                                               ││
│  │  • Use: Hot data, frequent access                                  ││
│  │  • Eviction: LRU policy                                            ││
│  └────────────────────────────────────────────────────────────────────┘│
│                            ↓ Cache Miss                                  │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  TIER 2: NAS PERSISTENT STORAGE                                    ││
│  │  ─────────────────────────────────────────────────────────────────││
│  │  • Location: Argon EON NAS (192.168.1.49)                         ││
│  │  • Access Time: 5-20ms                                             ││
│  │  • Capacity: 8TB                                                   ││
│  │  • Persistence: Yes                                                ││
│  │  • Use: Shared edge storage, models                                ││
│  │  • Protocol: NFS/SMB                                               ││
│  └────────────────────────────────────────────────────────────────────┘│
│                            ↓ NAS Miss                                    │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  TIER 3: CLOUD STORAGE (MinIO + Supabase)                         ││
│  │  ─────────────────────────────────────────────────────────────────││
│  │  • Location: PrimeCore4 (MinIO), PrimeCore2 (Supabase)            ││
│  │  • Access Time: 50-200ms                                           ││
│  │  • Capacity: Unlimited (S3)                                        ││
│  │  • Persistence: Yes, with backup                                   ││
│  │  • Use: Long-term storage, archives                                ││
│  │  • Protocol: S3 API, PostgreSQL                                    ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  Automatic Backfill: Hit in T3 → Store in T2 + T1                       │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                      DATA STREAMING LAYER (Enterprise)
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  APACHE KAFKA (3-node cluster on PrimeCore4)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Topics & Data Flows:                                                    │
│                                                                          │
│  Edge → Cloud:                                                           │
│  ├─ edge.telemetry         - System metrics (CPU, RAM, disk)           │
│  ├─ edge.ai.inference      - AI inference results                       │
│  ├─ edge.sensors           - Sensor data streams                        │
│  └─ system.health          - Health check events                        │
│                                                                          │
│  Cloud → Edge:                                                           │
│  ├─ cloud.commands         - Control commands                           │
│  └─ models.updates         - Model update notifications                 │
│                                                                          │
│  Analytics:                                                              │
│  └─ analytics.events       - Processed analytics events                 │
│                                                                          │
│  Configuration:                                                          │
│  • Replication Factor: 3                                                │
│  • Partitions: 3 per topic                                              │
│  • Retention: 7 days                                                    │
│  • Compression: snappy                                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  TIMESCALEDB ANALYTICS                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Tables:                                                                 │
│  ├─ device_metrics         - Time-series system metrics                │
│  ├─ ai_inference_results   - ML inference tracking                      │
│  ├─ sensor_data            - High-frequency sensor readings             │
│  └─ analytics_events       - Business events                            │
│                                                                          │
│  Features:                                                               │
│  • Continuous aggregates (hourly, daily)                                │
│  • Automatic compression                                                │
│  • Data retention policies                                              │
│  • Hypertables for time-series optimization                             │
│                                                                          │
│  Performance:                                                            │
│  • Insert Rate: >100k rows/sec                                          │
│  • Query Speed: 10-100x faster than vanilla PostgreSQL                  │
│  • Compression: 90%+ on old data                                        │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                  DATA PIPELINE LAYER (Apache Airflow)
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  ETL ORCHESTRATION                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DAGs:                                                                   │
│  ├─ edge_to_cloud_sync     - Sync edge data (every 15 min)            │
│  ├─ analytics_aggregation  - Daily aggregations                         │
│  ├─ model_performance      - Model monitoring                           │
│  └─ data_quality           - Data quality checks                        │
│                                                                          │
│  Architecture:                                                           │
│  ├─ Webserver              - UI (port 8081)                            │
│  ├─ Scheduler              - DAG scheduling                             │
│  ├─ Workers                - Task execution (Celery)                    │
│  └─ Database               - PostgreSQL metadata store                  │
│                                                                          │
│  Features:                                                               │
│  • Retry logic with exponential backoff                                 │
│  • Task dependencies & parallelization                                  │
│  • SLA monitoring                                                       │
│  • Email/Slack alerts                                                   │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                      ML OPS LAYER (MLflow)
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  MODEL LIFECYCLE MANAGEMENT                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Workflow:                                                               │
│  1. Train → 2. Log → 3. Register → 4. Deploy → 5. Monitor              │
│                                                                          │
│  Components:                                                             │
│  ├─ Tracking Server        - Experiment tracking (port 5000)           │
│  ├─ Model Registry         - Versioned models                           │
│  ├─ Artifact Store         - Model artifacts (MinIO)                    │
│  └─ Backend Store          - Metadata (PostgreSQL)                      │
│                                                                          │
│  Features:                                                               │
│  • Experiment comparison                                                │
│  • Model versioning (Staging/Production)                                │
│  • ONNX export for edge deployment                                      │
│  • Automated deployment pipeline                                        │
│  • A/B testing framework                                                │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                    MONITORING & OBSERVABILITY LAYER
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  PROMETHEUS + GRAFANA                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Metrics Collection:                                                     │
│  ├─ System Metrics         - Node Exporter (all nodes)                 │
│  ├─ Application Metrics    - FastAPI custom metrics                     │
│  ├─ Database Metrics       - Postgres Exporter                          │
│  ├─ Kafka Metrics          - Kafka Exporter                            │
│  └─ Custom Metrics         - Business metrics                           │
│                                                                          │
│  Dashboards:                                                             │
│  ├─ System Overview        - All services health                        │
│  ├─ Edge Devices           - Edge node metrics                          │
│  ├─ AI Performance         - Model inference stats                      │
│  ├─ Kafka Metrics          - Streaming performance                      │
│  └─ API Performance        - API latency & throughput                   │
│                                                                          │
│  Alerting:                                                               │
│  • High CPU/Memory usage                                                │
│  • Service down                                                         │
│  • High error rates                                                     │
│  • Slow response times                                                  │
│  • Disk space low                                                       │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                        SECURITY & AUTHENTICATION
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│  SECURITY LAYERS                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Network Security:                                                       │
│  ├─ VPN Encryption         - WireGuard (ChaCha20-Poly1305)            │
│  ├─ Firewall               - UFW/iptables on all nodes                 │
│  └─ TLS/SSL                - Let's Encrypt certificates (production)    │
│                                                                          │
│  Application Security:                                                   │
│  ├─ JWT Authentication     - HS256 algorithm                            │
│  ├─ Password Hashing       - bcrypt                                     │
│  ├─ RBAC                   - Role-based access control                  │
│  └─ Rate Limiting          - Per-endpoint limits                        │
│                                                                          │
│  Data Security:                                                          │
│  ├─ At-Rest Encryption     - LUKS for sensitive volumes                │
│  ├─ In-Transit Encryption  - TLS for all communication                 │
│  └─ Secret Management      - Environment variables / Vault              │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                            DATA FLOW DIAGRAM
═══════════════════════════════════════════════════════════════════════════

   Edge Devices                                          Cloud VMs

   ┌──────────┐                                    ┌──────────────┐
   │ Sensors  │─┐                                  │ PrimeCore1   │
   └──────────┘ │                                  │ (Orchestr.)  │
                │  ┌──────────┐                    └──────────────┘
   ┌──────────┐ ├─►│  Kafka   │◄───────────────────────────┐
   │ Control  │ │  │ Topics   │                             │
   │ PC       │─┤  └──────────┘                             │
   └──────────┘ │       │                                   │
                │       ▼                            ┌──────────────┐
   ┌──────────┐ │  ┌──────────┐    ┌──────────┐   │ PrimeCore4   │
   │ Spark    │─┘  │Timescale │◄───│ Airflow  │   │ (Services)   │
   │ Agent    │    │   DB     │    │  DAGs    │   └──────────────┘
   └──────────┘    └──────────┘    └──────────┘            │
        │               │                │                  │
        │               ▼                ▼                  ▼
        │          ┌─────────────────────────────────────────┐
        └─────────►│     Analytics & ML Ops Pipeline         │
                   └─────────────────────────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────────┐
                   │     Grafana Dashboards & Alerts         │
                   └─────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
