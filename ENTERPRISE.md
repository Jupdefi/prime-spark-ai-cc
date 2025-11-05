# Prime Spark AI - Enterprise Edition

**Production-Ready Hybrid Edge-Cloud AI Platform with Advanced Analytics**

## 🎯 Overview

Prime Spark AI Enterprise Edition is a comprehensive, production-ready system for deploying AI at scale across edge devices and cloud infrastructure. It combines real-time data streaming, advanced analytics, ML operations, and enterprise-grade monitoring.

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    PRIME SPARK AI ENTERPRISE                        │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        EDGE INFRASTRUCTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│  • Control PC (Pi5 16GB + Hailo-8) - Main coordinator               │
│  • Spark Agent (Pi5 8GB @ 192.168.1.92) - Voice/task agent          │
│  • Argon EON NAS (192.168.1.49) - 8TB storage                       │
│  • Pi4 OpenWRT Router - Network edge                                │
└─────────────────────────────────────────────────────────────────────┘
                              ▼ VPN (WireGuard)
┌─────────────────────────────────────────────────────────────────────┐
│                       CLOUD INFRASTRUCTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│  • PrimeCore1 (141.136.35.51) - Orchestration + OpenWebUI           │
│  • PrimeCore2 - Memory layer (Supabase + Nextcloud)                 │
│  • PrimeCore3 - Voice processing                                    │
│  • PrimeCore4 (69.62.123.97) - Services (Ollama, ComfyUI, MinIO)    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        DATA STREAMING LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│  Apache Kafka (3-node cluster)                                      │
│  • edge.telemetry - System metrics from edge                        │
│  • edge.ai.inference - AI inference results                         │
│  • edge.sensors - Sensor data streams                               │
│  • cloud.commands - Cloud → Edge commands                           │
│  • analytics.events - Processed analytics                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      ANALYTICS & STORAGE                             │
├─────────────────────────────────────────────────────────────────────┤
│  TimescaleDB (PostgreSQL + TimescaleDB extension)                   │
│  • device_metrics - Time-series metrics                             │
│  • ai_inference_results - ML inference tracking                     │
│  • sensor_data - High-frequency sensor readings                     │
│  • analytics_events - Business events                               │
│  • Continuous aggregates for fast queries                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       DATA PIPELINE (Airflow)                        │
├─────────────────────────────────────────────────────────────────────┤
│  • Edge-to-Cloud sync (every 15 min)                                │
│  • Analytics aggregation jobs                                       │
│  • Data validation and quality checks                               │
│  • Model performance monitoring                                     │
│  • Automated reporting                                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      ML OPS PIPELINE (MLflow)                        │
├─────────────────────────────────────────────────────────────────────┤
│  • Experiment tracking                                              │
│  • Model versioning and registry                                    │
│  • Automated deployment to edge/cloud                               │
│  • A/B testing framework                                            │
│  • Performance monitoring                                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   MONITORING & OBSERVABILITY                         │
├─────────────────────────────────────────────────────────────────────┤
│  Prometheus + Grafana                                               │
│  • System metrics (CPU, RAM, disk, network)                         │
│  • Application metrics (API latency, throughput)                    │
│  • Business metrics (inference count, accuracy)                     │
│  • Custom dashboards for edge and cloud                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (Traefik)                         │
├─────────────────────────────────────────────────────────────────────┤
│  • Load balancing                                                   │
│  • SSL/TLS termination                                              │
│  • Rate limiting                                                    │
│  • Request routing                                                  │
│  • Service discovery                                                │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start - Enterprise Edition

### Prerequisites

- **Docker & Docker Compose** (recommended) OR **Kubernetes cluster**
- **4GB+ RAM** per service (16GB+ recommended for full stack)
- **Network connectivity** between edge and cloud
- **Python 3.11+** for local development

### Option 1: Docker Compose (Recommended for Testing)

```bash
# 1. Clone and navigate
cd /home/pironman5/prime-spark-ai

# 2. Configure environment
cp .env.example .env
nano .env  # Configure your settings

# Generate secrets
export JWT_SECRET=$(openssl rand -hex 32)
export AIRFLOW_FERNET_KEY=$(openssl rand -base64 32)

# 3. Start enterprise stack
docker-compose -f docker-compose.enterprise.yml up -d

# 4. Verify services
docker-compose -f docker-compose.enterprise.yml ps

# 5. Initialize database
docker-compose -f docker-compose.enterprise.yml exec api python -c "
from analytics.timeseries_db import timescale_db
import asyncio
asyncio.run(timescale_db.initialize_schema())
"

# 6. Access services
# API: http://localhost:8000
# Kafka UI: http://localhost:8080
# Airflow: http://localhost:8081
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# MLflow: http://localhost:5000 (with --profile mlops)
```

### Option 2: Kubernetes (Production)

```bash
# 1. Create namespace
kubectl apply -f kubernetes/namespace.yaml

# 2. Create secrets
kubectl create secret generic prime-spark-secrets \
  --from-literal=redis-password=$(openssl rand -base64 32) \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  -n prime-spark-ai

# 3. Deploy infrastructure
kubectl apply -f kubernetes/ -n prime-spark-ai

# 4. Verify deployment
kubectl get pods -n prime-spark-ai
kubectl get svc -n prime-spark-ai

# 5. Access via ingress
# Configure your DNS to point to your ingress controller
# Access: https://api.prime-spark.ai
```

## 📊 Services & Ports

| Service | Port | Purpose |
|---------|------|---------|
| API | 8000 | Main REST API |
| Redis | 6379 | Cache (Tier 1) |
| PostgreSQL/TimescaleDB | 5432 | Analytics database |
| Kafka | 9092 | Message streaming |
| Kafka UI | 8080 | Kafka management |
| Airflow Web | 8081 | Data pipeline UI |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Visualization |
| MLflow | 5000 | ML experiment tracking |
| Traefik Dashboard | 8090 | API Gateway UI |

## 🔧 Configuration

### Environment Variables

```bash
# Streaming
KAFKA_PORT=9092
KAFKA_UI_PORT=8080

# Analytics
POSTGRES_HOST=timescaledb
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Data Pipeline
AIRFLOW_PORT=8081
AIRFLOW_DB_PASSWORD=airflow_secure_password
AIRFLOW_FERNET_KEY=your_generated_fernet_key

# ML Ops
MLFLOW_PORT=5000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Kafka Topics

All topics are auto-created with 3 partitions:

- `edge.telemetry` - System telemetry from edge devices
- `edge.ai.inference` - AI inference results
- `edge.sensors` - Sensor data streams
- `cloud.commands` - Commands from cloud to edge
- `analytics.events` - Processed analytics events
- `system.health` - Health check events
- `models.updates` - Model update notifications

## 📈 Data Pipeline

### Airflow DAGs

Located in `pipeline/dags/`:

- **edge_to_cloud_sync.py** - Syncs edge data to cloud (every 15 min)
- **analytics_aggregation.py** - Daily analytics aggregation
- **model_performance.py** - Model performance monitoring
- **data_quality.py** - Data quality checks

Access Airflow UI at `http://localhost:8081`

Default credentials:
- Username: `admin`
- Password: `admin` (change in production!)

## 🤖 ML Operations

### Model Deployment Workflow

1. **Train Model** (local or cloud)
   ```python
   from models.model_deployer import model_deployer

   # Log model to MLflow
   run_id = model_deployer.log_model(
       model=your_model,
       model_name="object-detection-v1",
       framework="pytorch",
       metrics={"accuracy": 0.95},
       params={"epochs": 50, "lr": 0.001}
   )
   ```

2. **Convert to ONNX** (for edge optimization)
   ```python
   onnx_path = model_deployer.convert_to_onnx(
       pytorch_model=your_model,
       input_shape=(1, 3, 224, 224),
       output_path="models/object-detection-v1.onnx"
   )
   ```

3. **Register Model**
   ```python
   model_deployer.register_model_version(
       model_name="object-detection-v1",
       run_id=run_id,
       stage="Production"
   )
   ```

4. **Deploy to Edge**
   ```python
   model_deployer.deploy_to_edge(
       model_name="object-detection-v1",
       version=None,  # Latest production version
       device_ids=["control-pc-1", "spark-agent-1"]
   )
   ```

Access MLflow UI at `http://localhost:5000`

## 📡 Real-Time Streaming

### Publishing Data to Kafka

```python
from streaming.kafka_manager import get_kafka_manager

kafka = get_kafka_manager()

# Publish telemetry
await kafka.send_message(
    topic='edge.telemetry',
    message={
        'device_id': 'control-pc-1',
        'metrics': {
            'cpu_usage': 45.2,
            'memory_usage': 60.5
        }
    },
    key='control-pc-1'
)
```

### Consuming Data

```python
def process_telemetry(message):
    print(f"Received: {message.value}")

kafka.subscribe_consumer(
    topics=['edge.telemetry'],
    group_id='my-consumer',
    callback=process_telemetry
)
```

## 📊 Analytics Queries

### TimescaleDB Examples

```sql
-- Device metrics over last 24 hours
SELECT
    time_bucket('5 minutes', time) AS bucket,
    AVG(value) as avg_value
FROM device_metrics
WHERE device_id = 'control-pc-1'
  AND metric_name = 'cpu_usage'
  AND time > NOW() - INTERVAL '24 hours'
GROUP BY bucket
ORDER BY bucket DESC;

-- AI inference performance
SELECT
    model_name,
    AVG(inference_time_ms) as avg_time,
    COUNT(*) as total_inferences
FROM ai_inference_results
WHERE time > NOW() - INTERVAL '1 day'
GROUP BY model_name;

-- Use materialized view for fast aggregates
SELECT * FROM device_metrics_hourly
WHERE device_id = 'control-pc-1'
  AND bucket > NOW() - INTERVAL '7 days';
```

## 🔍 Monitoring

### Grafana Dashboards

Access Grafana at `http://localhost:3000`

Default credentials:
- Username: `admin`
- Password: From `$ADMIN_PASSWORD` env var

Pre-configured dashboards:
- **System Overview** - All services health
- **Edge Devices** - Edge device metrics
- **AI Performance** - Model inference metrics
- **Kafka Metrics** - Streaming performance
- **API Performance** - API latency and throughput

### Prometheus Targets

All services expose metrics at `/metrics`:
- API: `api:8000/metrics`
- Node Exporter: `node-exporter:9100`
- Kafka Exporter: `kafka-exporter:9308`
- Postgres Exporter: `postgres-exporter:9187`

## 🔒 Security

### SSL/TLS with cert-manager (Kubernetes)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Authentication

All API endpoints require JWT authentication (except `/health`).

Get token:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your_password"}'
```

Use token:
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/endpoint
```

## 🚢 Deployment

### CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci-cd.yml`):

1. **Test** - Run pytest on all code
2. **Build** - Build Docker image
3. **Deploy Staging** - Auto-deploy `develop` branch
4. **Deploy Production** - Auto-deploy `main` branch with manual approval

### Manual Deployment

```bash
# Build image
docker build -t prime-spark-ai:latest .

# Push to registry
docker tag prime-spark-ai:latest ghcr.io/your-org/prime-spark-ai:latest
docker push ghcr.io/your-org/prime-spark-ai:latest

# Deploy to Kubernetes
kubectl set image deployment/prime-spark-api \
  api=ghcr.io/your-org/prime-spark-ai:latest \
  -n prime-spark-ai

# Rollback if needed
kubectl rollout undo deployment/prime-spark-api -n prime-spark-ai
```

## 📦 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **API** | FastAPI, Uvicorn |
| **Cache** | Redis |
| **Analytics DB** | PostgreSQL + TimescaleDB |
| **Streaming** | Apache Kafka |
| **Pipeline** | Apache Airflow |
| **ML Ops** | MLflow, PyTorch, ONNX |
| **Monitoring** | Prometheus, Grafana |
| **API Gateway** | Traefik |
| **Orchestration** | Docker Compose, Kubernetes |
| **CI/CD** | GitHub Actions |
| **VPN** | WireGuard |

## 🎓 Best Practices

### Performance

1. **Edge-first processing** - Keep data local when possible
2. **Batching** - Batch Kafka messages for efficiency
3. **Caching** - Use Redis for hot data
4. **Compression** - Enable Kafka compression
5. **Indexing** - Proper indexes on TimescaleDB

### Reliability

1. **Replication** - Kafka with RF=3 minimum
2. **Backups** - Regular PostgreSQL backups
3. **Health checks** - All services have health endpoints
4. **Graceful shutdown** - Handle SIGTERM properly
5. **Circuit breakers** - Prevent cascade failures

### Monitoring

1. **Metrics** - Expose Prometheus metrics
2. **Logging** - Structured JSON logging
3. **Tracing** - OpenTelemetry for distributed tracing
4. **Alerting** - Set up Prometheus alerts
5. **Dashboards** - Grafana for visualization

## 🔧 Troubleshooting

### Kafka Issues

```bash
# Check Kafka broker
docker-compose exec kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092

# List topics
docker-compose exec kafka kafka-topics \
  --list --bootstrap-server localhost:9092

# View consumer groups
docker-compose exec kafka kafka-consumer-groups \
  --list --bootstrap-server localhost:9092
```

### Database Issues

```bash
# Check TimescaleDB
docker-compose exec timescaledb psql -U postgres -d prime_spark_analytics

# View continuous aggregates
SELECT view_name FROM timescaledb_information.continuous_aggregates;

# Check compression
SELECT * FROM timescaledb_information.compression_settings;
```

### Airflow Issues

```bash
# View scheduler logs
docker-compose logs -f airflow-scheduler

# Test DAG
docker-compose exec airflow-webserver airflow dags test edge_to_cloud_sync

# Clear failed tasks
docker-compose exec airflow-webserver airflow tasks clear edge_to_cloud_sync
```

## 📚 Documentation

- **Quick Start**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- **Configuration**: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- **API Reference**: [docs/API.md](docs/API.md)
- **Installation**: [INSTALL.md](INSTALL.md)

## 💡 Mission

**Making AI More Fun, Free, and Fair**

Open-source, production-ready infrastructure running on affordable hardware (£50 Pi to £380 cloud servers).

---

**Enterprise Edition Status**: ✅ Production Ready

Version: 2.0.0-enterprise
Last Updated: 2025-01-15
