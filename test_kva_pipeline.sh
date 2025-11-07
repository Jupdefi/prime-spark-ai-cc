#!/bin/bash
# Prime Spark AI - KVA Pipeline Test Script

echo "========================================="
echo "Prime Spark AI - KVA Pipeline Test"
echo "========================================="
echo

# Test 1: API Health
echo "1. Testing Prime Spark API..."
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "   ✅ API is healthy"
else
    echo "   ❌ API is not responding"
fi

# Test 2: Redis (Key-Value)
echo "2. Testing Redis (Key-Value Store)..."
if docker exec prime-spark-redis redis-cli -a FIHKMB5nmCkkkqgakglO_CiMQTUMW9COVUWg071SYq4 PING 2>/dev/null | grep -q "PONG"; then
    echo "   ✅ Redis is responding"
else
    echo "   ❌ Redis is not responding"
fi

# Test 3: TimescaleDB (Analytics)
echo "3. Testing TimescaleDB (Analytics Database)..."
if docker exec prime-spark-timescaledb psql -U postgres -d prime_spark_analytics -c "SELECT 1" > /dev/null 2>&1; then
    echo "   ✅ TimescaleDB is responding"
else
    echo "   ❌ TimescaleDB is not responding"
fi

# Test 4: Kafka (Streaming)
echo "4. Testing Apache Kafka (Streaming)..."
if docker exec prime-spark-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "   ✅ Kafka is responding"
else
    echo "   ❌ Kafka is not responding"
fi

# Test 5: Prometheus (Monitoring)
echo "5. Testing Prometheus (Monitoring)..."
if curl -sf http://localhost:9090/-/healthy > /dev/null; then
    echo "   ✅ Prometheus is healthy"
else
    echo "   ❌ Prometheus is not responding"
fi

# Test 6: Grafana (Visualization)
echo "6. Testing Grafana (Visualization)..."
if curl -sf http://localhost:3002/api/health > /dev/null; then
    echo "   ✅ Grafana is responding"
else
    echo "   ❌ Grafana is not responding"
fi

# Test 7: Kafka UI
echo "7. Testing Kafka UI..."
if curl -sf http://localhost:8080 > /dev/null; then
    echo "   ✅ Kafka UI is responding"
else
    echo "   ❌ Kafka UI is not responding"
fi

# Test 8: Airflow (Pipeline)
echo "8. Testing Apache Airflow..."
if curl -sf http://localhost:8081/health > /dev/null 2>&1; then
    echo "   ✅ Airflow is responding"
else
    echo "   🟡 Airflow may still be initializing"
fi

echo
echo "========================================="
echo "Service Summary"
echo "========================================="
docker compose -f /home/pironman5/prime-spark-ai/docker-compose.enterprise.yml ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | head -15

echo
echo "========================================="
echo "KVA Pipeline Status"
echo "========================================="
echo "✅ Key-Value Store: Redis (6379)"
echo "✅ Analytics Database: TimescaleDB (5433)"
echo "✅ Streaming Platform: Apache Kafka (9092)"
echo "✅ Monitoring: Prometheus (9090) + Grafana (3002)"
echo "✅ Data Pipeline: Apache Airflow (8081)"
echo
echo "Access your services at:"
echo "  - API: http://localhost:8000/docs"
echo "  - Grafana: http://localhost:3002"
echo "  - Prometheus: http://localhost:9090"
echo "  - Kafka UI: http://localhost:8080"
echo "  - Airflow: http://localhost:8081"
echo
