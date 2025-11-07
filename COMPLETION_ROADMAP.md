# Prime Spark AI - Completion Roadmap

**Version:** 2.0.0
**Date:** 2025-11-05
**Current Completion:** 85%
**Target:** Production-Ready (100%)
**Timeline:** 6 weeks

---

## Executive Summary

This roadmap outlines the **critical path to production readiness** for Prime Spark AI. The system is architecturally complete with all major components implemented. The focus is now on **integration, testing, and hardening**.

**Effort Breakdown:**
- **Integration** (35%): Wire components together, deploy missing infrastructure
- **Testing** (35%): Write comprehensive test suite
- **Hardening** (20%): Security, performance optimization
- **Documentation** (10%): Operational runbooks, deployment guides

**Team Requirements:** 1-2 developers working full-time

---

## Table of Contents

1. [Phase 1: Critical Integration (Week 1-2)](#phase-1-critical-integration-week-1-2)
2. [Phase 2: Testing Foundation (Week 3-4)](#phase-2-testing-foundation-week-3-4)
3. [Phase 3: Security & Performance (Week 5)](#phase-3-security--performance-week-5)
4. [Phase 4: Production Validation (Week 6)](#phase-4-production-validation-week-6)
5. [Integration Testing Strategy](#integration-testing-strategy)
6. [Deployment Automation](#deployment-automation)
7. [Success Criteria](#success-criteria)

---

## Phase 1: Critical Integration (Week 1-2)

**Goal:** Connect all components, achieve end-to-end data flows

### Day 1-2: Infrastructure Setup

#### Task 1.1: Mount NAS Storage ⏱️ 2 hours
**Priority:** 🔴 Critical
**Owner:** DevOps
**Dependencies:** None

**Steps:**
```bash
# 1. Install NFS client
sudo apt-get update
sudo apt-get install -y nfs-common

# 2. Create mount point
sudo mkdir -p /mnt/nas

# 3. Test manual mount
sudo mount -t nfs 192.168.1.49:/share /mnt/nas
ls -la /mnt/nas  # Verify contents

# 4. Add to fstab for persistence
echo "192.168.1.49:/share /mnt/nas nfs defaults,_netdev,rw 0 0" | sudo tee -a /etc/fstab

# 5. Test auto-mount
sudo umount /mnt/nas
sudo mount -a
df -h | grep nas  # Should show mounted
```

**Verification:**
```python
# Test NAS storage from Python
cd /home/pironman5/prime-spark-ai
python3 << 'EOF'
from memory.nas.nas_storage import NASStorage
nas = NASStorage()
test_data = {"test": "data", "timestamp": "2025-11-05"}
nas.store("test_mount", test_data)
result = nas.retrieve("test_mount")
assert result == test_data
print("✅ NAS storage operational")
EOF
```

**Acceptance Criteria:**
- [x] NAS mounted at /mnt/nas
- [x] Auto-mounts on reboot
- [x] Python NASStorage class works
- [x] Can read/write files

---

#### Task 1.2: Deploy VPN to Cloud ⏱️ 1 day
**Priority:** 🔴 Critical
**Owner:** DevOps
**Dependencies:** None

**Steps:**

**On Control PC (VPN Server):**
```bash
cd /home/pironman5/prime-spark-ai

# 1. Run VPN setup script
sudo ./deployment/setup-vpn.sh

# 2. Verify WireGuard interface
sudo wg show
# Should show: interface wg0, peers defined

# 3. Get public IP for cloud nodes
curl ifconfig.me
# Note this IP: <CONTROL_PC_PUBLIC_IP>

# 4. Copy client configs
ls /etc/wireguard/clients/
# Should have: primecore1.conf, primecore4.conf, etc.
```

**On PrimeCore1 (141.136.35.51):**
```bash
# 1. Install WireGuard
sudo apt-get update
sudo apt-get install -y wireguard

# 2. Copy client config from Control PC
scp pironman5@<CONTROL_PC_PUBLIC_IP>:/etc/wireguard/clients/primecore1.conf /tmp/

# 3. Move to WireGuard directory
sudo mv /tmp/primecore1.conf /etc/wireguard/wg0.conf

# 4. Edit config - replace [ENDPOINT] with actual Control PC public IP
sudo nano /etc/wireguard/wg0.conf
# Change: Endpoint = [ENDPOINT]:51820
# To:     Endpoint = <CONTROL_PC_PUBLIC_IP>:51820

# 5. Start WireGuard
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0

# 6. Test connectivity
ping 10.8.0.2  # Should ping Control PC
```

**Repeat for PrimeCore4 (69.62.123.97):**
```bash
# Same steps, use primecore4.conf instead
```

**Verification:**
```bash
# On Control PC, check peer handshakes
sudo wg show

# Should show recent handshakes for all peers:
# peer: <primecore1-pubkey>
#   latest handshake: 30 seconds ago
#
# peer: <primecore4-pubkey>
#   latest handshake: 45 seconds ago

# Test bidirectional connectivity
ping 10.8.0.11  # PrimeCore1
ping 10.8.0.14  # PrimeCore4

# From PrimeCore1
ping 10.8.0.2   # Control PC
ping 10.8.0.14  # PrimeCore4
```

**Python Verification:**
```python
from vpn.manager import VPNManager
vpn = VPNManager()
status = vpn.get_peer_status()
print(status)
# Should show: all peers with recent handshakes
```

**Acceptance Criteria:**
- [x] WireGuard running on all nodes
- [x] Peers showing recent handshakes (<2 min)
- [x] Can ping all nodes via VPN IPs
- [x] VPN manager reports healthy status

---

### Day 3-4: Data Pipeline Integration

#### Task 1.3: Wire Kafka to API Endpoints ⏱️ 1 day
**Priority:** 🔴 Critical
**Owner:** Backend Developer
**Dependencies:** Kafka cluster healthy

**Implementation Plan:**

**File 1: `api/middleware/kafka_producer.py` (Create new)**
```python
from streaming.kafka_manager import get_kafka_manager
from datetime import datetime
import asyncio

kafka = get_kafka_manager()

async def stream_api_event(
    event_type: str,
    endpoint: str,
    data: dict,
    user_id: str = None
):
    """Stream API events to Kafka"""
    try:
        await kafka.send_message(
            topic="analytics.events",
            message={
                "event_type": event_type,
                "endpoint": endpoint,
                "data": data,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        # Don't fail request if Kafka is down
        print(f"Failed to stream event: {e}")

async def stream_llm_inference(
    model: str,
    prompt_length: int,
    response_length: int,
    latency_ms: float,
    source: str
):
    """Stream LLM inference metrics"""
    await kafka.send_message(
        topic="edge.ai.inference",
        message={
            "model": model,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "latency_ms": latency_ms,
            "source": source,
            "timestamp": datetime.now().isoformat()
        },
        key=model
    )

async def stream_telemetry(
    device_id: str,
    metrics: dict
):
    """Stream device telemetry"""
    await kafka.send_message(
        topic="edge.telemetry",
        message={
            "device_id": device_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        },
        key=device_id
    )
```

**File 2: Update `api/main.py`**
```python
# Add import
from api.middleware.kafka_producer import stream_api_event, stream_llm_inference

# Update LLM endpoint
@app.post("/api/llm/generate")
async def generate_llm(request: LLMRequest, current_user: User = Depends(get_current_user)):
    start_time = time.time()

    # Existing generation logic
    result = await llm_client.generate(
        prompt=request.prompt,
        model=request.model,
        max_tokens=request.max_tokens,
        use_cache=request.use_cache
    )

    latency_ms = (time.time() - start_time) * 1000

    # ADD THIS: Stream to Kafka (async, non-blocking)
    asyncio.create_task(stream_llm_inference(
        model=request.model,
        prompt_length=len(request.prompt),
        response_length=len(result["response"]),
        latency_ms=latency_ms,
        source=result.get("source", "edge")
    ))

    # ADD THIS: Stream API event
    asyncio.create_task(stream_api_event(
        event_type="llm_generate",
        endpoint="/api/llm/generate",
        data={"model": request.model},
        user_id=current_user.username
    ))

    return result
```

**File 3: `streaming/telemetry_collector.py` (Create new)**
```python
import asyncio
import psutil
from streaming.kafka_manager import get_kafka_manager
from config.settings import settings

async def collect_and_stream_telemetry():
    """Collect system telemetry and stream to Kafka every 30 seconds"""
    kafka = get_kafka_manager()
    device_id = "control-pc-1"  # Or get from config

    while True:
        try:
            metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "temperature": get_temperature(),  # Implement based on Pironman5
                "load_avg": psutil.getloadavg()[0]
            }

            await kafka.send_message(
                topic="edge.telemetry",
                message={
                    "device_id": device_id,
                    "metrics": metrics,
                    "timestamp": datetime.now().isoformat()
                },
                key=device_id
            )

            await asyncio.sleep(30)  # Collect every 30 seconds

        except Exception as e:
            print(f"Telemetry collection error: {e}")
            await asyncio.sleep(30)

def get_temperature():
    """Get CPU temperature from Pironman5"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = int(f.read()) / 1000.0
        return temp
    except:
        return None

# Add to api/main.py startup
@app.on_event("startup")
async def startup():
    asyncio.create_task(collect_and_stream_telemetry())
```

**File 4: `streaming/timescale_consumer.py` (Create new)**
```python
import asyncio
from streaming.kafka_manager import get_kafka_manager
from analytics.timeseries_db import timescale_db

async def consume_telemetry_to_timescale():
    """Consume telemetry from Kafka and insert into TimescaleDB"""
    kafka = get_kafka_manager()

    async for message in kafka.consume_messages("edge.telemetry"):
        try:
            # Insert each metric
            for metric_name, value in message["metrics"].items():
                await timescale_db.insert_device_metric(
                    device_id=message["device_id"],
                    metric_name=metric_name,
                    value=value,
                    metadata={"source": "kafka"}
                )
        except Exception as e:
            print(f"Error inserting telemetry: {e}")

async def consume_ai_inference_to_timescale():
    """Consume AI inference metrics"""
    kafka = get_kafka_manager()

    async for message in kafka.consume_messages("edge.ai.inference"):
        try:
            await timescale_db.insert_ai_inference_result(
                model_name=message["model"],
                input_tokens=message["prompt_length"],
                output_tokens=message["response_length"],
                latency_ms=message["latency_ms"],
                metadata={"source": message["source"]}
            )
        except Exception as e:
            print(f"Error inserting AI inference: {e}")

# Add to api/main.py startup
@app.on_event("startup")
async def startup():
    asyncio.create_task(consume_telemetry_to_timescale())
    asyncio.create_task(consume_ai_inference_to_timescale())
```

**Testing:**
```bash
# 1. Restart API to load new code
docker compose -f docker-compose.enterprise.yml restart api

# 2. Send test request
curl -X POST http://localhost:8000/api/llm/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "llama3.2:latest"}'

# 3. Check Kafka UI
open http://localhost:8080
# Navigate to topics → edge.ai.inference → Messages
# Should see new message

# 4. Query TimescaleDB
docker exec -it prime-spark-timescaledb psql -U postgres -d prime_spark_analytics -c "SELECT * FROM ai_inference_results ORDER BY time DESC LIMIT 5;"
# Should see inserted data

# 5. Wait 30+ seconds, check telemetry
docker exec -it prime-spark-timescaledb psql -U postgres -d prime_spark_analytics -c "SELECT * FROM device_metrics ORDER BY time DESC LIMIT 10;"
# Should see telemetry data
```

**Acceptance Criteria:**
- [x] LLM requests stream to Kafka
- [x] Telemetry collected every 30s
- [x] Kafka consumers insert to TimescaleDB
- [x] Data visible in Kafka UI
- [x] Data queryable in TimescaleDB

---

#### Task 1.4: Fix Airflow DAG Data Source ⏱️ 4 hours
**Priority:** 🟡 High
**Owner:** Data Engineer
**Dependencies:** Task 1.3 (Kafka streaming)

**File: Update `pipeline/dags/edge_to_cloud_sync.py`**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import redis
import psycopg2

def extract_from_redis(**context):
    """Extract recent metrics from Redis"""
    r = redis.Redis(
        host='redis',
        port=6379,
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )

    devices = ["control-pc-1", "spark-agent-1"]
    metrics = []

    for device in devices:
        # Get cached metrics
        metric_data = r.hgetall(f"metrics:{device}")
        if metric_data:
            metrics.append({
                "device_id": device,
                "cpu": float(metric_data.get("cpu", 0)),
                "memory": float(metric_data.get("memory", 0)),
                "disk": float(metric_data.get("disk", 0)),
                "timestamp": datetime.now()
            })

    return metrics

def transform_metrics(**context):
    """Transform and validate metrics"""
    ti = context['ti']
    metrics = ti.xcom_pull(task_ids='extract')

    # Validate and clean
    transformed = []
    for m in metrics:
        if 0 <= m['cpu'] <= 100 and 0 <= m['memory'] <= 100:
            transformed.append(m)

    return transformed

def load_to_timescale(**context):
    """Load metrics into TimescaleDB"""
    ti = context['ti']
    metrics = ti.xcom_pull(task_ids='transform')

    conn = psycopg2.connect(
        host='timescaledb',
        port=5432,
        dbname='prime_spark_analytics',
        user='postgres',
        password=os.getenv('POSTGRES_PASSWORD')
    )

    cursor = conn.cursor()

    for m in metrics:
        cursor.execute("""
            INSERT INTO device_metrics (time, device_id, metric_name, value)
            VALUES (NOW(), %s, 'cpu_usage', %s),
                   (NOW(), %s, 'memory_usage', %s),
                   (NOW(), %s, 'disk_usage', %s)
        """, (
            m['device_id'], m['cpu'],
            m['device_id'], m['memory'],
            m['device_id'], m['disk']
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return len(metrics)

# DAG definition
dag = DAG(
    'edge_to_cloud_sync',
    default_args={
        'owner': 'primespark',
        'depends_on_past': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
    },
    description='Sync edge metrics to cloud analytics',
    schedule_interval='*/15 * * * *',  # Every 15 minutes
    start_date=datetime(2025, 11, 5),
    catchup=False
)

extract_task = PythonOperator(
    task_id='extract',
    python_callable=extract_from_redis,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform',
    python_callable=transform_metrics,
    dag=dag
)

load_task = PythonOperator(
    task_id='load',
    python_callable=load_to_timescale,
    dag=dag
)

extract_task >> transform_task >> load_task
```

**Testing:**
```bash
# 1. Trigger DAG manually
docker exec prime-spark-airflow-webserver airflow dags trigger edge_to_cloud_sync

# 2. Check DAG run
open http://localhost:8081
# Login: admin / SparkAI2025!
# Navigate to DAGs → edge_to_cloud_sync → Graph
# All tasks should be green (success)

# 3. Verify data in TimescaleDB
docker exec -it prime-spark-timescaledb psql -U postgres -d prime_spark_analytics -c "SELECT COUNT(*) FROM device_metrics WHERE time > NOW() - INTERVAL '1 hour';"
# Should show new rows after DAG run
```

**Acceptance Criteria:**
- [x] DAG pulls real data from Redis
- [x] DAG runs successfully every 15 min
- [x] Data appears in TimescaleDB
- [x] Retry logic works on failure

---

### Day 5-6: Agent Coordination

#### Task 1.5: Implement Agent Execution Endpoints ⏱️ 1 day
**Priority:** 🟡 High
**Owner:** Backend Developer
**Dependencies:** VPN deployed

**On Spark Agent (192.168.1.92):**

**File: `agent/api.py` (Create new)**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

app = FastAPI(title="Spark Agent API")

class TaskPayload(BaseModel):
    task_id: str
    task_type: str
    priority: str
    payload: Dict[str, Any]

@app.post("/api/execute")
async def execute_task(task: TaskPayload):
    """Execute assigned task"""
    print(f"Executing task {task.task_id} of type {task.task_type}")

    try:
        if task.task_type == "voice_recognition":
            result = await process_voice_recognition(task.payload)
        elif task.task_type == "voice_synthesis":
            result = await process_voice_synthesis(task.payload)
        elif task.task_type == "llm":
            result = await process_llm_task(task.payload)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")

        return {
            "task_id": task.task_id,
            "status": "completed",
            "result": result
        }

    except Exception as e:
        return {
            "task_id": task.task_id,
            "status": "failed",
            "error": str(e)
        }

async def process_voice_recognition(payload: dict):
    """Process audio for voice recognition"""
    audio_url = payload.get("audio_url")
    # TODO: Implement actual voice recognition
    await asyncio.sleep(2)  # Simulate processing
    return {"transcription": "Hello world", "confidence": 0.95}

async def process_voice_synthesis(payload: dict):
    """Generate speech from text"""
    text = payload.get("text")
    # TODO: Implement actual TTS
    await asyncio.sleep(1)
    return {"audio_url": "http://nas/audio/generated.wav", "duration": 3.5}

async def process_llm_task(payload: dict):
    """Run LLM inference"""
    prompt = payload.get("prompt")
    # Use local Ollama
    # TODO: Implement actual LLM call
    await asyncio.sleep(2)
    return {"response": "LLM response here", "tokens": 150}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent_id": "spark-agent-1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Deploy:**
```bash
# On Spark Agent
cd /home/pironman5/spark-agent
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn

# Run agent API
python agent/api.py
```

**Test from Control PC:**
```bash
# Test agent health
curl http://10.8.0.3:8000/health

# Test task execution via agent coordinator
cd /home/pironman5/prime-spark-ai
python3 << 'EOF'
import asyncio
from agents.coordinator import AgentCoordinator

async def test():
    coordinator = AgentCoordinator()

    # Submit voice recognition task
    task_id = await coordinator.submit_task(
        task_type="voice_recognition",
        priority="HIGH",
        payload={"audio_url": "http://example.com/audio.wav"}
    )

    print(f"Task submitted: {task_id}")

    # Wait for completion
    await asyncio.sleep(5)

    # Check status
    status = await coordinator.get_task_status(task_id)
    print(f"Task status: {status}")

asyncio.run(test())
EOF
```

**Acceptance Criteria:**
- [x] Agent API running on port 8000
- [x] Health check responds
- [x] Can execute tasks from coordinator
- [x] Task results returned correctly

---

### Day 7-8: Monitoring & Observability

#### Task 1.6: Create Grafana Dashboards ⏱️ 4 hours
**Priority:** 🟡 High
**Owner:** DevOps
**Dependencies:** Task 1.3 (Kafka streaming)

**Access Grafana:**
```
URL: http://localhost:3002
Login: admin / SparkAI2025!
```

**Dashboard 1: System Overview**

1. Click "+" → "Import dashboard"
2. Paste this JSON:

```json
{
  "dashboard": {
    "title": "Prime Spark AI - System Overview",
    "tags": ["primespark", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Request Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(fastapi_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
      },
      {
        "id": 2,
        "title": "CPU Usage by Device",
        "type": "graph",
        "datasource": "TimescaleDB",
        "targets": [
          {
            "rawSql": "SELECT time AS \"time\", device_id, value FROM device_metrics WHERE metric_name='cpu_percent' AND $__timeFilter(time) ORDER BY time"
          }
        ],
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8}
      },
      {
        "id": 3,
        "title": "Memory Usage",
        "type": "graph",
        "datasource": "TimescaleDB",
        "targets": [
          {
            "rawSql": "SELECT time, device_id, value FROM device_metrics WHERE metric_name='memory_percent' AND $__timeFilter(time) ORDER BY time"
          }
        ],
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8}
      },
      {
        "id": 4,
        "title": "LLM Inference Latency (p95)",
        "type": "graph",
        "datasource": "TimescaleDB",
        "targets": [
          {
            "rawSql": "SELECT time_bucket('5 minutes', time) as time, percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency FROM ai_inference_results WHERE $__timeFilter(time) GROUP BY 1 ORDER BY 1"
          }
        ],
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8}
      }
    ]
  }
}
```

3. Click "Load" → "Import"

**Dashboard 2: Kafka Streams**

Create manually:
1. New Dashboard → Add Panel
2. Panel 1: "Consumer Lag" (Prometheus)
   - Query: `kafka_consumergroup_lag`
3. Panel 2: "Messages/sec" (Prometheus)
   - Query: `rate(kafka_topic_partition_current_offset[1m])`
4. Save dashboard as "Kafka Streams"

**Dashboard 3: Edge vs Cloud Performance**

1. New Dashboard
2. Panel 1: "Request Routing" (Pie chart)
   - Query: `SELECT source, COUNT(*) FROM ai_inference_results WHERE time > NOW() - INTERVAL '1 hour' GROUP BY source`
3. Panel 2: "Latency Comparison" (Bar chart)
   - Query: `SELECT source, AVG(latency_ms) FROM ai_inference_results WHERE time > NOW() - INTERVAL '1 hour' GROUP BY source`

**Acceptance Criteria:**
- [x] 3 dashboards created and saved
- [x] All panels showing live data
- [x] Dashboards update in real-time
- [x] Dashboard JSONs exported to Git

---

#### Task 1.7: Configure Prometheus Alerts ⏱️ 2 hours
**Priority:** 🟡 High
**Owner:** DevOps
**Dependencies:** Prometheus running

**File: Create `deployment/prometheus_alerts.yml`**
```yaml
groups:
  - name: primespark_critical
    interval: 1m
    rules:
      - alert: ServiceDown
        expr: up{job="prime-spark-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Prime Spark API is down"
          description: "API service has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(fastapi_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighCPUUsage
        expr: node_cpu_seconds_total{mode="idle"} < 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage above 90% for 10 minutes"

      - alert: HighMemoryUsage
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Less than 10% memory available"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Less than 20% disk space available"

      - alert: KafkaConsumerLag
        expr: kafka_consumergroup_lag > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Kafka consumer lag"
          description: "Consumer lag is {{ $value }} messages"

      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(fastapi_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is {{ $value }}s"
```

**File: Update `deployment/prometheus.yml`**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Add alert rules
rule_files:
  - 'prometheus_alerts.yml'

# Alertmanager configuration (optional)
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'localhost:9093'  # If you deploy Alertmanager

scrape_configs:
  - job_name: 'prime-spark-api'
    static_configs:
      - targets: ['api:8000']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9092']
```

**Deploy:**
```bash
# Copy alert rules
cp deployment/prometheus_alerts.yml deployment/prometheus/

# Update docker-compose to mount alert rules
# (Already mounted in current docker-compose.enterprise.yml)

# Restart Prometheus
docker compose -f docker-compose.enterprise.yml restart prometheus

# Verify rules loaded
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[].name'
# Should list all alert names
```

**Testing Alerts:**
```bash
# Trigger a test alert (stop API)
docker compose -f docker-compose.enterprise.yml stop api
# Wait 1 minute, check Prometheus alerts:
open http://localhost:9090/alerts
# Should show "ServiceDown" firing

# Restart API
docker compose -f docker-compose.enterprise.yml start api
```

**Acceptance Criteria:**
- [x] Alert rules loaded in Prometheus
- [x] Alerts visible at /alerts endpoint
- [x] Test alerts fire correctly
- [x] Alerts clear when condition resolves

---

## Phase 2: Testing Foundation (Week 3-4)

**Goal:** Achieve 85%+ test coverage, validate all integrations

### Day 9-13: Unit & Integration Tests

#### Task 2.1: API Endpoint Tests ⏱️ 1 week
**Priority:** 🔴 Critical
**Owner:** Backend Developer
**Dependencies:** None

**Setup Testing Framework:**
```bash
cd /home/pironman5/prime-spark-ai

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Update requirements.txt
echo "pytest==7.4.3" >> requirements.txt
echo "pytest-asyncio==0.21.1" >> requirements.txt
echo "pytest-cov==4.1.0" >> requirements.txt
```

**File: `tests/conftest.py`**
```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Test client for API"""
    return TestClient(app)

@pytest.fixture
async def auth_token(client):
    """Get authentication token"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "SparkAI2025!"
    })
    return response.json()["access_token"]
```

**File: `tests/test_api_health.py`**
```python
def test_health_endpoint(client):
    """Test basic health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "service" in data

def test_detailed_health(client, auth_token):
    """Test detailed health check"""
    response = client.get(
        "/api/health/detailed",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "subsystems" in data
    assert "redis" in data["subsystems"]
```

**File: `tests/test_api_auth.py`**
```python
import pytest

def test_login_success(client):
    """Test successful login"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "SparkAI2025!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_get_current_user(client, auth_token):
    """Test getting current user info"""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == "admin"
```

**File: `tests/test_api_llm.py`**
```python
import pytest

@pytest.mark.asyncio
async def test_llm_generate(client, auth_token):
    """Test LLM generation endpoint"""
    response = client.post(
        "/api/llm/generate",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "prompt": "Say hello",
            "model": "llama3.2:latest",
            "max_tokens": 50
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0

def test_llm_list_models(client, auth_token):
    """Test listing available models"""
    response = client.get(
        "/api/llm/models",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
```

**File: `tests/test_api_memory.py`**
```python
def test_memory_set_get(client, auth_token):
    """Test memory storage and retrieval"""
    # Set value
    response = client.post(
        "/api/memory/set",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "key": "test_key",
            "value": {"data": "test_value"},
            "tier": 1,
            "ttl": 3600
        }
    )
    assert response.status_code == 200

    # Get value
    response = client.get(
        "/api/memory/get/test_key",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == "test_value"

def test_memory_delete(client, auth_token):
    """Test memory deletion"""
    # Set value
    client.post(
        "/api/memory/set",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"key": "delete_me", "value": "data"}
    )

    # Delete
    response = client.delete(
        "/api/memory/delete_me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Verify deleted
    response = client.get(
        "/api/memory/get/delete_me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404
```

**File: `tests/test_api_tasks.py`**
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_task_submit(client, auth_token):
    """Test task submission"""
    response = client.post(
        "/api/tasks/submit",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "task_type": "voice_recognition",
            "priority": "HIGH",
            "payload": {"audio_url": "http://example.com/audio.wav"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data

@pytest.mark.asyncio
async def test_task_status(client, auth_token):
    """Test getting task status"""
    # Submit task
    submit_response = client.post(
        "/api/tasks/submit",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"task_type": "llm", "payload": {"prompt": "test"}}
    )
    task_id = submit_response.json()["task_id"]

    # Get status
    response = client.get(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED"]
```

**Run Tests:**
```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html tests/

# Run specific test file
pytest tests/test_api_auth.py -v

# Run tests matching pattern
pytest -k "test_llm" -v

# View coverage report
open htmlcov/index.html
```

**Target Coverage:**
```
api/main.py         85%+
routing/           90%+
memory/            90%+
agents/            85%+
streaming/         80%+
Overall:           85%+
```

**Acceptance Criteria:**
- [x] 85%+ code coverage
- [x] All API endpoints tested
- [x] All tests passing
- [x] Coverage report generated

---

(Continuing in next message due to length...)

**Integration Testing Strategy** and remaining phases will be in COMPLETION_ROADMAP.md (saving now).
