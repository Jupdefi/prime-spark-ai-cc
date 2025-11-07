# Prime Spark AI - Monitoring and Observability

Comprehensive monitoring and observability stack for Prime Spark AI using Prometheus, Grafana, Jaeger, and Loki.

## Components

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Jaeger**: Distributed tracing
- **Loki**: Log aggregation
- **Alertmanager**: Alert routing and management

## Quick Start

### Deploy Monitoring Stack

```bash
# Deploy to Kubernetes
kubectl apply -k deployment/monitoring/k8s/

# Or use Helm
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values deployment/monitoring/values.yaml
```

### Access Dashboards

**Grafana:**
```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
# Access at http://localhost:3000
# Default credentials: admin/admin
```

**Prometheus:**
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Access at http://localhost:9090
```

**Jaeger:**
```bash
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
# Access at http://localhost:16686
```

## Metrics

### KVA API Metrics

**Request Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_flight` - Current requests being processed

**Application Metrics:**
- `kva_storage_operations_total` - Storage operations count
- `kva_storage_latency_seconds` - Storage operation latency
- `kva_analytics_queries_total` - Analytics query count
- `kva_cache_hits_total` - Cache hit rate
- `kva_cache_misses_total` - Cache miss rate

**System Metrics:**
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `process_open_fds` - Open file descriptors

### Infrastructure Metrics

**Kubernetes:**
- Pod CPU/memory usage
- Node resources
- Cluster capacity

**Databases:**
- PostgreSQL connections, queries, cache hit ratio
- Redis operations, memory usage, evictions
- ClickHouse queries, inserts, merges

## Dashboards

### Pre-configured Dashboards

1. **KVA Overview** (`kva-overview.json`)
   - Request rate and latency
   - Error rates
   - Active pods
   - Resource usage

2. **Infrastructure** (`infrastructure.json`)
   - Node metrics
   - Cluster capacity
   - Network I/O
   - Disk usage

3. **Database Performance** (`database.json`)
   - PostgreSQL metrics
   - Redis metrics
   - ClickHouse metrics
   - Query performance

4. **SLA Dashboard** (`sla.json`)
   - Availability (99.95% target)
   - Latency percentiles
   - Error budget
   - Incident timeline

### Importing Dashboards

```bash
# Via Grafana UI: Home -> Dashboards -> Import

# Or via API:
curl -X POST http://grafana/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @deployment/monitoring/grafana/dashboards/kva-overview.json
```

## Alerts

### Alert Rules

**Critical Alerts:**
- API Down (> 2 minutes)
- High Error Rate (> 5%)
- Database Connection Failure
- Node Down
- SLA Violation

**Warning Alerts:**
- High Latency (p95 > 500ms)
- High CPU Usage (> 80%)
- High Memory Usage (> 85%)
- High Disk Usage (> 90%)

### Alert Configuration

Edit `prometheus/alerts.yml` to customize alert thresholds and add new rules.

### Alert Routing

Configure Alertmanager routes in `alertmanager/config.yml`:

```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: <key>
  - name: 'slack'
    slack_configs:
      - api_url: <webhook>
        channel: '#alerts'
```

## Distributed Tracing

### Jaeger Configuration

Traces are automatically collected from:
- HTTP requests (via OpenTelemetry instrumentation)
- Database queries
- Cache operations
- External API calls

### Viewing Traces

1. Access Jaeger UI at http://localhost:16686
2. Select "kva-api" service
3. Search traces by:
   - Operation name
   - Tags
   - Time range
   - Duration

### Trace Sampling

**Development:** 100% sampling
**Staging:** 10% sampling
**Production:** 1% sampling

Configure in application:
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

# Configure sampling
tracer_provider = TracerProvider(
    sampler=TraceIdRatioBased(0.01)  # 1% sampling
)
```

## Log Aggregation

### Loki Integration

Logs are collected from:
- Application logs (stdout/stderr)
- Kubernetes events
- System logs

### Querying Logs

**LogQL Examples:**

```logql
# All logs from kva-api
{app="kva-api"}

# Error logs only
{app="kva-api"} |= "ERROR"

# Filter by time range
{app="kva-api"} |= "ERROR" | json | line_format "{{.message}}"

# Count errors per minute
rate({app="kva-api"} |= "ERROR" [1m])
```

### Log Retention

- **Development:** 7 days
- **Staging:** 30 days
- **Production:** 90 days

## Performance Monitoring

### SLA Targets

- **Availability:** 99.95%
- **Latency P95:** < 200ms
- **Latency P99:** < 500ms
- **Error Rate:** < 0.1%

### Monitoring SLAs

View SLA compliance in Grafana dashboard "SLA Overview".

Error budget calculation:
```
Error Budget = (1 - SLA) * Total Requests
Example: (1 - 0.9995) * 1M = 500 requests
```

## Troubleshooting

### High Memory Usage

1. Check Grafana dashboard for memory trends
2. View detailed pod metrics:
   ```bash
   kubectl top pod -n prime-spark -l app=kva-api
   ```
3. Check for memory leaks in traces
4. Review application logs for OOM errors

### High Latency

1. Check Jaeger for slow traces
2. Identify bottlenecks (database, cache, external APIs)
3. Review Prometheus metrics for resource constraints
4. Check database query performance

### Missing Metrics

1. Verify Prometheus targets:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   # Visit http://localhost:9090/targets
   ```
2. Check pod annotations for Prometheus scraping
3. Verify metrics endpoint is accessible:
   ```bash
   kubectl exec -it <pod> -- curl localhost:8002/metrics
   ```

## Best Practices

1. **Alert Fatigue:** Set appropriate thresholds to avoid noisy alerts
2. **Dashboard Organization:** Group related metrics together
3. **Log Levels:** Use appropriate log levels (DEBUG, INFO, WARN, ERROR)
4. **Trace Sampling:** Adjust sampling rate based on traffic volume
5. **Metric Cardinality:** Avoid high-cardinality labels
6. **Resource Limits:** Set Prometheus/Grafana resource limits appropriately

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
