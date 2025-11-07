"""
KVA API Gateway
RESTful, GraphQL, WebSocket with authentication and rate limiting
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import FastAPI, WebSocket, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt

from kva.storage_manager import get_storage_manager
from kva.analytics_engine import get_analytics_engine

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

# FastAPI app
app = FastAPI(
    title="Prime Spark KVA API",
    description="Comprehensive KVA System API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security
security = HTTPBearer()


# === Pydantic Models ===

class StoreRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None


class QueryRequest(BaseModel):
    metric_name: str
    start_time: datetime
    end_time: datetime
    aggregation: str = "avg"


class ForecastRequest(BaseModel):
    metric_name: str
    horizon_hours: int = 24


class MLTrainRequest(BaseModel):
    model_id: str
    model_type: str = "regression"
    training_data: Dict[str, List]


class UserCredentials(BaseModel):
    username: str
    password: str


# === Rate Limiter ===

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: int = 100, per: int = 60):
        self.rate = rate  # requests
        self.per = per    # seconds
        self.allowance = defaultdict(lambda: rate)
        self.last_check = defaultdict(lambda: datetime.now())

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        current = datetime.now()
        time_passed = (current - self.last_check[identifier]).total_seconds()
        self.last_check[identifier] = current

        self.allowance[identifier] += time_passed * (self.rate / self.per)
        if self.allowance[identifier] > self.rate:
            self.allowance[identifier] = self.rate

        if self.allowance[identifier] < 1.0:
            return False
        else:
            self.allowance[identifier] -= 1.0
            return True


rate_limiter = RateLimiter(rate=100, per=60)


# === Authentication ===

def create_jwt_token(user_id: str, role: str = "user") -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    return payload


async def check_rate_limit(user_id: str = Depends(get_current_user)):
    """Check rate limit"""
    if not rate_limiter.is_allowed(user_id["user_id"]):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return user_id


# === REST API Endpoints ===

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "Prime Spark KVA API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth/login",
            "storage": "/api/v1/store, /api/v1/retrieve",
            "analytics": "/api/v1/analytics/*",
            "ml": "/api/v1/ml/*",
            "websocket": "/ws"
        }
    }


@app.post("/auth/login")
async def login(credentials: UserCredentials):
    """Login and get JWT token"""
    # Simplified authentication (in production, check against database)
    if credentials.username == "admin" and credentials.password == "admin":
        token = create_jwt_token(credentials.username, role="admin")
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/v1/store")
async def store_data(
    request: StoreRequest,
    user: Dict = Depends(check_rate_limit)
):
    """Store data in KVA system"""
    storage = get_storage_manager()
    success = await storage.store(request.key, request.value, ttl=request.ttl)
    return {"success": success, "key": request.key}


@app.get("/api/v1/retrieve/{key}")
async def retrieve_data(
    key: str,
    user: Dict = Depends(check_rate_limit)
):
    """Retrieve data from KVA system"""
    storage = get_storage_manager()
    value = await storage.retrieve(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value}


@app.post("/api/v1/analytics/query")
async def run_analytics_query(
    request: QueryRequest,
    user: Dict = Depends(check_rate_limit)
):
    """Run analytics query"""
    analytics = get_analytics_engine()
    result = await analytics.batch_analytics.run_aggregation(
        request.metric_name,
        (request.start_time, request.end_time)
    )
    return result


@app.post("/api/v1/analytics/forecast")
async def forecast_metric(
    request: ForecastRequest,
    user: Dict = Depends(check_rate_limit)
):
    """Forecast metric values"""
    analytics = get_analytics_engine()
    result = await analytics.predictive.forecast_metric(
        request.metric_name,
        request.horizon_hours
    )
    return result


@app.get("/api/v1/analytics/anomalies/{metric_name}")
async def detect_anomalies(
    metric_name: str,
    user: Dict = Depends(check_rate_limit)
):
    """Detect anomalies in metric"""
    analytics = get_analytics_engine()
    anomalies = await analytics.predictive.detect_anomalies(metric_name)
    return {"metric": metric_name, "anomalies": anomalies}


@app.post("/api/v1/ml/train")
async def train_model(
    request: MLTrainRequest,
    user: Dict = Depends(check_rate_limit)
):
    """Train ML model"""
    analytics = get_analytics_engine()

    # Convert to DataFrame
    import pandas as pd
    df = pd.DataFrame(request.training_data)

    result = await analytics.ml_pipeline.train_model(
        request.model_id,
        df,
        request.model_type
    )
    return result


@app.post("/api/v1/ml/predict/{model_id}")
async def predict(
    model_id: str,
    input_data: Dict,
    user: Dict = Depends(check_rate_limit)
):
    """Run ML prediction"""
    analytics = get_analytics_engine()
    result = await analytics.ml_pipeline.predict(model_id, input_data)
    return result


@app.get("/api/v1/stats")
async def get_stats(user: Dict = Depends(check_rate_limit)):
    """Get system statistics"""
    storage = get_storage_manager()
    return storage.get_stats()


# === WebSocket Endpoint ===

class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages
            data = await websocket.receive_json()

            # Process based on message type
            if data.get("type") == "subscribe":
                # Subscribe to metric updates
                metric = data.get("metric")
                await websocket.send_json({
                    "type": "subscribed",
                    "metric": metric,
                    "timestamp": datetime.now().isoformat()
                })

            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# === GraphQL Support (Simplified) ===

@app.post("/graphql")
async def graphql_endpoint(
    query: str,
    user: Dict = Depends(check_rate_limit)
):
    """GraphQL endpoint (simplified)"""
    # In production, use graphene or strawberry

    # Parse simple queries
    if "metrics" in query:
        storage = get_storage_manager()
        stats = storage.get_stats()
        return {"data": {"metrics": stats}}

    return {"data": None, "errors": ["Query not supported"]}


# === Health Check ===

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# === Startup/Shutdown Events ===

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    storage = get_storage_manager()
    await storage.initialize()

    analytics = get_analytics_engine()
    await analytics.initialize()

    logger.info("KVA API Gateway started")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    storage = get_storage_manager()
    await storage.close()

    logger.info("KVA API Gateway shutdown")


# === Run Server ===

def run_api_gateway(host: str = "0.0.0.0", port: int = 8002):
    """Run API gateway"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api_gateway()
