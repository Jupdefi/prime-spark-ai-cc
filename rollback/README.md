## Prime Spark AI Rollback System

Comprehensive rollback infrastructure for safely reverting deployments to previous states.

## Features

- **🔄 Full System Rollback**: Restore entire system to previous state
- **🎯 Service-Specific Rollback**: Rollback individual services
- **💾 Configuration Backup**: Automatic backup of all config files
- **🐳 Docker Image Tracking**: Version tracking for all containers
- **📦 Volume Backup**: Optional data volume backup
- **✅ Health Checks**: Service-specific health verification
- **📊 Logging Integration**: Full audit trail via logging system
- **🔒 Safety Features**: Dry-run mode and confirmation prompts

## Quick Start

### Create a Rollback Point

Before deploying changes, create a rollback point:

```bash
# Basic rollback point
./rollback/scripts/create_rollback_point.sh "Before v2.0 deployment"

# Include volume data (slower but complete)
./rollback/scripts/create_rollback_point.sh "Before migration" --include-volumes
```

### List Available Rollback Points

```bash
./rollback/scripts/list_rollback_points.sh
```

Example output:
```
Found 3 rollback point(s):

1. [rb-a1b2c3d4e5f6]
   Description: Before v2.0 deployment
   Created: 2025-11-05 17:30:00 UTC
   Services: redis, api, prometheus, grafana
   Images: 4
   Git commit: 6c3d2010

2. [rb-f6e5d4c3b2a1]
   Description: Before migration
   Created: 2025-11-04 14:20:00 UTC
   Services: redis, api, prometheus, grafana
   Images: 4
   Volumes: 3 backed up
```

### Rollback to a Specific Point

```bash
# Dry run first (recommended)
./rollback/scripts/rollback.sh rb-a1b2c3d4e5f6 --dry-run

# Perform actual rollback
./rollback/scripts/rollback.sh rb-a1b2c3d4e5f6
```

### Quick Rollback (Latest Point)

```bash
# Rollback to the most recent rollback point
./rollback/scripts/quick_rollback.sh
```

## Architecture

### Components

1. **RollbackManager** (`rollback_manager.py`)
   - Orchestrates all rollback operations
   - Manages rollback point lifecycle
   - Handles backup/restore of configs and volumes

2. **ServiceRollback** (`service_rollback.py`)
   - Service-specific rollback logic
   - Pre/post rollback hooks
   - Health verification

3. **Shell Scripts** (`scripts/`)
   - User-friendly command-line interface
   - Wrapper scripts for common operations

### Rollback Point Structure

```
rollback/backups/
├── rollback_index.json          # Master index
└── rb-a1b2c3d4e5f6/             # Rollback point directory
    ├── configs/                  # Configuration backups
    │   ├── docker-compose.yml
    │   ├── .env
    │   └── deployment_prometheus.yml
    └── volumes/                  # Volume backups (if included)
        ├── prime-spark-redis.tar.gz
        └── prime-spark-api.tar.gz
```

### Rollback Point Data

Each rollback point stores:

```json
{
  "id": "rb-a1b2c3d4e5f6",
  "timestamp": "2025-11-05T17:30:00.123456",
  "description": "Before v2.0 deployment",
  "services": ["redis", "api", "prometheus", "grafana"],
  "docker_images": {
    "redis": "redis:7-alpine",
    "api": "prime-spark-api:v1.5",
    "prometheus": "prom/prometheus:latest",
    "grafana": "grafana/grafana:latest"
  },
  "config_hashes": {
    "docker-compose.yml": "sha256:abc123...",
    ".env": "sha256:def456..."
  },
  "volumes": ["prime-spark-redis", "prime-spark-api"],
  "metadata": {
    "git_commit": "6c3d201...",
    "hostname": "raspberry-pi-5",
    "include_volumes": true
  }
}
```

## Usage

### Python API

```python
from rollback import RollbackManager

# Initialize manager
manager = RollbackManager(
    backup_dir="rollback/backups",
    max_rollback_points=10,
    project_root="."
)

# Create rollback point
rollback_point = manager.create_rollback_point(
    description="Before critical update",
    services=["api", "redis"],  # None = all services
    include_volumes=True
)

print(f"Created rollback point: {rollback_point.id}")

# List all rollback points
points = manager.list_rollback_points()
for point in points:
    print(f"{point.id}: {point.description}")

# Rollback
success = manager.rollback(
    rollback_id="rb-a1b2c3d4e5f6",
    dry_run=False
)

if success:
    print("Rollback completed successfully")
else:
    print("Rollback failed")

# Delete old rollback point
manager.delete_rollback_point("rb-old123456")
```

### Service-Specific Rollback

```python
from rollback.service_rollback import get_service_rollback

# Get service rollback handler
api_rollback = get_service_rollback("api", project_root=".")

# Perform service-specific rollback
if api_rollback.pre_rollback():
    if api_rollback.rollback():
        api_rollback.post_rollback()

        if api_rollback.verify_health():
            print("API rollback successful")
```

### Shell Commands

```bash
# Create rollback point
./rollback/scripts/create_rollback_point.sh "Description" [--include-volumes]

# List rollback points
./rollback/scripts/list_rollback_points.sh

# Rollback to specific point
./rollback/scripts/rollback.sh <rollback-id> [--dry-run]

# Quick rollback (most recent)
./rollback/scripts/quick_rollback.sh [--dry-run]

# Rollback individual service
./rollback/scripts/rollback_service.sh <service-name> [image-tag]

# Delete rollback point
./rollback/scripts/delete_rollback_point.sh <rollback-id>
```

## Service-Specific Details

### Redis

- **Pre-rollback**: Triggers Redis SAVE to persist data
- **Health check**: Verifies Redis PING response
- **Recovery time**: ~5 seconds

### API

- **Pre-rollback**: Checks Redis dependency
- **Post-rollback**: Waits for health endpoint (up to 30s)
- **Health check**: Verifies `/health` endpoint
- **Recovery time**: ~15-30 seconds

### Prometheus

- **Post-rollback**: Reloads configuration (HUP signal)
- **Health check**: Verifies `/-/healthy` endpoint
- **Recovery time**: ~10 seconds

### Grafana

- **Post-rollback**: 5-second initialization wait
- **Health check**: Verifies `/api/health` endpoint
- **Recovery time**: ~10 seconds

## Rollback Process

### Full System Rollback

1. **Stop Services**
   ```
   → Stopping redis...
   → Stopping api...
   → Stopping prometheus...
   → Stopping grafana...
   ```

2. **Restore Configurations**
   ```
   → Restoring docker-compose.yml
   → Restoring .env
   → Restoring prometheus.yml
   ```

3. **Restore Docker Images**
   ```
   → redis: redis:7-alpine
   → api: prime-spark-api:v1.5
   → prometheus: prom/prometheus:latest
   → grafana: grafana/grafana:latest
   ```

4. **Restore Volumes** (if backed up)
   ```
   → Restoring prime-spark-redis
   → Restoring prime-spark-api
   ```

5. **Start Services**
   ```
   → Starting redis...
   → Starting api...
   → Starting prometheus...
   → Starting grafana...
   ```

6. **Verify Rollback**
   ```
   → Verifying service health...
   ✓ All services healthy
   ```

## Safety Features

### Dry Run Mode

Test rollback without making changes:

```bash
./rollback/scripts/rollback.sh rb-a1b2c3d4e5f6 --dry-run
```

Output shows what would be done:
```
Rollback plan:
  1. Stop services: redis, api, prometheus, grafana
  2. Restore 3 configuration files
  3. Restore Docker images:
     - redis: redis:7-alpine
     - api: prime-spark-api:v1.5
  4. Restore 2 volumes
  5. Start services
```

### Confirmation Prompts

Interactive prompts prevent accidental rollbacks:

```
⚠️  WARNING: This will rollback the system to a previous state
Rollback point: Before v2.0 deployment
Created: 2025-11-05 17:30:00 UTC

Proceed with rollback? [yes/no]:
```

### Automatic Cleanup

- Keeps only the most recent 10 rollback points (configurable)
- Automatically removes oldest points when limit exceeded
- Manual deletion available via scripts

### Logging Integration

All rollback operations are logged:

```python
# Rollback start
logger.log_agent_decision(
    decision="Starting rollback to: rb-a1b2c3d4e5f6",
    reasoning="Restoring to state: Before v2.0 deployment"
)

# Rollback success
logger.log_agent_decision(
    decision="Rollback completed: rb-a1b2c3d4e5f6",
    reasoning="Successfully restored to previous state"
)

# Rollback failure
logger.log(
    change_type=ChangeType.DEPLOYMENT,
    description="Rollback failed: rb-a1b2c3d4e5f6",
    level=LogLevel.ERROR
)
```

## Best Practices

### 1. Create Rollback Points Before Deployments

```bash
# Before deploying
./rollback/scripts/create_rollback_point.sh "Before v2.0 deployment"

# Deploy changes
docker-compose up -d

# If something goes wrong
./rollback/scripts/quick_rollback.sh
```

### 2. Use Descriptive Names

Good:
```bash
./rollback/scripts/create_rollback_point.sh "Before database migration v2.0"
./rollback/scripts/create_rollback_point.sh "Stable production state 2025-11-05"
```

Bad:
```bash
./rollback/scripts/create_rollback_point.sh "test"
./rollback/scripts/create_rollback_point.sh "backup"
```

### 3. Include Volumes for Critical Updates

```bash
# For database schema changes, data migrations
./rollback/scripts/create_rollback_point.sh "Before migration" --include-volumes

# For config-only changes (faster)
./rollback/scripts/create_rollback_point.sh "Config update"
```

### 4. Test Rollback in Staging First

```bash
# In staging environment
./rollback/scripts/create_rollback_point.sh "Test rollback"
./rollback/scripts/rollback.sh rb-test123 --dry-run
./rollback/scripts/rollback.sh rb-test123
```

### 5. Always Dry Run First in Production

```bash
# 1. Dry run
./rollback/scripts/rollback.sh rb-a1b2c3d4e5f6 --dry-run

# 2. Review plan

# 3. Execute
./rollback/scripts/rollback.sh rb-a1b2c3d4e5f6
```

### 6. Verify After Rollback

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs --tail=100

# Verify endpoints
curl http://localhost:8000/health
```

## Integration with Deployment

### Automated Rollback Points

Add to your deployment script:

```bash
#!/bin/bash

# Create rollback point
echo "Creating rollback point..."
./rollback/scripts/create_rollback_point.sh "Before automated deployment"

# Deploy
echo "Deploying..."
docker-compose pull
docker-compose up -d

# Verify deployment
echo "Verifying deployment..."
sleep 10

if ! curl -f http://localhost:8000/health; then
    echo "Deployment failed, rolling back..."
    ./rollback/scripts/quick_rollback.sh --auto-confirm
    exit 1
fi

echo "Deployment successful"
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
steps:
  - name: Create rollback point
    run: |
      ./rollback/scripts/create_rollback_point.sh "Before CI/CD deployment"

  - name: Deploy
    run: |
      docker-compose up -d

  - name: Verify deployment
    run: |
      sleep 10
      curl -f http://localhost:8000/health || exit 1

  - name: Rollback on failure
    if: failure()
    run: |
      ./rollback/scripts/quick_rollback.sh --auto-confirm
```

## Troubleshooting

### Rollback Point Creation Failed

```bash
# Check disk space
df -h

# Check Docker status
docker ps

# Check permissions
ls -la rollback/backups/
```

### Rollback Failed

```bash
# Check service logs
docker-compose logs

# Manually stop services
docker-compose down

# Try rollback again
./rollback/scripts/rollback.sh <rollback-id>
```

### Service Not Starting After Rollback

```bash
# Check individual service
docker-compose up <service-name>

# Check logs
docker-compose logs <service-name>

# Restart specific service
./rollback/scripts/rollback_service.sh <service-name>
```

### Volume Restore Failed

```bash
# Check volume exists
docker volume ls

# Manually restore volume
docker run --rm \
  -v <volume-name>:/data \
  -v $(pwd)/rollback/backups/<rollback-id>/volumes:/backup \
  alpine \
  sh -c "rm -rf /data/* && tar xzf /backup/<volume-name>.tar.gz -C /data"
```

## Configuration

### Maximum Rollback Points

Default: 10

Change in code:

```python
manager = RollbackManager(max_rollback_points=20)
```

### Backup Directory

Default: `rollback/backups`

Change in code:

```python
manager = RollbackManager(backup_dir="custom/backup/path")
```

### Volume Backup Behavior

Include volumes by default:

```bash
# Modify create_rollback_point.sh
INCLUDE_VOLUMES=true  # Change from false to true
```

## Performance Considerations

### Rollback Point Creation Time

- **Without volumes**: ~5-10 seconds
- **With volumes**: ~30 seconds to several minutes (depends on data size)

### Rollback Execution Time

- **Config-only rollback**: ~30 seconds
- **With volume restore**: ~1-5 minutes (depends on data size)

### Storage Requirements

- **Config-only**: ~100 KB per rollback point
- **With volumes**: Varies (typically 10 MB - 1 GB per point)

### Recommendations

- Use volume backup only for critical updates
- Keep 5-10 rollback points for fast deployments
- Use volume backup for 2-3 most recent critical points

## API Reference

See individual module documentation:

- [RollbackManager](./rollback_manager.py)
- [ServiceRollback](./service_rollback.py)

## License

Part of Prime Spark AI platform. See LICENSE for details.
