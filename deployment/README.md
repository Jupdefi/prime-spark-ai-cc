# Prime Spark AI - Deployment System

Comprehensive deployment automation for Prime Spark AI across development, staging, and production environments using Infrastructure as Code, containerization, and CI/CD pipelines.

## 🚀 Quick Start

### Single-Command Deployment

```bash
# Deploy to local development (Raspberry Pi 5)
./deploy.sh dev

# Deploy to staging environment
./deploy.sh staging

# Deploy to production environment
./deploy.sh production --auto-approve

# Validate all configurations
./deploy.sh validate
```

## 📁 Directory Structure

```
deployment/
├── environments/              # Environment-specific configurations
│   ├── dev.yaml              # Local Raspberry Pi 5 development
│   ├── staging.yaml          # AWS cloud sandbox
│   └── prod.yaml             # Multi-region production
├── terraform/                 # Infrastructure as Code
│   ├── modules/              # Reusable Terraform modules
│   │   ├── vpc/              # Multi-AZ VPC with subnets
│   │   ├── eks/              # EKS Kubernetes cluster
│   │   ├── rds/              # PostgreSQL database
│   │   ├── elasticache/      # Redis cluster
│   │   └── s3/               # S3 object storage
│   ├── environments/         # Environment tfvars
│   └── *.tf                  # Main Terraform files
├── kubernetes/                # Kubernetes manifests
│   ├── base/                 # Base resources
│   └── overlays/             # Environment overlays
│       ├── staging/
│       └── production/
├── ci-cd/                     # CI/CD pipelines
│   ├── github-actions/       # GitHub Actions workflows
│   ├── gitlab-ci/            # GitLab CI configurations
│   └── scripts/              # Test and validation scripts
├── monitoring/                # Observability stack
│   ├── prometheus/           # Metrics and alerts
│   ├── grafana/              # Dashboards
│   ├── alertmanager/         # Alert routing
│   └── loki/                 # Log aggregation
└── ansible/                   # Configuration management
    ├── playbooks/
    └── roles/
```

## 🎯 Architecture Overview

### Development Environment
- **Platform:** Raspberry Pi 5 with Hailo-8 AI accelerator
- **Deployment:** Docker Compose
- **Services:** All services run locally
- **Database:** Local PostgreSQL, Redis, ClickHouse, MinIO

### Staging Environment
- **Platform:** AWS EKS (single region)
- **Deployment:** Kubernetes with Kustomize
- **Strategy:** Blue-green deployments
- **Scale:** 2-6 replicas with auto-scaling
- **Budget:** ~$500/month

### Production Environment
- **Platform:** AWS EKS (multi-region)
- **Deployment:** Kubernetes with Kustomize
- **Strategy:** Canary deployments (10% → 25% → 50% → 100%)
- **Scale:** 6-20 replicas with multi-metric HPA
- **High Availability:** Multi-AZ, auto-failover, disaster recovery
- **SLA:** 99.95% uptime, <200ms p95 latency
- **Budget:** ~$5000/month

## 🛠 Prerequisites

### Required Tools
- **Docker** >= 20.10
- **kubectl** >= 1.28
- **Terraform** >= 1.5.0
- **AWS CLI** >= 2.0
- **jq** >= 1.6
- **Python** >= 3.11

### Cloud Access
- AWS account with administrator access
- Configured AWS credentials (`~/.aws/credentials`)
- EKS cluster access (via IAM roles)

## 📦 Components

### 1. Infrastructure as Code (Terraform)

Automated provisioning of:
- VPC with public, private, and database subnets
- EKS cluster with multiple node groups
- RDS PostgreSQL with read replicas
- ElastiCache Redis with automatic failover
- S3 buckets with lifecycle policies
- KMS encryption keys
- CloudWatch logs and alarms

**Usage:**
```bash
cd deployment/terraform
terraform init
terraform plan -var-file=environments/staging.tfvars
terraform apply -var-file=environments/staging.tfvars
```

**Documentation:** [terraform/README.md](terraform/README.md)

### 2. Kubernetes Manifests

Production-ready Kubernetes resources:
- Deployments with health checks and security contexts
- Services (ClusterIP and headless)
- Horizontal Pod Autoscalers
- Ingress with AWS ALB controller
- PodDisruptionBudgets for high availability
- NetworkPolicies for security
- ConfigMaps and Secrets management

**Usage:**
```bash
# Deploy to staging
kubectl apply -k deployment/kubernetes/overlays/staging

# Deploy to production
kubectl apply -k deployment/kubernetes/overlays/production
```

**Documentation:** [kubernetes/README.md](kubernetes/README.md)

### 3. CI/CD Pipelines

Automated build, test, and deployment:
- **Build:** Docker image creation and push to ECR
- **Test:** Unit tests, integration tests, security scans
- **Security:** Trivy vulnerability scanning, Bandit linting
- **Deploy:** Automated deployment with approval gates
- **Canary:** Progressive rollout with automatic rollback
- **Notifications:** Slack/PagerDuty alerts

**Supported Platforms:**
- GitHub Actions
- GitLab CI
- Jenkins (planned)

**Documentation:** [ci-cd/README.md](ci-cd/README.md)

### 4. Monitoring and Observability

Comprehensive monitoring stack:
- **Prometheus:** Metrics collection and alerting
- **Grafana:** Visualization dashboards
- **Jaeger:** Distributed tracing
- **Loki:** Log aggregation
- **Alertmanager:** Alert routing and deduplication

**Pre-configured Dashboards:**
- KVA API Overview
- Infrastructure Metrics
- Database Performance
- SLA Compliance

**Documentation:** [monitoring/README.md](monitoring/README.md)

### 5. Master Deployment Orchestrator

Single script for end-to-end deployment:
- Pre-flight checks (prerequisites, credentials, health)
- Automated testing (unit, integration, smoke tests)
- Backup creation before deployment
- Infrastructure provisioning (Terraform)
- Application deployment (Kubernetes)
- Post-deployment validation
- Automatic rollback on failure

**Features:**
- Multi-environment support
- Dry-run mode
- Component-specific deployment
- Comprehensive logging
- Colored terminal output

## 🔒 Security

### Infrastructure Security
- **Network:** VPC isolation, security groups, network policies
- **Encryption:** KMS encryption for data at rest and in transit
- **Secrets:** AWS Secrets Manager for sensitive data
- **IAM:** Least privilege access with IRSA for pods
- **WAF:** AWS WAF for API protection

### Application Security
- **Authentication:** JWT tokens with OAuth2
- **Authorization:** RBAC for Kubernetes resources
- **Container Security:** Non-root containers, read-only filesystem
- **Scanning:** Automated vulnerability scanning with Trivy
- **Compliance:** SOC 2, ISO 27001, HIPAA, GDPR

## 📊 Monitoring and Alerts

### Key Metrics
- Request rate and latency (p50, p95, p99)
- Error rates (4xx, 5xx)
- CPU and memory usage
- Database connections and query performance
- Cache hit/miss ratios

### Critical Alerts
- API Down (> 2 minutes)
- High Error Rate (> 5%)
- SLA Violation (availability < 99.95%)
- Database Connection Failure
- Node Down

### Alert Channels
- **Critical:** PagerDuty (24/7 on-call)
- **Warning:** Slack (#alerts channel)
- **Info:** Email (ops team)

## 🧪 Testing Strategy

### Test Levels
1. **Unit Tests:** Individual component testing
2. **Integration Tests:** Inter-component communication
3. **Smoke Tests:** Basic health checks post-deployment
4. **Performance Tests:** Load and stress testing
5. **Security Tests:** Vulnerability scanning and penetration testing

### Test Execution
```bash
# Run all tests
pytest tests/ -v

# Run smoke tests
./deployment/ci-cd/scripts/smoke-tests.sh staging

# Run integration tests
./deployment/ci-cd/scripts/integration-tests.sh production

# Check deployment metrics
./deployment/ci-cd/scripts/check-metrics.sh production
```

## 🔄 Deployment Strategies

### Blue-Green Deployment (Staging)
1. Deploy new version to "green" environment
2. Run smoke tests
3. Switch traffic via Ingress
4. Monitor for issues
5. Remove "blue" environment

### Canary Deployment (Production)
1. Deploy to 10% of pods (5 minutes)
2. Monitor metrics and error rates
3. Gradually increase: 25% (15m) → 50% (30m) → 100%
4. Automatic rollback if error rate > 5%

## 🌐 Multi-Region Architecture

### Primary Region: us-east-1
- Active-active EKS cluster
- Primary RDS instance
- ElastiCache Redis cluster
- S3 primary bucket

### Secondary Region: us-west-2
- Hot standby EKS cluster
- RDS read replica
- S3 replication bucket
- Route53 health checks for automatic failover

### Disaster Recovery
- **RTO:** 1 hour (Recovery Time Objective)
- **RPO:** 15 minutes (Recovery Point Objective)
- **Automated Failover:** Route53 health checks
- **Manual Failover:** Runbook available

## 📈 Scaling

### Horizontal Pod Autoscaling
- **Staging:** 2-6 replicas based on CPU (70%)
- **Production:** 6-20 replicas based on CPU (65%) and memory (75%)

### Cluster Autoscaling
- Node groups scale based on pod requirements
- Min/max nodes defined per environment
- Spot instances for batch workloads (production)

### Database Scaling
- RDS storage auto-scaling
- Read replicas for read-heavy workloads
- Connection pooling for efficiency

## 🔧 Troubleshooting

### Common Issues

**Pods Not Starting:**
```bash
kubectl describe pod <pod-name> -n prime-spark
kubectl logs <pod-name> -n prime-spark --previous
```

**Deployment Failed:**
```bash
# Check rollout status
kubectl rollout status deployment/kva-api -n prime-spark

# Rollback if needed
kubectl rollout undo deployment/kva-api -n prime-spark
```

**High Latency:**
```bash
# Check metrics
./deployment/ci-cd/scripts/check-metrics.sh production

# View traces in Jaeger
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
```

**Database Connection Issues:**
```bash
# Check RDS security group
aws rds describe-db-instances --db-instance-identifier prime-spark-db

# Test connectivity from pod
kubectl exec -it <pod-name> -n prime-spark -- \
  psql -h <rds-endpoint> -U postgres -d prime_spark
```

## 📚 Documentation

- **Terraform:** [deployment/terraform/README.md](terraform/README.md)
- **Kubernetes:** [deployment/kubernetes/README.md](kubernetes/README.md)
- **Monitoring:** [deployment/monitoring/README.md](monitoring/README.md)
- **CI/CD:** [deployment/ci-cd/README.md](ci-cd/README.md)

## 🎓 Best Practices

1. **Infrastructure as Code:** All infrastructure changes via Terraform
2. **GitOps:** All deployment changes via Git
3. **Immutable Infrastructure:** Never modify running infrastructure
4. **Automated Testing:** All changes pass tests before deployment
5. **Monitoring First:** Deploy monitoring before applications
6. **Security by Default:** Security baked into every layer
7. **Documented Runbooks:** Procedures for common operations
8. **Regular Backups:** Automated backups with tested recovery
9. **Cost Optimization:** Right-sizing and spot instances where appropriate
10. **Continuous Improvement:** Regular reviews and optimization

## 🤝 Contributing

1. Create feature branch from `main`
2. Make changes and test locally
3. Run validation: `./deploy.sh validate`
4. Submit pull request with detailed description
5. Wait for CI/CD pipeline to pass
6. Get approval from team leads
7. Merge to `main`

## 📞 Support

- **Documentation:** [docs.prime-spark.ai](https://docs.prime-spark.ai)
- **Issues:** [GitHub Issues](https://github.com/prime-spark/ai/issues)
- **Slack:** #prime-spark-ops
- **Email:** ops@prime-spark.ai
- **On-Call:** PagerDuty escalation

## 📝 License

Proprietary - Prime Spark AI © 2025

---

**Made with ❤️ by the Prime Spark AI Team**
