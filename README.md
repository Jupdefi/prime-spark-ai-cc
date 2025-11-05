# Prime Spark AI

**Making AI More Fun, Free, and Fair**

A comprehensive hybrid edge-cloud AI platform that bridges affordable edge hardware with enterprise cloud infrastructure.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-326CE5.svg)](https://kubernetes.io/)

---

## 🎯 What is Prime Spark AI?

Prime Spark AI is a **production-ready hybrid edge-cloud AI system** designed to run on affordable hardware while providing enterprise-grade capabilities. From Raspberry Pi homelab setups to cloud VM deployments, it seamlessly bridges the gap between edge computing and cloud processing.

### Two Editions

#### **Standard Edition** - Perfect for Homelabs
- Edge-cloud hybrid architecture
- VPN infrastructure (WireGuard)
- Three-tier memory (Redis → NAS → Cloud)
- Intelligent request routing
- Agent coordination
- Power-aware operation
- Basic monitoring

👉 **[Get Started with Standard](docs/QUICKSTART.md)**

#### **Enterprise Edition** - Production Ready
Everything in Standard, plus:
- **Real-time streaming** with Apache Kafka
- **Advanced analytics** with TimescaleDB
- **Data pipelines** with Apache Airflow
- **ML Ops** with MLflow
- **Kubernetes** deployment manifests
- **API Gateway** with Traefik
- **Enhanced monitoring** with Prometheus & Grafana
- **CI/CD pipelines** with GitHub Actions

👉 **[Get Started with Enterprise](ENTERPRISE.md)**

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    PRIME SPARK AI PLATFORM                      │
└────────────────────────────────────────────────────────────────┘

EDGE LAYER                                    CLOUD LAYER
┌─────────────────┐                          ┌──────────────────┐
│ Control PC      │◄────── VPN Tunnel ──────►│ PrimeCore1       │
│ (Pi5 + Hailo-8) │      (WireGuard)         │ (Orchestration)  │
└─────────────────┘                          └──────────────────┘

┌─────────────────┐                          ┌──────────────────┐
│ Spark Agent     │◄────── VPN Tunnel ──────►│ PrimeCore4       │
│ (Pi5 8GB)       │      (Encrypted)         │ (15 Services)    │
└─────────────────┘                          └──────────────────┘

┌─────────────────┐
│ Argon EON NAS   │
│ (8TB Storage)   │
└─────────────────┘

                        ▼
┌────────────────────────────────────────────────────────────────┐
│                      DATA & STREAMING LAYER                     │
│  Kafka → TimescaleDB → Analytics → ML Ops                      │
└────────────────────────────────────────────────────────────────┘

                        ▼
┌────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│  FastAPI | Authentication | Routing | Agent Coordination       │
└────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Standard Edition (Homelab)

```bash
# 1. Clone and configure
cd /home/pironman5/prime-spark-ai
cp .env.example .env
nano .env

# 2. Deploy
sudo ./deployment/deploy.sh

# 3. Verify
curl http://localhost:8000/health
```

### Enterprise Edition (Production)

```bash
# Docker Compose
docker-compose -f docker-compose.enterprise.yml up -d

# OR Kubernetes
kubectl apply -f kubernetes/ -n prime-spark-ai
```

**Access Services:**
- API: http://localhost:8000 (Interactive docs at `/docs`)
- Kafka UI: http://localhost:8080
- Airflow: http://localhost:8081
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- MLflow: http://localhost:5000

---

## 🌟 Key Features

### 🔒 **Secure VPN Infrastructure**
- WireGuard-based encrypted tunnels
- Automatic peer discovery
- Health monitoring
- Seamless edge-cloud connectivity

### 💾 **Three-Tier Memory Architecture**
- **Tier 1**: Redis cache (sub-ms, hot data)
- **Tier 2**: NAS storage (persistent, shared edge)
- **Tier 3**: Cloud storage (long-term, S3-compatible)
- Automatic tiering and backfill

### 🧠 **Intelligent Request Routing**
- **Edge-first**: Privacy + low latency
- **Cloud fallback**: Reliability
- **Balanced**: Lowest latency wins
- Power-aware (edge-only on battery)

### 🤝 **Agent Coordination**
- Distributed task execution
- Load balancing
- Priority queues
- Health monitoring
- Graceful degradation

### 🔋 **Power Management**
- Battery monitoring
- Auto mode switching
- Edge-only on low battery
- Configurable thresholds

### 📡 **Real-Time Streaming** (Enterprise)
- Apache Kafka for message streaming
- Multiple topics for different data types
- Scalable consumer groups
- Guaranteed delivery

### 📊 **Advanced Analytics** (Enterprise)
- TimescaleDB for time-series data
- Continuous aggregates for fast queries
- SQL analytics on streaming data
- Retention policies

### 🔄 **Data Pipelines** (Enterprise)
- Apache Airflow orchestration
- Scheduled ETL jobs
- Data quality checks
- Automated reporting

### 🤖 **ML Operations** (Enterprise)
- MLflow experiment tracking
- Model versioning
- ONNX export for edge
- Automated deployment
- A/B testing

### 📈 **Enterprise Monitoring** (Enterprise)
- Prometheus metrics collection
- Grafana dashboards
- Custom alerts
- Distributed tracing

---

## 🎨 Use Cases

### Homelab AI
- Personal AI assistant
- Home automation
- Media processing
- Learning and experimentation

### Edge AI Deployment
- Computer vision at edge
- Voice processing
- Sensor data analytics
- Real-time inference

### Enterprise Production
- Multi-site AI deployment
- Real-time analytics
- Model A/B testing
- Regulatory compliance

### Research & Development
- Experiment tracking
- Model comparison
- Performance benchmarking
- Data exploration

---

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API** | FastAPI | REST API server |
| **Cache** | Redis | Fast in-memory cache |
| **Database** | TimescaleDB | Time-series analytics |
| **Streaming** | Apache Kafka | Real-time data flow |
| **Pipeline** | Apache Airflow | ETL orchestration |
| **ML Ops** | MLflow | Model management |
| **Monitoring** | Prometheus + Grafana | Observability |
| **Gateway** | Traefik | API gateway |
| **VPN** | WireGuard | Secure networking |
| **Container** | Docker | Application packaging |
| **Orchestration** | Kubernetes | Container orchestration |
| **CI/CD** | GitHub Actions | Automation |

---

## 📚 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 10 minutes
- **[Configuration Guide](docs/CONFIGURATION.md)** - All configuration options
- **[API Documentation](docs/API.md)** - Complete API reference
- **[Enterprise Guide](ENTERPRISE.md)** - Production deployment
- **[Installation Details](INSTALL.md)** - Architecture overview

---

## 🚀 Deployment Options

### Development (Docker Compose)
Perfect for testing and development:
```bash
docker-compose up -d  # Standard
docker-compose -f docker-compose.enterprise.yml up -d  # Enterprise
```

### Production (Kubernetes)
For scalable production deployments:
```bash
kubectl apply -f kubernetes/ -n prime-spark-ai
```

### Bare Metal
Direct installation on hardware:
```bash
./deployment/deploy.sh
```

---

## 🔧 Configuration

Key environment variables:

```bash
# Edge Infrastructure
CONTROL_PC_IP=192.168.1.100
SPARK_AGENT_IP=192.168.1.92
EDGE_NAS_IP=192.168.1.49

# Cloud Infrastructure
PRIMECORE1_IP=141.136.35.51
PRIMECORE4_IP=69.62.123.97

# Security
JWT_SECRET=<generate-with-openssl>
ADMIN_PASSWORD=<secure-password>

# Streaming (Enterprise)
KAFKA_PORT=9092
POSTGRES_PORT=5432

# ML Ops (Enterprise)
MLFLOW_PORT=5000
```

See [CONFIGURATION.md](docs/CONFIGURATION.md) for full details.

---

## 🎓 Examples

### LLM Inference
```python
from routing.llm_client import llm_client

result = await llm_client.generate(
    prompt="Explain quantum computing",
    model="llama3.2:latest",
    use_cache=True
)
print(result['response'])
```

### Stream Data to Kafka
```python
from streaming.kafka_manager import get_kafka_manager

kafka = get_kafka_manager()
await kafka.send_message(
    topic='edge.telemetry',
    message={'cpu': 45.2, 'memory': 60.5},
    key='control-pc-1'
)
```

### Query Analytics
```python
from analytics.timeseries_db import timescale_db

metrics = await timescale_db.query_device_metrics(
    device_id='control-pc-1',
    metric_name='cpu_usage',
    start_time=datetime.now() - timedelta(hours=24)
)
```

### Deploy ML Model
```python
from models.model_deployer import model_deployer

model_deployer.deploy_to_edge(
    model_name="object-detection-v1",
    version=None,  # Latest
    device_ids=["control-pc-1", "spark-agent-1"]
)
```

---

## 🤝 Contributing

We welcome contributions! This project aims to make AI accessible to everyone.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Mission

**Making AI More Fun, Free, and Fair**

Prime Spark AI is designed to run on affordable hardware:
- **Edge**: £50-£180 (Raspberry Pi 5)
- **Cloud**: £5-£380/month (Budget VPS to dedicated servers)

Open-source, production-ready, and accessible to all.

---

## 🆘 Support

- **Documentation**: See `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/your-org/prime-spark-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/prime-spark-ai/discussions)

---

## 🎯 Roadmap

- [x] Edge-cloud hybrid architecture
- [x] VPN infrastructure
- [x] Three-tier memory
- [x] Intelligent routing
- [x] Agent coordination
- [x] Real-time streaming (Kafka)
- [x] Advanced analytics (TimescaleDB)
- [x] Data pipelines (Airflow)
- [x] ML Ops (MLflow)
- [x] Kubernetes deployment
- [ ] WebSocket real-time API
- [ ] Multi-region support
- [ ] Advanced security (mTLS, vault)
- [ ] Auto-scaling
- [ ] Edge AI model optimization
- [ ] Mobile app integration

---

## ⭐ Star History

If you find Prime Spark AI useful, please consider giving it a star!

---

**Built with ❤️ for the open-source community**

Prime Spark AI | Version 2.0.0 | 2025
