"""
Tier 1: Local Cache using Redis
Fast in-memory storage for hot data
"""
import json
from typing import Any, Optional
import redis.asyncio as redis
from config.settings import settings


class RedisCache:
    """Redis-based local cache (Tier 1)"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.host = "localhost"
        self.port = settings.memory.redis_local_port
        self.password = settings.memory.redis_password
        self.default_ttl = 3600  # 1 hour default

    async def connect(self):
        """Connect to Redis"""
        if not self.redis:
            self.redis = await redis.from_url(
                f"redis://:{self.password}@{self.host}:{self.port}",
                encoding="utf-8",
                decode_responses=True
            )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self.connect()
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        await self.connect()
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        await self.connect()
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        await self.connect()
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        await self.connect()
        try:
            info = await self.redis.info("stats")
            memory = await self.redis.info("memory")
            return {
                "total_keys": await self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used_mb": round(memory.get("used_memory", 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(memory.get("used_memory_peak", 0) / 1024 / 1024, 2),
            }
        except Exception as e:
            print(f"Redis stats error: {e}")
            return {}

    async def flush(self) -> bool:
        """Flush all cache data (use with caution)"""
        await self.connect()
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Redis flush error: {e}")
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values at once"""
        await self.connect()
        try:
            values = await self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            print(f"Redis get_many error: {e}")
            return {}

    async def set_many(self, items: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values at once"""
        await self.connect()
        try:
            ttl = ttl or self.default_ttl
            pipe = self.redis.pipeline()
            for key, value in items.items():
                serialized = json.dumps(value)
                pipe.setex(key, ttl, serialized)
            await pipe.execute()
            return True
        except Exception as e:
            print(f"Redis set_many error: {e}")
            return False


# Global cache instance
cache = RedisCache()
