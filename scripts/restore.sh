#!/bin/bash
# Prime Spark AI - Automated Restore Script
#
# Restores system from backup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if backup path provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_path>"
    echo ""
    echo "Available backups:"
    ls -lth /mnt/nas/backups/prime-spark/ | grep "^d" | head -10
    exit 1
fi

BACKUP_PATH="$1"

if [ ! -d "$BACKUP_PATH" ]; then
    error "Backup path not found: $BACKUP_PATH"
    exit 1
fi

log "Restoring from backup: $BACKUP_PATH"

# Verify backup integrity
if [ -f "$BACKUP_PATH/manifest.json" ]; then
    log "Backup manifest found"
    cat "$BACKUP_PATH/manifest.json"
else
    warn "No manifest found, proceeding anyway"
fi

# Confirm restore
echo ""
echo -e "${RED}WARNING: This will restore system from backup and OVERWRITE existing data!${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log "Restore cancelled"
    exit 0
fi

# 1. Restore PostgreSQL
log "Restoring PostgreSQL..."
if [ -f "$BACKUP_PATH/postgres_all.sql.gz" ]; then
    # Stop services that depend on PostgreSQL
    docker-compose -f /home/pironman5/prime-spark-ai/docker-compose.enterprise.yml stop api

    # Restore
    gunzip -c "$BACKUP_PATH/postgres_all.sql.gz" | docker exec -i prime-spark-postgres psql -U postgres
    log "✓ PostgreSQL restored"
else
    warn "PostgreSQL backup not found, skipping"
fi

# 2. Restore TimescaleDB
log "Restoring TimescaleDB..."
if [ -f "$BACKUP_PATH/timescaledb_analytics.sql.gz" ]; then
    gunzip -c "$BACKUP_PATH/timescaledb_analytics.sql.gz" | docker exec -i prime-spark-timescaledb psql -U postgres prime_spark_analytics
    log "✓ TimescaleDB restored"
else
    warn "TimescaleDB backup not found, skipping"
fi

# 3. Restore Redis
log "Restoring Redis..."
if [ -f "$BACKUP_PATH/redis_dump.rdb" ]; then
    docker-compose -f /home/pironman5/prime-spark-ai/docker-compose.enterprise.yml stop redis
    docker cp "$BACKUP_PATH/redis_dump.rdb" prime-spark-redis:/data/dump.rdb
    docker-compose -f /home/pironman5/prime-spark-ai/docker-compose.enterprise.yml start redis
    log "✓ Redis restored"
else
    warn "Redis backup not found, skipping"
fi

# 4. Restore MinIO
log "Restoring MinIO object storage..."
if [ -d "$BACKUP_PATH/minio" ]; then
    if command -v mc &> /dev/null; then
        mc alias set local http://localhost:9000 minioadmin minioadmin
        mc mirror --overwrite "$BACKUP_PATH/minio/models/" local/models/
        mc mirror --overwrite "$BACKUP_PATH/minio/data/" local/data/
        log "✓ MinIO restored"
    else
        warn "MinIO client not installed, skipping"
    fi
else
    warn "MinIO backup not found, skipping"
fi

# 5. Restore Configuration
log "Restoring configuration files..."
if [ -d "$BACKUP_PATH/config" ]; then
    cp -r "$BACKUP_PATH/config/config" /home/pironman5/prime-spark-ai/ 2>/dev/null || true
    cp "$BACKUP_PATH/config/.env" /home/pironman5/prime-spark-ai/.env 2>/dev/null || true
    log "✓ Configuration restored"
else
    warn "Configuration backup not found, skipping"
fi

# 6. Restore ML Models
log "Restoring ML models..."
if [ -f "$BACKUP_PATH/models.tar.gz" ]; then
    mkdir -p /home/pironman5/prime-spark-ai/models
    tar -xzf "$BACKUP_PATH/models.tar.gz" -C /home/pironman5/prime-spark-ai/models/
    log "✓ Models restored"
else
    warn "Models backup not found, skipping"
fi

# 7. Restore Edge Storage
log "Restoring edge storage..."
if [ -f "$BACKUP_PATH/edge_storage.tar.gz" ]; then
    tar -xzf "$BACKUP_PATH/edge_storage.tar.gz" -C /tmp/
    log "✓ Edge storage restored"
else
    warn "Edge storage backup not found, skipping"
fi

# 8. Restart all services
log "Restarting all services..."
docker-compose -f /home/pironman5/prime-spark-ai/docker-compose.enterprise.yml restart
log "✓ Services restarted"

# 9. Verify restoration
log "Verifying restoration..."
sleep 10  # Wait for services to start

# Check PostgreSQL
if docker exec prime-spark-postgres psql -U postgres -c "SELECT 1" &>/dev/null; then
    log "✓ PostgreSQL is running"
else
    error "PostgreSQL verification failed"
fi

# Check Redis
if docker exec prime-spark-redis redis-cli PING &>/dev/null; then
    log "✓ Redis is running"
else
    error "Redis verification failed"
fi

log ""
log "=========================================="
log "RESTORE COMPLETED"
log "=========================================="
log "Backup path: $BACKUP_PATH"
log "Please verify system functionality"
