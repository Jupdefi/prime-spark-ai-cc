# Prime Spark AI - Testing Strategy

## Overview

Comprehensive testing strategy covering unit, integration, end-to-end, and load testing for the Prime Spark AI platform.

---

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_memory.py     # Memory tier tests
│   ├── test_routing.py    # Routing logic tests
│   ├── test_auth.py       # Authentication tests
│   └── test_agents.py     # Agent coordination tests
├── integration/            # Integration tests between services
│   ├── test_api.py        # API endpoint tests
│   ├── test_streaming.py  # Kafka integration tests
│   ├── test_database.py   # TimescaleDB tests
│   └── test_pipeline.py   # Airflow pipeline tests
├── e2e/                    # End-to-end user scenarios
│   ├── test_data_flow.py  # Complete data pipeline
│   ├── test_model_deploy.py # ML model deployment
│   └── test_failover.py   # Failover scenarios
├── load/                   # Performance and load tests
│   ├── locustfile.py      # Locust load tests
│   └── benchmarks.py      # Performance benchmarks
└── fixtures/               # Test data and mocks
    ├── mock_data.py
    └── test_configs.py
```

---

## 1. Unit Testing

### Purpose
Test individual components in isolation without external dependencies.

### Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run unit tests
pytest tests/unit/ -v --cov=. --cov-report=html
```

### Example: Memory Tier Tests

```python
# tests/unit/test_memory.py

import pytest
import asyncio
from memory.memory_manager import MemoryManager, MemoryTier

@pytest.fixture
async def memory_manager():
    """Create memory manager for testing"""
    manager = MemoryManager()
    yield manager
    # Cleanup
    await manager.cache.flush()

@pytest.mark.asyncio
async def test_memory_set_and_get(memory_manager):
    """Test basic set/get operations"""
    key = "test_key"
    value = {"data": "test_value"}

    # Set in memory
    success = await memory_manager.set(key, value)
    assert success is True

    # Get from memory
    result = await memory_manager.get(key)
    assert result == value

@pytest.mark.asyncio
async def test_memory_tiering(memory_manager):
    """Test automatic tier fallback"""
    key = "tiered_key"
    value = {"tier": "test"}

    # Set with NAS persistence
    await memory_manager.set(key, value, persist_to_nas=True)

    # Clear cache (Tier 1)
    await memory_manager.cache.delete(key)

    # Should retrieve from Tier 2 (NAS) and backfill Tier 1
    result = await memory_manager.get(key)
    assert result == value

    # Verify Tier 1 was backfilled
    cached = await memory_manager.cache.exists(key)
    assert cached is True

@pytest.mark.asyncio
async def test_memory_delete_all_tiers(memory_manager):
    """Test deletion across all tiers"""
    key = "delete_test"
    value = {"to": "delete"}

    # Set in all tiers
    await memory_manager.set(key, value, persist_to_nas=True)
    await memory_manager.persist_to_cloud(key, value)

    # Delete from all tiers
    success = await memory_manager.delete(key, all_tiers=True)
    assert success is True

    # Verify deleted from all tiers
    result = await memory_manager.get(key, max_tier=MemoryTier.CLOUD)
    assert result is None
```

### Test Coverage Targets
- Memory Manager: 90%+
- Routing Logic: 90%+
- Authentication: 95%+
- Agent Coordination: 85%+
- Power Management: 80%+

---

## 2. Integration Testing

### Purpose
Test interactions between multiple components and external services.

### Setup

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v --asyncio-mode=auto

# Stop test services
docker-compose -f docker-compose.test.yml down
```

### Test Environment

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"  # Different port to avoid conflicts

  test-postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"

  test-kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: test-zookeeper:2181
      # ... (same as production but test instance)
```

### Example: API Integration Tests

```python
# tests/integration/test_api.py

import pytest
import httpx
import asyncio
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_USER = {"username": "test_admin", "password": "test_password"}

@pytest.fixture
async def auth_token():
    """Get authentication token for tests"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        assert response.status_code == 200
        return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Create auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}

class TestAPIAuthentication:
    """Test authentication flows"""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json=TEST_USER
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": "wrong", "password": "wrong"}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/auth/me")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_auth(self, auth_headers):
        """Test accessing protected endpoint with valid token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == TEST_USER["username"]

class TestAPIMemoryOperations:
    """Test memory API operations"""

    @pytest.mark.asyncio
    async def test_memory_crud_operations(self, auth_headers):
        """Test complete CRUD flow for memory operations"""
        async with httpx.AsyncClient() as client:
            test_key = f"test_{datetime.now().timestamp()}"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}

            # Create
            response = await client.post(
                f"{BASE_URL}/api/memory/set",
                json={"key": test_key, "value": test_value},
                headers=auth_headers
            )
            assert response.status_code == 200

            # Read
            response = await client.post(
                f"{BASE_URL}/api/memory/get",
                json={"key": test_key},
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["value"] == test_value

            # Delete
            response = await client.delete(
                f"{BASE_URL}/api/memory/{test_key}",
                headers=auth_headers
            )
            assert response.status_code == 200

            # Verify deleted
            response = await client.post(
                f"{BASE_URL}/api/memory/get",
                json={"key": test_key},
                headers=auth_headers
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_memory_stats(self, auth_headers):
        """Test memory statistics endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/memory/stats",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "tier1_local_cache" in data
            assert "tier2_nas_storage" in data
            assert "tier3_cloud_storage" in data

class TestAPIAgentCoordination:
    """Test agent coordination API"""

    @pytest.mark.asyncio
    async def test_task_submission_and_status(self, auth_headers):
        """Test task submission and status checking"""
        async with httpx.AsyncClient() as client:
            # Submit task
            response = await client.post(
                f"{BASE_URL}/api/tasks/submit",
                json={
                    "type": "test_task",
                    "payload": {"message": "test"},
                    "priority": "normal"
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            task_id = response.json()["task_id"]

            # Check status
            response = await client.get(
                f"{BASE_URL}/api/tasks/{task_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert data["status"] in ["pending", "assigned", "in_progress", "completed"]

    @pytest.mark.asyncio
    async def test_agent_status(self, auth_headers):
        """Test agent status endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/agents/status",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data
            assert "tasks" in data
            assert len(data["agents"]) > 0

class TestAPILLMInference:
    """Test LLM inference API"""

    @pytest.mark.asyncio
    async def test_llm_generate(self, auth_headers):
        """Test LLM generation endpoint"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/llm/generate",
                json={
                    "prompt": "Say hello in one word",
                    "model": "llama3.2:latest",
                    "max_tokens": 10,
                    "use_cache": False
                },
                headers=auth_headers
            )
            # May return 200 (success) or 500 (Ollama not running)
            assert response.status_code in [200, 500]

            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert "location" in data
                assert data["location"] in ["edge_local", "cloud_core4"]

    @pytest.mark.asyncio
    async def test_llm_models_list(self, auth_headers):
        """Test listing available models"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/llm/models",
                headers=auth_headers
            )
            assert response.status_code in [200, 500]

class TestAPIHealthChecks:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_basic_health(self):
        """Test basic health endpoint (no auth required)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_detailed_health(self, auth_headers):
        """Test detailed health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/health/detailed",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "overall_status" in data
            assert "components" in data
```

### Integration Test Scenarios

1. **Authentication Flow**
   - Login/logout
   - Token validation
   - Token expiration
   - Role-based access

2. **Data Pipeline**
   - Kafka publish/consume
   - TimescaleDB insert/query
   - Airflow DAG execution
   - Data sync service

3. **Memory Operations**
   - Three-tier storage
   - Cache hit/miss
   - Tier fallback
   - Backfill

4. **Agent Coordination**
   - Task submission
   - Task execution
   - Load balancing
   - Health monitoring

5. **Routing Logic**
   - Edge-first routing
   - Cloud fallback
   - Power-aware routing
   - Health-based routing

---

## 3. End-to-End Testing

### Purpose
Test complete user workflows from start to finish.

### Example: Complete Data Pipeline E2E Test

```python
# tests/e2e/test_data_pipeline.py

import pytest
import asyncio
import httpx
from datetime import datetime, timedelta

class TestCompleteDataPipeline:
    """Test end-to-end data flow"""

    @pytest.mark.asyncio
    async def test_telemetry_data_pipeline(self):
        """
        Test: Edge device → Kafka → TimescaleDB → Grafana

        Steps:
        1. Publish telemetry to Kafka
        2. Wait for data sync service to process
        3. Query TimescaleDB to verify data arrived
        4. Verify data can be queried via API
        """
        from streaming.kafka_manager import get_kafka_manager
        from analytics.timeseries_db import timescale_db

        # Step 1: Publish telemetry
        kafka = get_kafka_manager(["localhost:9092"])
        device_id = "test-device-1"

        await kafka.send_message(
            topic='edge.telemetry',
            message={
                'device_id': device_id,
                'metrics': {
                    'cpu_usage': 75.5,
                    'memory_usage': 82.3
                }
            },
            key=device_id
        )

        # Step 2: Wait for processing
        await asyncio.sleep(5)

        # Step 3: Verify in database
        metrics = await timescale_db.query_device_metrics(
            device_id=device_id,
            metric_name='cpu_usage',
            start_time=datetime.now() - timedelta(minutes=5)
        )

        assert len(metrics) > 0
        assert metrics[0]['value'] == 75.5

        # Step 4: Verify via API
        async with httpx.AsyncClient() as client:
            # (Would require analytics API endpoint)
            pass

class TestMLModelDeployment:
    """Test complete ML model deployment flow"""

    @pytest.mark.asyncio
    async def test_model_deployment_pipeline(self):
        """
        Test: Train → Log → Register → Deploy → Inference

        Steps:
        1. Log model to MLflow
        2. Register model version
        3. Deploy to edge
        4. Run inference
        5. Track results in TimescaleDB
        """
        # Implementation would test actual model deployment
        pass

class TestFailoverScenario:
    """Test system failover capabilities"""

    @pytest.mark.asyncio
    async def test_edge_to_cloud_failover(self):
        """
        Test: Edge service down → Automatic cloud fallback

        Steps:
        1. Verify edge service is healthy
        2. Make successful edge request
        3. Stop edge service
        4. Make request (should fallback to cloud)
        5. Restart edge service
        6. Verify requests return to edge
        """
        # Implementation would test actual failover
        pass
```

---

## 4. Load Testing

### Purpose
Test system performance under load and identify bottlenecks.

### Setup

```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Web UI: http://localhost:8089
```

### Load Test Scenarios

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between, events
import time

class PrimeSparkUser(HttpUser):
    """Simulated user for load testing"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when user starts - login and get token"""
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "test_password"
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Login failed: {response.status_code}")
            self.environment.runner.quit()

    @task(10)  # Weight: 10 (most common)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health", name="/health")

    @task(5)  # Weight: 5
    def memory_operations(self):
        """Memory set/get operations"""
        import uuid
        key = f"load_test_{uuid.uuid4()}"

        # Set
        with self.client.post(
            "/api/memory/set",
            json={"key": key, "value": {"test": "data"}},
            headers=self.headers,
            catch_response=True,
            name="/api/memory/set"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Set failed: {response.status_code}")

        # Get
        with self.client.post(
            "/api/memory/get",
            json={"key": key},
            headers=self.headers,
            catch_response=True,
            name="/api/memory/get"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Get failed: {response.status_code}")

    @task(2)  # Weight: 2
    def task_submission(self):
        """Agent task submission"""
        self.client.post(
            "/api/tasks/submit",
            json={
                "type": "load_test_task",
                "payload": {"data": "test"}
            },
            headers=self.headers,
            name="/api/tasks/submit"
        )

    @task(1)  # Weight: 1 (least common, slow)
    def llm_inference(self):
        """LLM inference (slow operation)"""
        with self.client.post(
            "/api/llm/generate",
            json={
                "prompt": "Say hi",
                "model": "llama3.2:latest",
                "max_tokens": 10
            },
            headers=self.headers,
            timeout=30,
            catch_response=True,
            name="/api/llm/generate"
        ) as response:
            if response.status_code not in [200, 500]:  # 500 OK if Ollama not running
                response.failure(f"LLM failed: {response.status_code}")

# Performance benchmarks
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test starting...")
    print("Target metrics:")
    print("  - Health check: < 10ms (p95)")
    print("  - Memory ops: < 50ms (p95)")
    print("  - Task submission: < 100ms (p95)")
    print("  - Error rate: < 1%")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\nLoad test complete!")
    print("Check results in Locust web UI")
```

### Load Test Targets

| Endpoint | p50 | p95 | p99 | RPS Target |
|----------|-----|-----|-----|------------|
| /health | 5ms | 10ms | 20ms | 1000 |
| /api/memory/* | 20ms | 50ms | 100ms | 100 |
| /api/tasks/* | 50ms | 100ms | 200ms | 50 |
| /api/llm/generate | 2s | 5s | 10s | 5 |

### Load Test Scenarios

1. **Baseline**: 10 users, 5 min
2. **Normal Load**: 50 users, 10 min
3. **Peak Load**: 100 users, 10 min
4. **Stress Test**: 200 users, 10 min
5. **Spike Test**: 0 → 100 → 0 users

---

## 5. Test Execution

### Running All Tests

```bash
# Full test suite
./scripts/run_all_tests.sh

# Or manually:
# 1. Unit tests
pytest tests/unit/ -v --cov=. --cov-report=html

# 2. Integration tests (requires services running)
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v --asyncio-mode=auto
docker-compose -f docker-compose.test.yml down

# 3. E2E tests
pytest tests/e2e/ -v --asyncio-mode=auto

# 4. Load tests
locust -f tests/load/locustfile.py --headless --users 10 --spawn-rate 1 --run-time 5m
```

### Test Automation Script

```bash
#!/bin/bash
# scripts/run_all_tests.sh

set -e

echo "===== Prime Spark AI Test Suite ====="

# 1. Unit Tests
echo "\n[1/4] Running unit tests..."
pytest tests/unit/ -v --cov=. --cov-report=term --cov-report=html || true

# 2. Integration Tests
echo "\n[2/4] Running integration tests..."
docker-compose -f docker-compose.test.yml up -d
sleep 10  # Wait for services
pytest tests/integration/ -v --asyncio-mode=auto || true
docker-compose -f docker-compose.test.yml down

# 3. E2E Tests
echo "\n[3/4] Running E2E tests..."
pytest tests/e2e/ -v --asyncio-mode=auto || true

# 4. Load Tests
echo "\n[4/4] Running load tests..."
locust -f tests/load/locustfile.py --headless \
  --users 10 --spawn-rate 2 --run-time 2m \
  --html reports/locust_report.html || true

echo "\n===== Test Suite Complete ====="
echo "Coverage report: htmlcov/index.html"
echo "Load test report: reports/locust_report.html"
```

---

## 6. Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

      postgres:
        image: timescale/timescaledb:latest-pg15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=. --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -v --asyncio-mode=auto

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 7. Test Data Management

### Fixtures

```python
# tests/fixtures/mock_data.py

import pytest
from datetime import datetime

@pytest.fixture
def sample_telemetry():
    """Sample telemetry data"""
    return {
        'device_id': 'test-device-1',
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'cpu_usage': 45.2,
            'memory_usage': 60.5,
            'disk_usage': 70.1
        }
    }

@pytest.fixture
def sample_inference_result():
    """Sample AI inference result"""
    return {
        'model': 'object-detection-v1',
        'inference_time_ms': 125.5,
        'result': {
            'objects': [
                {'class': 'person', 'confidence': 0.95},
                {'class': 'car', 'confidence': 0.87}
            ]
        }
    }

@pytest.fixture
async def test_database():
    """Test database connection"""
    from analytics.timeseries_db import TimescaleDBManager

    db = TimescaleDBManager(
        host="localhost",
        port=5433,
        database="test_db",
        user="test_user",
        password="test_pass"
    )

    await db.connect()
    await db.initialize_schema()

    yield db

    await db.disconnect()
```

---

## 8. Test Reporting

### Coverage Reports
- HTML: `htmlcov/index.html`
- XML: `coverage.xml` (for CI tools)
- Terminal: Real-time during test runs

### Load Test Reports
- Locust HTML: `reports/locust_report.html`
- CSV exports: `reports/locust_stats.csv`

### Test Metrics Dashboard
Create Grafana dashboard to track:
- Test pass rate over time
- Code coverage trends
- Load test results
- CI/CD pipeline duration

---

## Success Criteria

### Unit Tests
- [ ] >85% code coverage
- [ ] All critical paths tested
- [ ] Edge cases covered
- [ ] Fast execution (< 1 min)

### Integration Tests
- [ ] All API endpoints tested
- [ ] All service integrations verified
- [ ] Error handling validated
- [ ] Execution time < 5 min

### E2E Tests
- [ ] Critical user flows work
- [ ] Failover scenarios validated
- [ ] Data pipeline verified
- [ ] Execution time < 15 min

### Load Tests
- [ ] Meet performance targets
- [ ] System stable under load
- [ ] No memory leaks
- [ ] Graceful degradation

---

**Testing Strategy Version**: 1.0
**Last Updated**: 2025-01-15
**Owner**: Prime Spark AI Team
