# Prime Spark AI - Configuration Guide

This guide covers all configuration options for Prime Spark AI.

## Environment Variables

All configuration is managed through environment variables in the `.env` file.

### Edge Infrastructure

```bash
# Edge device IPs
EDGE_ROUTER_IP=192.168.1.1          # Pi4 OpenWRT router
EDGE_NAS_IP=192.168.1.49            # Argon EON NAS
CONTROL_PC_IP=192.168.1.100         # Control PC (Pi5 16GB + Hailo-8)
SPARK_AGENT_IP=192.168.1.92         # Spark Agent (Pi5 8GB)
```

### Cloud Infrastructure

```bash
# Cloud VM IPs
PRIMECORE1_IP=141.136.35.51         # Orchestration hub
PRIMECORE2_IP=                      # Memory layer (Supabase + Nextcloud)
PRIMECORE3_IP=                      # Voice processing
PRIMECORE4_IP=69.62.123.97          # 15 services (Ollama, ComfyUI, etc.)

# Ports
PRIMECORE1_PORT=443
PRIMECORE2_PORT=443
PRIMECORE3_PORT=443
PRIMECORE4_PORT=443
```

### VPN Configuration

```bash
VPN_TYPE=wireguard                  # VPN type (wireguard or zerotier)
WIREGUARD_PORT=51820                # WireGuard listen port
WIREGUARD_INTERFACE=wg0             # Interface name
VPN_SUBNET=10.8.0.0/24              # VPN subnet

# VPN IPs for each node
VPN_CONTROL_PC_IP=10.8.0.2
VPN_SPARK_AGENT_IP=10.8.0.3
VPN_PRIMECORE1_IP=10.8.0.11
VPN_PRIMECORE2_IP=10.8.0.12
VPN_PRIMECORE3_IP=10.8.0.13
VPN_PRIMECORE4_IP=10.8.0.14
```

### Memory Configuration

#### Tier 1: Local Cache (Redis)

```bash
REDIS_LOCAL_PORT=6379
REDIS_PASSWORD=change_me_in_production
REDIS_MAX_MEMORY=2gb
REDIS_EVICTION_POLICY=allkeys-lru   # LRU eviction when full
```

#### Tier 2: NAS Persistent Storage

```bash
NAS_SHARE_PATH=/mnt/nas
NAS_USERNAME=primeai
NAS_PASSWORD=change_me_in_production
```

#### Tier 3: Cloud Storage

```bash
# Supabase
SUPABASE_URL=
SUPABASE_KEY=

# MinIO (S3-compatible)
MINIO_ENDPOINT=http://69.62.123.97:9000
MINIO_ACCESS_KEY=change_me_in_production
MINIO_SECRET_KEY=change_me_in_production
MINIO_BUCKET=prime-spark-ai
```

### Ollama Configuration

```bash
OLLAMA_EDGE_URL=http://localhost:11434      # Edge Ollama instance
OLLAMA_CLOUD_URL=http://69.62.123.97:11434  # Cloud Ollama instance
OLLAMA_DEFAULT_MODEL=llama3.2:latest
```

### API Configuration

```bash
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_LOG_LEVEL=info
```

### Authentication

```bash
JWT_SECRET=change_me_to_random_256bit_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me_in_production
```

### Power Management

```bash
POWER_MODE=auto                     # auto, on-grid, or off-grid
BATTERY_MONITOR_ENABLED=true
BATTERY_LOW_THRESHOLD=20            # Percentage
BATTERY_CRITICAL_THRESHOLD=10       # Percentage
```

### Routing Configuration

```bash
ROUTING_STRATEGY=edge-first         # edge-first, cloud-first, or balanced
EDGE_TIMEOUT_SECONDS=5
CLOUD_FALLBACK_ENABLED=true
MAX_RETRIES=3
```

### Monitoring

```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3000
HEALTH_CHECK_INTERVAL=30
```

### Hailo AI Accelerator

```bash
HAILO_ENABLED=true
HAILO_DEVICE_ID=0
```

### Logging

```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/prime-spark-ai/app.log
```

## Routing Strategies

### Edge-First (Default)

- Always tries edge compute first
- Falls back to cloud if edge unavailable
- Best for privacy and low latency
- Power-aware (edge-only on battery)

### Cloud-First

- Prioritizes cloud compute
- Falls back to edge if cloud unavailable
- Best for heavy workloads
- Uses more network bandwidth

### Balanced

- Chooses endpoint with lowest latency
- Distributes load between edge and cloud
- Best for mixed workloads
- Adapts to network conditions

## Power Modes

### Auto (Default)

- Automatically switches based on power state
- On AC: Full edge + cloud capability
- On battery: Edge-first with power optimization
- Critical battery: Edge-only mode

### On-Grid

- Forces full edge + cloud capability
- Ignores battery state
- Use when always on AC power

### Off-Grid

- Forces edge-only operation
- No cloud fallback
- Use for air-gapped or off-grid scenarios

## Security Best Practices

1. **Change default passwords**: Update `ADMIN_PASSWORD`, `REDIS_PASSWORD`, etc.

2. **Generate secure JWT secret**:
   ```bash
   openssl rand -hex 32
   ```

3. **Use strong MinIO credentials**:
   ```bash
   # Generate random keys
   MINIO_ACCESS_KEY=$(openssl rand -hex 16)
   MINIO_SECRET_KEY=$(openssl rand -hex 32)
   ```

4. **Enable HTTPS**: Use a reverse proxy (nginx, Caddy) with Let's Encrypt

5. **Restrict CORS**: Update `allow_origins` in `api/main.py` for production

6. **VPN Security**: Keep WireGuard keys secure and rotate periodically

## Performance Tuning

### Redis Cache

- Increase `REDIS_MAX_MEMORY` for better caching on systems with more RAM
- Use `allkeys-lru` for general caching
- Use `volatile-lru` to preserve important keys

### API Workers

- Set `API_WORKERS` based on CPU cores: `cpu_cores * 2 + 1`
- On Pi5: 4 workers is optimal
- Monitor with `htop` and adjust as needed

### Health Check Interval

- Decrease for faster failure detection (more overhead)
- Increase for lower resource usage (slower detection)
- Default 30s is a good balance

## Troubleshooting

### VPN Issues

```bash
# Check VPN status
python vpn/manager.py status

# Restart VPN
sudo systemctl restart wg-quick@wg0

# Check logs
journalctl -u wg-quick@wg0 -f
```

### Memory Issues

```bash
# Check Redis
docker exec -it prime-spark-redis redis-cli -a $REDIS_PASSWORD INFO

# Check NAS mount
df -h /mnt/nas

# Test MinIO connection
curl $MINIO_ENDPOINT/minio/health/live
```

### API Issues

```bash
# Check API logs
docker-compose logs -f api

# Test health endpoint
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/api/health/detailed
```

## Advanced Configuration

### Custom Models

Add custom Ollama models to edge or cloud:

```bash
# On edge
ollama pull custom-model:latest

# On cloud
ssh primecore4 "ollama pull custom-model:latest"
```

### NAS Configuration

For NFS:
```bash
sudo mount -t nfs $EDGE_NAS_IP:/export/prime-spark /mnt/nas
```

For SMB/CIFS:
```bash
sudo mount -t cifs //$EDGE_NAS_IP/prime-spark /mnt/nas \
  -o username=$NAS_USERNAME,password=$NAS_PASSWORD
```

Add to `/etc/fstab` for persistent mounts.

### Monitoring with Prometheus

Start monitoring services:
```bash
docker-compose --profile monitoring up -d
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:8000/api/health/detailed`
3. Review this documentation
4. Open a GitHub issue with logs and configuration
