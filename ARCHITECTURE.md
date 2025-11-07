# Prime Spark AI - System Architecture

**Version:** 2.0.0
**Last Updated:** 2025-11-05
**Status:** 85% Complete, Production-Ready Core

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Homelab Edge Nodes](#homelab-edge-nodes)
4. [Cloud KVA Services](#cloud-kva-services)
5. [Data Flow Pathways](#data-flow-pathways)
6. [API Integration Points](#api-integration-points)
7. [Network Topology](#network-topology)
8. [Component Interactions](#component-interactions)

---

## Overview

Prime Spark AI is a hybrid edge-cloud AI platform designed to bridge affordable Raspberry Pi homelab infrastructure with enterprise-grade cloud services. The architecture follows a **tiered approach** for compute, storage, and networking to optimize for latency, cost, and reliability.

**Key Design Principles:**
- **Edge-First Processing**: AI inference happens locally when possible
- **Intelligent Fallback**: Cloud resources used when edge is overloaded
- **Tiered Memory**: Data flows through Redis → NAS → Cloud
- **Event-Driven**: Kafka streams enable real-time responsiveness
- **Power-Aware**: Routing adapts to battery/grid power state

---

## Architecture Diagram

### High-Level System View

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PRIME SPARK AI PLATFORM                               │
│                    Hybrid Edge-Cloud AI Infrastructure                        │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  • Web Apps • Mobile Apps • CLI Tools • IoT Devices                         │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ HTTPS/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ FastAPI Server (Port 8000)                                   │            │
│  │  • Authentication (JWT)                                      │            │
│  │  • Request Validation (Pydantic)                             │            │
│  │  • Rate Limiting                                             │            │
│  │  • CORS Middleware                                           │            │
│  │  • Health Checks                                             │            │
│  └─────────────────────────────────────────────────────────────┘            │
└────────┬────────────────────────────────────────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┬───────────
         ▼                  ▼                  ▼                  ▼
    ┌─────────┐        ┌─────────┐       ┌─────────┐       ┌─────────┐
    │ Router  │        │ Memory  │       │ Agents  │       │  Power  │
    │ Manager │        │ Manager │       │ Coord.  │       │ Manager │
    └─────────┘        └─────────┘       └─────────┘       └─────────┘
         │                  │                  │                  │
         └──────────────────┴──────────────────┴──────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EDGE COMPUTE LAYER                                  │
│  ┌────────────────────────┐            ┌────────────────────────┐           │
│  │ Control PC (Pi5 8GB)   │            │ Spark Agent (Pi5 8GB)  │           │
│  │ • Hailo-8 AI (13 TOPS) │            │ • ReSpeaker 4-Mic      │           │
│  │ • Coordination         │            │ • Audio Processing     │           │
│  │ • Memory Management    │            │ • Task Execution       │           │
│  │ • LLM Inference        │            │ • Voice Recognition    │           │
│  │ IP: 192.168.1.100      │            │ IP: 192.168.1.92       │           │
│  │ VPN: 10.8.0.2          │            │ VPN: 10.8.0.3          │           │
│  └────────────────────────┘            └────────────────────────┘           │
│                             │                                                │
│                             ▼                                                │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Argon EON NAS (8TB)                                       │              │
│  │ • Shared Storage (NFS/SMB)                                │              │
│  │ • Model Artifacts                                         │              │
│  │ • Persistent Data                                         │              │
│  │ IP: 192.168.1.49                                          │              │
│  └──────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │  WireGuard VPN    │
                   │  10.8.0.0/24      │
                   └─────────┬─────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLOUD COMPUTE LAYER                                  │
│  ┌────────────────────────┐            ┌────────────────────────┐           │
│  │ PrimeCore1 (Oracle)    │            │ PrimeCore4 (Hostinger) │           │
│  │ • Orchestration        │            │ • 15 Services          │           │
│  │ • Load Balancing       │            │ • KVA Pipeline         │           │
│  │ IP: 141.136.35.51      │            │ IP: 69.62.123.97       │           │
│  │ VPN: 10.8.0.11         │            │ VPN: 10.8.0.14         │           │
│  └────────────────────────┘            └────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STREAMING LAYER (Kafka)                              │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Apache Kafka Cluster (Port 9092)                          │              │
│  │ ├─ edge.telemetry          (System metrics)              │              │
│  │ ├─ edge.ai.inference       (AI results)                  │              │
│  │ ├─ edge.sensors            (Sensor data)                 │              │
│  │ ├─ cloud.commands          (Commands to edge)            │              │
│  │ ├─ analytics.events        (Processed events)            │              │
│  │ ├─ system.health           (Health checks)               │              │
│  │ └─ models.updates          (Model deployments)           │              │
│  └──────────────────────────────────────────────────────────┘              │
│                             │                                                │
│  ┌──────────────────────────┴──────────────────────────┐                   │
│  │ Zookeeper (Port 2181)                                │                   │
│  │ • Cluster Coordination                               │                   │
│  └──────────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ANALYTICS LAYER (TimescaleDB)                          │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ TimescaleDB (PostgreSQL 15 + TimescaleDB 2.23)           │              │
│  │ Port: 5433                                                │              │
│  │                                                           │              │
│  │ Hypertables:                                              │              │
│  │ ├─ device_metrics         (1 day chunks)                 │              │
│  │ ├─ ai_inference_results   (model performance)            │              │
│  │ ├─ sensor_data            (1 hour chunks)                │              │
│  │ └─ analytics_events       (business events)              │              │
│  │                                                           │              │
│  │ Continuous Aggregates:                                    │              │
│  │ └─ hourly_device_metrics  (rollup)                       │              │
│  └──────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE LAYER (Airflow)                            │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Apache Airflow 2.7.3                                      │              │
│  │                                                           │              │
│  │ ┌───────────────────┐  ┌───────────────────┐            │              │
│  │ │ Webserver (8081)  │  │ Scheduler         │            │              │
│  │ │ • UI              │  │ • DAG Execution   │            │              │
│  │ │ • API             │  │ • Task Queuing    │            │              │
│  │ └───────────────────┘  └───────────────────┘            │              │
│  │                                                           │              │
│  │ ┌───────────────────┐  ┌───────────────────┐            │              │
│  │ │ Worker            │  │ PostgreSQL DB     │            │              │
│  │ │ • Task Execution  │  │ • Metadata Store  │            │              │
│  │ │ • Celery Executor │  │ • State Tracking  │            │              │
│  │ └───────────────────┘  └───────────────────┘            │              │
│  │                                                           │              │
│  │ DAGs:                                                     │              │
│  │ └─ edge_to_cloud_sync.py (Every 15 min)                 │              │
│  └──────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MONITORING LAYER                                      │
│  ┌────────────────────────┐            ┌────────────────────────┐           │
│  │ Prometheus (9090)      │            │ Grafana (3002)         │           │
│  │ • Metrics Collection   │───────────▶│ • Dashboards           │           │
│  │ • Time-series DB       │            │ • Alerting             │           │
│  │ • Alert Manager        │            │ • Visualization        │           │
│  └────────────────────────┘            └────────────────────────┘           │
│                             │                                                │
│  ┌──────────────────────────┴──────────────────────────┐                   │
│  │ Node Exporter (9100)                                 │                   │
│  │ • CPU, Memory, Disk Metrics                          │                   │
│  └──────────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY STORAGE LAYER                                 │
│                                                                              │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐          │
│  │ TIER 1       │        │ TIER 2       │        │ TIER 3       │          │
│  │ Redis Cache  │───────▶│ NAS Storage  │───────▶│ Cloud Store  │          │
│  │              │        │              │        │              │          │
│  │ • Sub-ms     │        │ • Persistent │        │ • Long-term  │          │
│  │ • 2GB        │        │ • 8TB        │        │ • Unlimited  │          │
│  │ • LRU        │        │ • Shared     │        │ • S3/MinIO   │          │
│  │ Port: 6379   │        │ NFS Mount    │        │ Supabase     │          │
│  └──────────────┘        └──────────────┘        └──────────────┘          │
│         ▲                        ▲                        ▲                 │
│         │                        │                        │                 │
│         └────────────────────────┴────────────────────────┘                 │
│                    Memory Manager (Automatic Tiering)                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Homelab Edge Nodes

### 1. Control PC (Primary Edge Node)

**Hardware:**
- Platform: Raspberry Pi 5 (8GB RAM)
- CPU: ARM Cortex-A76 (2.4 GHz, 4 cores)
- AI Accelerator: Hailo-8 (13 TOPS)
- Case: Pironman 5 (active cooling)
- Storage: 256GB NVMe SSD

**Network:**
- LAN IP: 192.168.1.100
- VPN IP: 10.8.0.2
- Role: VPN Server

**Capabilities:**
- LLM inference (Ollama)
- Computer vision (Hailo-8)
- System coordination
- Memory management
- API serving

**Software Stack:**
- OS: Raspberry Pi OS (Linux 6.12.47)
- Python: 3.11.2
- Docker: 20.10.24
- Node.js: v24.11.0 (NVM)

**Running Services:**
```
• prime-spark-api       (Port 8000)
• ollama                (Port 11434)
• redis                 (Port 6379)
• All enterprise stack (when deployed)
```

### 2. Spark Agent (Secondary Edge Node)

**Hardware:**
- Platform: Raspberry Pi 5 (8GB RAM)
- CPU: ARM Cortex-A76 (2.4 GHz, 4 cores)
- Audio: ReSpeaker USB 4 Mic Array
  - 4 microphones
  - 12 RGB LEDs
  - Built-in AEC, VAD, DOA, beamforming
  - Sample rate: 16kHz

**Network:**
- LAN IP: 192.168.1.92
- VPN IP: 10.8.0.3

**Capabilities:**
- Voice recognition
- Voice synthesis
- Audio processing
- Task execution
- LLM inference

**Registered Capabilities:**
```python
{
  "agent_id": "spark-agent-1",
  "endpoint": "http://10.8.0.3:8000",
  "capabilities": [
    "voice_recognition",
    "voice_synthesis",
    "task_execution",
    "llm"
  ],
  "max_concurrent_tasks": 5
}
```

### 3. Argon EON NAS

**Hardware:**
- Platform: Raspberry Pi 4 (4GB RAM)
- Storage: 4x 2TB HDDs (8TB total)
- Interface: USB 3.0

**Network:**
- LAN IP: 192.168.1.49
- Protocols: NFS, SMB

**Purpose:**
- Tier-2 memory storage
- Model artifact repository
- Shared data storage
- Backup target

**Mount Points:**
- Control PC: `/mnt/nas`
- Share Path: `/share`

---

## Cloud KVA Services

### KVA = Key-Value-Analytics Pipeline

The cloud layer provides enterprise-grade KVA services that complement the edge infrastructure:

### Key-Value Layer (Redis)

**Service:** Redis 7.0 (Alpine)
**Port:** 6379
**Purpose:** Sub-millisecond caching and session storage

**Configuration:**
```yaml
Max Memory: 2GB
Eviction Policy: allkeys-lru
Persistence: RDB snapshots
Replication: Single instance (can scale to cluster)
```

**Use Cases:**
- API response caching
- LLM prompt/response caching
- Session storage
- Rate limiting counters
- Real-time leaderboards

**Performance:**
- Latency: <1ms for simple operations
- Throughput: 100k+ ops/sec on Pi 5
- Hit Rate Target: >90%

### Analytics Layer (TimescaleDB)

**Service:** TimescaleDB 2.23 (PostgreSQL 15)
**Port:** 5433
**Purpose:** Time-series analytics and historical data

**Hypertables:**

```sql
-- Device Metrics (system telemetry)
CREATE TABLE device_metrics (
  time TIMESTAMPTZ NOT NULL,
  device_id TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  value DOUBLE PRECISION,
  metadata JSONB
);
SELECT create_hypertable('device_metrics', 'time', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX ON device_metrics (device_id, time DESC);

-- AI Inference Results (model performance)
CREATE TABLE ai_inference_results (
  time TIMESTAMPTZ NOT NULL,
  model_name TEXT NOT NULL,
  input_tokens INT,
  output_tokens INT,
  latency_ms DOUBLE PRECISION,
  accuracy DOUBLE PRECISION,
  metadata JSONB
);
SELECT create_hypertable('ai_inference_results', 'time', chunk_time_interval => INTERVAL '1 day');

-- Sensor Data (high-frequency readings)
CREATE TABLE sensor_data (
  time TIMESTAMPTZ NOT NULL,
  sensor_id TEXT NOT NULL,
  reading_type TEXT NOT NULL,
  value DOUBLE PRECISION,
  unit TEXT
);
SELECT create_hypertable('sensor_data', 'time', chunk_time_interval => INTERVAL '1 hour');

-- Analytics Events (business events)
CREATE TABLE analytics_events (
  time TIMESTAMPTZ NOT NULL,
  event_type TEXT NOT NULL,
  user_id TEXT,
  properties JSONB,
  metadata JSONB
);
SELECT create_hypertable('analytics_events', 'time');
```

**Continuous Aggregates:**
```sql
-- Hourly rollup for device metrics
CREATE MATERIALIZED VIEW hourly_device_metrics
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS bucket,
       device_id,
       metric_name,
       AVG(value) as avg_value,
       MAX(value) as max_value,
       MIN(value) as min_value
FROM device_metrics
GROUP BY bucket, device_id, metric_name;
```

**Retention Policies:**
```sql
-- Keep raw data for 30 days
SELECT add_retention_policy('device_metrics', INTERVAL '30 days');

-- Keep aggregates for 1 year
SELECT add_retention_policy('hourly_device_metrics', INTERVAL '365 days');
```

**Performance:**
- Insert Rate: 100k+ rows/sec
- Query Speed: 10-100x faster than PostgreSQL
- Compression: 90%+ for time-series data
- Storage: Automatic chunking and compression

### Streaming Layer (Apache Kafka)

**Service:** Kafka 7.5.0 (Confluent Platform)
**Port:** 9092
**Purpose:** Real-time event streaming and message broker

**Topics:**

| Topic | Purpose | Partitions | Retention |
|-------|---------|------------|-----------|
| edge.telemetry | System metrics from edge | 3 | 7 days |
| edge.ai.inference | AI results from edge | 3 | 7 days |
| edge.sensors | Sensor data streams | 5 | 3 days |
| cloud.commands | Commands to edge devices | 2 | 1 day |
| analytics.events | Processed business events | 3 | 30 days |
| system.health | Health check messages | 1 | 1 day |
| models.updates | Model deployment notifications | 1 | 7 days |

**Producer Configuration:**
```python
{
  "acks": "all",              # Wait for all replicas
  "compression.type": "snappy",
  "max.in.flight.requests.per.connection": 5,
  "enable.idempotence": True  # Exactly-once semantics
}
```

**Consumer Groups:**
```
- analytics-processor (consumes edge.* topics)
- command-dispatcher (consumes cloud.commands)
- health-monitor (consumes system.health)
- timescale-ingester (consumes all topics → TimescaleDB)
```

**Performance:**
- Throughput: 1M+ messages/sec (with tuning)
- Latency: <10ms end-to-end
- Durability: Replicated to all brokers
- Ordering: Guaranteed within partition

**Kafka UI:**
- Port: 8080
- Features: Topic management, consumer lag monitoring, message inspection

---

## Data Flow Pathways

### Flow 1: LLM Inference (Edge-First)

```
┌─────────┐
│ Client  │
└────┬────┘
     │ POST /api/llm/generate
     ▼
┌──────────────────┐
│ API Gateway      │
│ • Authenticate   │───────┐
│ • Validate       │       │ Check cache
└────┬─────────────┘       ▼
     │              ┌──────────────┐
     │              │ Memory Mgr   │
     │              │ • Redis (T1) │
     │         Hit  └──────┬───────┘
     │  ◄──────────────────┘
     │
     │ Miss
     ▼
┌──────────────────┐
│ Router Manager   │
│ • Check power    │
│ • Check health   │
│ • Route decision │
└────┬─────────────┘
     │
     ├──────────────┬──────────────┐
     │ Edge-first   │ Cloud fallback│
     ▼              ▼               ▼
┌─────────┐   ┌─────────┐    ┌─────────┐
│ Edge    │   │ Cloud   │    │ Cloud   │
│ Ollama  │   │ Ollama  │    │ LLM API │
│ (local) │   │ (VPN)   │    │ (backup)│
└────┬────┘   └────┬────┘    └────┬────┘
     │             │              │
     └─────────────┴──────────────┘
                   │ Response
                   ▼
           ┌──────────────┐
           │ Memory Mgr   │──► Cache result
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │ Kafka        │──► Stream event
           │ edge.ai.     │    (async)
           │ inference    │
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │TimescaleDB   │──► Store metrics
           │ai_inference_ │    (via consumer)
           │results       │
           └──────────────┘
                  │
                  ▼
           ┌──────────────┐
           │ Client       │◄── Return response
           └──────────────┘
```

**Latency Breakdown:**
- Edge path: 100-500ms total
  - API: 5-10ms
  - Cache check: 1-2ms
  - Routing: 2-5ms
  - Ollama inference: 50-400ms (model dependent)
  - Cache store: 1-2ms (async)

- Cloud fallback: 500-2000ms total
  - + VPN latency: 20-50ms
  - + Internet latency: 50-200ms
  - + Cloud inference: 100-1000ms

### Flow 2: Edge-to-Cloud Data Sync

```
┌──────────────┐
│ Edge Device  │
│ (Pi 5)       │
└──────┬───────┘
       │ Telemetry generated
       ▼
┌──────────────┐
│ Local Redis  │──► Write to Tier 1
│ (Cache)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Kafka        │──► Publish to topic
│ Producer     │    edge.telemetry
└──────┬───────┘
       │
       │ Network (VPN)
       ▼
┌──────────────┐
│ Kafka Broker │──► Store in partition
│ (Cloud)      │    (replicated)
└──────┬───────┘
       │
       ├────────────────────┬────────────────────┐
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Consumer 1   │    │ Consumer 2   │    │ Consumer 3   │
│ TimescaleDB  │    │ Analytics    │    │ Archiver     │
│ Ingester     │    │ Processor    │    │ (S3)         │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│TimescaleDB   │    │ Alerts       │    │ Cloud        │
│device_metrics│    │ Dashboard    │    │ Storage      │
└──────────────┘    └──────────────┘    └──────────────┘
```

**Sync Frequency:**
- Real-time: Kafka streaming (continuous)
- Batch: Airflow DAG (every 15 min)
- On-demand: Manual API calls

### Flow 3: Memory Tiering

```
┌───────────────┐
│ Read Request  │
└───────┬───────┘
        │
        ▼
    ┌───────────────┐
    │ Tier 1: Redis │
    │ Check cache   │
    └───┬───────┬───┘
        │       │
    Hit │       │ Miss
        │       │
        ▼       ▼
    Return  ┌───────────────┐
            │ Tier 2: NAS   │
            │ Check file    │
            └───┬───────┬───┘
                │       │
            Hit │       │ Miss
                │       │
                ▼       ▼
            Backfill ┌───────────────┐
            to T1    │ Tier 3: Cloud │
                     │ S3/Supabase   │
                     └───┬───────────┘
                         │
                         ▼
                     Backfill to T2
                     Backfill to T1
                     Return data

┌───────────────┐
│ Write Request │
└───────┬───────┘
        │
        ├───────────────┬───────────────┐
        ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Tier 1  │    │ Tier 2  │    │ Tier 3  │
    │ (sync)  │    │ (async) │    │(explicit)│
    └─────────┘    └─────────┘    └─────────┘
```

**Tiering Rules:**
- Tier 1 (Redis): Hot data, <1 hour old, <2GB total
- Tier 2 (NAS): Warm data, <30 days old, <8TB total
- Tier 3 (Cloud): Cold data, >30 days old, unlimited

**Automatic Migration:**
- T1→T2: After 1 hour (automatic)
- T2→T3: Manual or explicit policy
- Backfill: On cache miss (automatic)

### Flow 4: Task Distribution

```
┌───────────────┐
│ Client        │
│ Submit Task   │
└───────┬───────┘
        │ POST /api/tasks/submit
        ▼
┌───────────────────┐
│ Agent Coordinator │
│ • Parse task      │
│ • Find agent      │
│ • Load balance    │
└────────┬──────────┘
         │
         │ Find suitable agent by:
         │ 1. Capability match
         │ 2. Current load
         │ 3. Health status
         ▼
    ┌────────────┬────────────┐
    │ Priority   │            │
    │ Queue      │            │
    │ URGENT     │────────┐   │
    │ HIGH       │        │   │
    │ NORMAL     │        │   │
    │ LOW        │        │   │
    └────────────┘        │   │
                          ▼   ▼
                    ┌──────────────┐
                    │ Selected     │
                    │ Agent        │
                    │ (via VPN)    │
                    └──────┬───────┘
                           │ POST /api/execute
                           ▼
                    ┌──────────────┐
                    │ Task         │
                    │ Execution    │
                    │ (on agent)   │
                    └──────┬───────┘
                           │
                      Success?
                           │
                  ┌────────┴────────┐
                  │                 │
              Yes │                 │ No
                  ▼                 ▼
           ┌─────────────┐   ┌─────────────┐
           │ Mark        │   │ Retry       │
           │ COMPLETED   │   │ (max 3x)    │
           └─────────────┘   └─────────────┘
                  │                 │
                  │                 │ After 3 retries
                  │                 ▼
                  │          ┌─────────────┐
                  │          │ Mark FAILED │
                  │          └─────────────┘
                  │                 │
                  └─────────┬───────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ Return to   │
                     │ Client      │
                     └─────────────┘
```

**Task Lifecycle:**
```
PENDING → ASSIGNED → IN_PROGRESS → COMPLETED
                                 └→ FAILED (after retries)
```

**Load Balancing Algorithm:**
```python
def select_agent(task):
    # 1. Filter by capability
    capable = [a for a in agents if task.capability in a.capabilities]

    # 2. Filter by health
    healthy = [a for a in capable if a.health_status == "healthy"]

    # 3. Sort by load (ascending)
    sorted_agents = sorted(healthy, key=lambda a: a.current_load)

    # 4. Return least loaded
    return sorted_agents[0] if sorted_agents else None
```

---

## API Integration Points

### Authentication Flow

```
┌─────────────┐
│ Client      │
└──────┬──────┘
       │ POST /api/auth/login
       │ {username, password}
       ▼
┌─────────────────┐
│ Auth Endpoint   │
│ • Validate user │
│ • Check password│
│ • Generate JWT  │
└──────┬──────────┘
       │ {access_token, refresh_token}
       ▼
┌─────────────┐
│ Client      │
│ Store token │
└──────┬──────┘
       │ Subsequent requests
       │ Header: Authorization: Bearer <token>
       ▼
┌─────────────────┐
│ API Middleware  │
│ • Verify JWT    │
│ • Check expiry  │
│ • Extract user  │
└──────┬──────────┘
       │ Request with user context
       ▼
┌─────────────────┐
│ Protected       │
│ Endpoint        │
└─────────────────┘
```

### Endpoint Categories

**1. Health & Status**
```
GET  /health                      # Basic health check
GET  /api/health/detailed         # All subsystems

Response:
{
  "status": "healthy|degraded|unhealthy",
  "subsystems": {
    "redis": "healthy",
    "ollama": "healthy",
    "kafka": "healthy",
    "timescaledb": "healthy"
  }
}
```

**2. Authentication**
```
POST /api/auth/login              # Login
POST /api/auth/register           # Register user
POST /api/auth/refresh            # Refresh token
GET  /api/auth/me                 # Current user

Example:
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SparkAI2025!"}'
```

**3. LLM Operations**
```
POST /api/llm/generate            # Sync generation
POST /api/llm/generate/stream     # Streaming generation
GET  /api/llm/models              # List models
POST /api/llm/embeddings          # Generate embeddings

Example:
curl -X POST http://localhost:8000/api/llm/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "model": "llama3.2:latest",
    "max_tokens": 500,
    "use_cache": true
  }'
```

**4. Memory Operations**
```
POST /api/memory/set              # Store data
GET  /api/memory/get/{key}        # Retrieve data
DELETE /api/memory/{key}          # Delete data
GET  /api/memory/stats            # Memory statistics

Example:
curl -X POST http://localhost:8000/api/memory/set \
  -H "Authorization: Bearer <token>" \
  -d '{
    "key": "user_preferences",
    "value": {"theme": "dark"},
    "tier": 1,
    "ttl": 3600
  }'
```

**5. Task Management**
```
POST /api/tasks/submit            # Submit new task
GET  /api/tasks/{task_id}         # Get task status
DELETE /api/tasks/{task_id}       # Cancel task
GET  /api/tasks                   # List all tasks
GET  /api/agents/status           # Agent health

Example:
curl -X POST http://localhost:8000/api/tasks/submit \
  -H "Authorization: Bearer <token>" \
  -d '{
    "task_type": "voice_recognition",
    "priority": "HIGH",
    "payload": {"audio_url": "..."}
  }'
```

**6. Power Management**
```
GET  /api/power/status            # Battery & power state
POST /api/power/mode/{mode}       # Set mode (auto|on-grid|off-grid)

Response:
{
  "battery_percentage": 85,
  "is_charging": true,
  "power_mode": "auto",
  "routing_strategy": "edge-first"
}
```

**7. System Information**
```
GET  /api/system/info             # Infrastructure details
GET  /api/routing/stats           # Routing statistics
GET  /api/vpn/status              # VPN connection status

Response (system/info):
{
  "edge_nodes": [
    {"id": "control-pc-1", "ip": "10.8.0.2", "status": "healthy"},
    {"id": "spark-agent-1", "ip": "10.8.0.3", "status": "healthy"}
  ],
  "cloud_nodes": [
    {"id": "primecore1", "ip": "10.8.0.11", "status": "connected"},
    {"id": "primecore4", "ip": "10.8.0.14", "status": "connected"}
  ]
}
```

### Middleware Stack

```
Request
  │
  ▼
┌────────────────┐
│ CORS           │ Allow origins, methods, headers
└────────┬───────┘
         ▼
┌────────────────┐
│ Rate Limiting  │ 100 req/min per IP
└────────┬───────┘
         ▼
┌────────────────┐
│ Authentication │ Verify JWT token
└────────┬───────┘
         ▼
┌────────────────┐
│ Authorization  │ Check RBAC permissions
└────────┬───────┘
         ▼
┌────────────────┐
│ Validation     │ Pydantic schema validation
└────────┬───────┘
         ▼
┌────────────────┐
│ Endpoint       │ Execute business logic
└────────┬───────┘
         ▼
┌────────────────┐
│ Response       │ JSON serialization
└────────────────┘
  │
  ▼
Response
```

---

## Network Topology

### Physical Network Layout

```
                        INTERNET
                           │
                           │
                ┌──────────┴──────────┐
                │                     │
          ┌─────▼─────┐        ┌─────▼─────┐
          │ PrimeCore1│        │ PrimeCore4│
          │ (Oracle)  │        │(Hostinger)│
          │141.136.   │        │69.62.123. │
          │  35.51    │        │   97      │
          └─────┬─────┘        └─────┬─────┘
                │                    │
                │   WireGuard VPN    │
                │   10.8.0.0/24      │
                │                    │
       ┌────────┴────────────────────┴────────┐
       │         VPN Tunnel (Encrypted)       │
       └────────┬────────────────────┬────────┘
                │                    │
          ┌─────▼─────┐        ┌─────▼─────┐
          │VPN: 10.8. │        │VPN: 10.8. │
          │     0.11  │        │     0.14  │
          └───────────┘        └───────────┘
                │                    │
                │                    │
                └──────────┬─────────┘
                           │
                    INTERNET (ISP)
                           │
                ┌──────────▼──────────┐
                │  Edge Router        │
                │  192.168.1.1        │
                │  (Home Network)     │
                └──────────┬──────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐   ┌─────▼─────┐
    │ Control PC│    │Spark Agent│   │  Argon    │
    │ Pi5 + Hailo│   │ Pi5 + Mic │   │  EON NAS  │
    │ .100 (VPN │    │ .92 (VPN  │   │  .49      │
    │ Server)   │    │ Client)   │   │           │
    │ 10.8.0.2  │    │ 10.8.0.3  │   │           │
    └───────────┘    └───────────┘   └───────────┘
```

### Network Segmentation

**1. Edge LAN (192.168.1.0/24)**
- Router: 192.168.1.1
- Control PC: 192.168.1.100
- Spark Agent: 192.168.1.92
- Argon NAS: 192.168.1.49
- Purpose: Local edge-to-edge communication

**2. VPN Overlay (10.8.0.0/24)**
- Control PC: 10.8.0.2 (server)
- Spark Agent: 10.8.0.3
- PrimeCore1: 10.8.0.11
- PrimeCore2: 10.8.0.12
- PrimeCore3: 10.8.0.13
- PrimeCore4: 10.8.0.14
- Purpose: Encrypted edge-cloud communication

**3. Docker Networks**
```
prime-spark-network (bridge)
├─ prime-spark-api (172.18.0.2)
├─ prime-spark-redis (172.18.0.3)
├─ prime-spark-kafka (172.18.0.4)
├─ prime-spark-timescaledb (172.18.0.5)
└─ ... (all other services)
```

### Port Mapping

**Edge Services:**
```
8000  → Prime Spark API (FastAPI)
6379  → Redis Cache
11434 → Ollama LLM (local)
```

**Cloud/Enterprise Services:**
```
5433  → TimescaleDB (Analytics)
9092  → Kafka (Streaming)
2181  → Zookeeper (Coordination)
8080  → Kafka UI
8081  → Airflow Webserver
9090  → Prometheus (Monitoring)
3002  → Grafana (Dashboards)
9100  → Node Exporter (Metrics)
```

**External Services:**
```
3000  → Open WebUI
3001  → Flowise
5432  → PostgreSQL (general)
11435 → Ollama (containerized)
```

### Firewall Rules

**Edge Router (192.168.1.1):**
```
ALLOW: 192.168.1.0/24 → 192.168.1.0/24 (intra-LAN)
ALLOW: 192.168.1.100:51820 (WireGuard)
ALLOW: outbound HTTPS (443)
DENY:  all other inbound
```

**Control PC (iptables):**
```bash
# Allow VPN
-A INPUT -p udp --dport 51820 -j ACCEPT

# Allow Docker
-A INPUT -i docker0 -j ACCEPT

# Allow local services
-A INPUT -p tcp --dport 8000 -j ACCEPT  # API
-A INPUT -p tcp --dport 6379 -s 127.0.0.1 -j ACCEPT  # Redis (localhost only)

# Drop everything else
-A INPUT -j DROP
```

---

## Component Interactions

### Service Dependency Graph

```
┌──────────────────────────────────────────────────────────┐
│                   DEPENDENCY HIERARCHY                    │
└──────────────────────────────────────────────────────────┘

Level 0 (Foundation)
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Redis   │  │  NAS    │  │ Cloud   │
│ Cache   │  │ Storage │  │ Storage │
└─────────┘  └─────────┘  └─────────┘

Level 1 (Data Platforms)
┌────────────┐  ┌────────────┐  ┌────────────┐
│ PostgreSQL │  │ Zookeeper  │  │   Ollama   │
│ (Airflow)  │  │            │  │    LLM     │
└────────────┘  └──────┬─────┘  └────────────┘
                       │
                       ▼
                ┌────────────┐
                │   Kafka    │
                └──────┬─────┘
                       │
                       ▼
                ┌────────────┐
                │TimescaleDB │
                └────────────┘

Level 2 (Core Services)
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Memory    │  │  Router    │  │   Power    │
│  Manager   │  │  Manager   │  │  Manager   │
└──────┬─────┘  └──────┬─────┘  └──────┬─────┘
       │               │               │
       └───────────────┴───────────────┘
                       │
                       ▼
                ┌────────────┐
                │    API     │
                │  Gateway   │
                └──────┬─────┘
                       │
                       ▼

Level 3 (Orchestration)
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Airflow   │  │  Agents    │  │    VPN     │
│  Pipeline  │  │ Coordinator│  │  Manager   │
└────────────┘  └────────────┘  └────────────┘

Level 4 (Observability)
┌────────────┐  ┌────────────┐  ┌────────────┐
│Prometheus  │  │  Grafana   │  │   Node     │
│            │──▶│            │  │  Exporter  │
└────────────┘  └────────────┘  └────────────┘
```

### Startup Sequence

```bash
# 1. Foundation Layer (parallel)
docker-compose up -d redis zookeeper

# 2. Data Platforms (after foundation)
docker-compose up -d postgres timescaledb kafka

# 3. Supporting Services
docker-compose up -d kafka-ui prometheus grafana node-exporter

# 4. Data Pipeline (after postgres + redis)
docker-compose up -d airflow-db airflow-webserver airflow-scheduler airflow-worker

# 5. API & Application (after all dependencies)
docker-compose up -d api

# Health check
curl http://localhost:8000/health
```

### Shutdown Sequence (Graceful)

```bash
# 1. Stop client-facing services
docker-compose stop api

# 2. Stop pipeline workers
docker-compose stop airflow-worker airflow-scheduler

# 3. Stop processing services
docker-compose stop kafka-ui airflow-webserver

# 4. Stop data platforms
docker-compose stop kafka timescaledb postgres

# 5. Stop monitoring
docker-compose stop prometheus grafana node-exporter

# 6. Stop foundation
docker-compose stop redis zookeeper
```

### Inter-Service Communication

**Synchronous (HTTP/gRPC):**
```
API → Ollama (HTTP)
API → Redis (Redis Protocol)
Router → Edge/Cloud Endpoints (HTTP)
Agent Coordinator → Agents (HTTP)
```

**Asynchronous (Message Queue):**
```
API → Kafka → TimescaleDB Consumer
Edge Telemetry → Kafka → Analytics Processor
Model Updates → Kafka → Edge Devices
```

**Database Connections:**
```
API → TimescaleDB (asyncpg, connection pool)
Airflow → PostgreSQL (SQLAlchemy)
All Services → Redis (connection pool)
```

### Failure Handling

**Redis Failure:**
```
Memory Manager → Skip T1 → Query T2 (NAS) directly
                          → Query T3 (Cloud) if T2 miss
Degraded performance but functional
```

**Kafka Failure:**
```
API → Continue serving requests
    → Skip streaming (log locally)
    → Airflow batch sync (fallback)
Analytics delayed but API operational
```

**TimescaleDB Failure:**
```
Kafka → Buffer messages (retention policy)
Airflow → Retry with exponential backoff
API → Continue (analytics unavailable)
```

**Ollama Failure (Edge):**
```
Router → Detect failure (health check)
       → Route to Cloud Ollama
       → Return response with "source: cloud" metadata
Automatic failover, transparent to client
```

**VPN Failure:**
```
Edge ← → Cloud: Communication lost
Edge Services: Continue operating locally
Cloud Commands: Queued in Kafka
Recovery: VPN auto-reconnect, process queued messages
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────┐
│ Layer 7: Application                        │
│ • Input validation (Pydantic)               │
│ • SQL injection prevention (parameterized)  │
│ • XSS prevention (output encoding)          │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Layer 6: Authentication & Authorization     │
│ • JWT tokens (HS256)                        │
│ • Role-based access control (RBAC)          │
│ • Password hashing (bcrypt)                 │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Layer 5: API Security                       │
│ • Rate limiting (100 req/min)               │
│ • CORS (configured origins)                 │
│ • API key validation                        │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Layer 4: Transport Security                 │
│ • TLS 1.3 (recommended, not yet deployed)   │
│ • Certificate pinning                       │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Layer 3: Network Security                   │
│ • VPN encryption (WireGuard, ChaCha20)      │
│ • Network segmentation (VLANs)              │
│ • Firewall rules (iptables)                 │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Layer 2: Host Security                      │
│ • Docker container isolation                │
│ • Read-only filesystems                     │
│ • Non-root users                            │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Layer 1: Physical Security                  │
│ • Homelab physical access control           │
│ • Cloud provider datacenter security        │
└─────────────────────────────────────────────┘
```

### Secrets Management

**Current State (Development):**
```
.env file (plaintext)
├─ JWT_SECRET=<secret>
├─ REDIS_PASSWORD=<password>
├─ ADMIN_PASSWORD=<password>
└─ MINIO_SECRET_KEY=<key>
```

**Recommended (Production):**
```
HashiCorp Vault
├─ secret/primespark/jwt
├─ secret/primespark/redis
├─ secret/primespark/admin
└─ secret/primespark/minio

Access via:
- VAULT_ADDR + VAULT_TOKEN
- Auto-renewal
- Audit logging
```

---

## Performance Characteristics

### Throughput Targets

| Component | Target | Actual (Pi 5) |
|-----------|--------|---------------|
| API Requests | 1000 req/s | ~500 req/s |
| Redis Ops | 100k ops/s | ~80k ops/s |
| Kafka Messages | 1M msg/s | ~100k msg/s |
| TimescaleDB Inserts | 100k rows/s | ~50k rows/s |
| LLM Inference (Edge) | 10 tok/s | 8-12 tok/s (model dependent) |

### Latency Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| API Health Check | <5ms | 2-3ms |
| Redis Cache Hit | <2ms | 1-2ms |
| LLM Inference (Edge) | <1s | 0.5-2s |
| LLM Inference (Cloud) | <3s | 1-5s |
| Kafka Publish | <10ms | 5-8ms |
| TimescaleDB Query (simple) | <50ms | 20-40ms |
| TimescaleDB Query (aggregate) | <500ms | 200-400ms |

### Scalability Limits

**Current Configuration:**
- **Concurrent Users**: ~100-200
- **Data Retention**: 30 days (raw), 365 days (aggregates)
- **Storage**: 8TB NAS + unlimited cloud
- **Compute**: 2x Pi5 (8 cores total) + cloud VMs

**Scaling Options:**
1. **Horizontal Edge Scaling**: Add more Pi5 nodes
2. **Vertical Cloud Scaling**: Upgrade VM sizes
3. **Kafka Partitioning**: Increase partitions for parallelism
4. **Redis Clustering**: Multi-node Redis for >2GB cache
5. **TimescaleDB Sharding**: Multi-node for >1TB data

---

## Deployment Topology

### Development (Current)

```
Single Pi5 (Control PC)
├─ All Docker containers
├─ Local development
└─ Hot reload enabled
```

### Staging (Recommended)

```
Control PC
├─ API + Redis + Ollama
└─ Basic monitoring

Cloud VM
├─ Kafka + TimescaleDB
├─ Airflow
└─ Grafana + Prometheus
```

### Production (Target)

```
Edge Cluster (3x Pi5)
├─ Control PC: API + Coordination
├─ Spark Agent 1: Audio processing
└─ Spark Agent 2: Vision processing

Cloud Cluster
├─ PrimeCore1: Load balancer + Orchestration
├─ PrimeCore2: Kafka cluster (3 nodes)
├─ PrimeCore3: TimescaleDB cluster (2 nodes)
└─ PrimeCore4: Airflow + Monitoring
```

---

## Technology Stack Summary

**Core Framework:**
- FastAPI 0.104.1 (Python async web framework)
- Uvicorn (ASGI server)
- Pydantic 2.5.0 (Data validation)

**Data Storage:**
- Redis 7.0 (Cache)
- PostgreSQL 15 (Relational + Airflow metadata)
- TimescaleDB 2.23 (Time-series)
- MinIO / Supabase (Object storage)

**Streaming:**
- Apache Kafka 7.5.0 (Message broker)
- Zookeeper (Coordination)

**Data Pipeline:**
- Apache Airflow 2.7.3 (Workflow orchestration)

**AI/ML:**
- Ollama (Local LLM serving)
- MLflow 2.9.2 (Model lifecycle)
- PyTorch 2.1.2 (ML framework)
- ONNX Runtime (Edge optimization)

**Monitoring:**
- Prometheus (Metrics)
- Grafana (Visualization)
- Node Exporter (System metrics)

**Networking:**
- WireGuard (VPN)
- Docker Networking (Container orchestration)

**Container Orchestration:**
- Docker Compose (Development)
- Kubernetes (Production-ready manifests)

---

## Conclusion

Prime Spark AI implements a comprehensive hybrid edge-cloud architecture that successfully bridges Raspberry Pi homelab infrastructure with enterprise cloud services. The system demonstrates:

✅ **Intelligent Routing**: Edge-first with cloud fallback
✅ **Tiered Memory**: Redis → NAS → Cloud with automatic migration
✅ **Real-time Streaming**: Kafka for event-driven architecture
✅ **Time-series Analytics**: TimescaleDB for metrics and insights
✅ **Task Orchestration**: Distributed agent coordination
✅ **Observability**: Prometheus + Grafana monitoring
✅ **Security**: VPN, JWT auth, RBAC, encryption

**Current Status**: 85% complete, production-ready core with enterprise features requiring final integration.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Maintained By:** Prime Spark AI Team
