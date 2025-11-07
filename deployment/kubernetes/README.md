# Prime Spark AI - Kubernetes Manifests

Kubernetes manifests for deploying Prime Spark AI to EKS using Kustomize.

## Structure

```
kubernetes/
├── base/                    # Base Kubernetes resources
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment-kva-api.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── serviceaccount.yaml
│   ├── poddisruptionbudget.yaml
│   └── networkpolicy.yaml
└── overlays/               # Environment-specific overlays
    ├── dev/
    ├── staging/
    └── production/
```

## Prerequisites

- kubectl configured with EKS cluster access
- kustomize >= 4.0.0 (or kubectl with kustomize support)
- AWS Load Balancer Controller installed in cluster
- Metrics Server installed for HPA

## Quick Start

### Deploy to Staging

```bash
kubectl apply -k deployment/kubernetes/overlays/staging
```

### Deploy to Production

```bash
kubectl apply -k deployment/kubernetes/overlays/production
```

### Verify Deployment

```bash
kubectl get pods -n prime-spark
kubectl get svc -n prime-spark
kubectl get ingress -n prime-spark
```

## Components

### Base Resources

**Deployment (deployment-kva-api.yaml)**
- KVA API pods with health checks
- Resource requests and limits
- Security context (non-root, read-only filesystem)
- Volume mounts for cache

**Service (service.yaml)**
- ClusterIP service for internal communication
- Headless service for StatefulSet-like behavior
- Metrics endpoint for Prometheus

**HorizontalPodAutoscaler (hpa.yaml)**
- CPU and memory-based auto-scaling
- Min: 2, Max: 20 replicas (base)
- Scale-up/down policies for stability

**Ingress (ingress.yaml)**
- AWS ALB integration
- HTTPS with ACM certificate
- Health check configuration

**PodDisruptionBudget (poddisruptionbudget.yaml)**
- Ensures minimum 2 pods during disruptions
- Prevents complete service outage during node maintenance

**NetworkPolicy (networkpolicy.yaml)**
- Restricts traffic to/from KVA API pods
- Allows ingress from ALB
- Allows egress to databases and external APIs

### Environment Overlays

**Staging**
- 2-6 replicas
- Lower resource limits (250m CPU, 512Mi memory)
- Debug logging
- Development image tag

**Production**
- 6-20 replicas
- Higher resource limits (1000m CPU, 2Gi memory)
- Info logging
- Semantic version tag
- Pod anti-affinity for high availability

## Configuration

### Secrets

Update `base/secret.yaml` with actual values or use External Secrets Operator:

```bash
kubectl create secret generic kva-secrets \
  --from-literal=JWT_SECRET=your-secret \
  --from-literal=POSTGRES_PASSWORD=your-password \
  -n prime-spark
```

### ConfigMap

Environment variables are stored in `base/configmap.yaml`. Overlay-specific values are merged in kustomization.yaml.

### Ingress Certificate

Update the certificate ARN in `base/ingress.yaml`:
```yaml
alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:REGION:ACCOUNT:certificate/ID"
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment kva-api --replicas=5 -n prime-spark
```

### Auto-Scaling

HPA automatically scales based on CPU/memory metrics. View HPA status:

```bash
kubectl get hpa -n prime-spark
kubectl describe hpa kva-api-hpa -n prime-spark
```

## Monitoring

### Pod Logs

```bash
kubectl logs -f deployment/kva-api -n prime-spark
kubectl logs -f deployment/kva-api -n prime-spark --all-containers
```

### Pod Status

```bash
kubectl get pods -n prime-spark -o wide
kubectl describe pod <pod-name> -n prime-spark
```

### Metrics

Prometheus scrapes metrics from pods via annotations:
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8002"
prometheus.io/path: "/metrics"
```

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n prime-spark
kubectl logs <pod-name> -n prime-spark --previous
```

Common issues:
- Image pull errors: Check image name and credentials
- CrashLoopBackOff: Check application logs
- Pending: Check node resources and scheduling constraints

### Service Not Accessible

```bash
kubectl get svc -n prime-spark
kubectl get endpoints -n prime-spark
```

Test service internally:
```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n prime-spark -- \
  curl http://kva-api:8002/health
```

### Ingress Not Working

```bash
kubectl describe ingress kva-api-ingress -n prime-spark
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

Verify ALB created:
```bash
aws elbv2 describe-load-balancers --region us-east-1
```

## Blue-Green Deployment

Use Kustomize to create blue/green deployments:

```bash
# Deploy green version
kubectl apply -k overlays/production -n prime-spark-green

# Switch traffic via Ingress
kubectl patch ingress kva-api-ingress -n prime-spark \
  --type=json -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "kva-api-green"}]'

# Remove blue version
kubectl delete -k overlays/production -n prime-spark-blue
```

## Canary Deployment

Use Argo Rollouts or Flagger for automated canary deployments:

```bash
kubectl apply -f rollout.yaml
kubectl argo rollouts set image kva-api kva-api=prime-spark/kva-api:v1.1.0
```

## Database Migrations

Run migrations as Kubernetes Jobs before deployment:

```bash
kubectl apply -f jobs/db-migrate.yaml
kubectl wait --for=condition=complete job/db-migrate -n prime-spark
```

## Cleanup

```bash
kubectl delete -k overlays/staging
kubectl delete namespace prime-spark
```

## Best Practices

1. **Resource Limits**: Always set requests and limits
2. **Health Checks**: Configure liveness and readiness probes
3. **Security**: Use NetworkPolicy, non-root containers, read-only filesystem
4. **High Availability**: Use PodDisruptionBudget and anti-affinity
5. **Monitoring**: Expose metrics and use structured logging
6. **Secrets**: Never commit secrets to git, use External Secrets Operator
7. **Rolling Updates**: Use maxUnavailable and maxSurge for controlled rollouts

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
