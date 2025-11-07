"""
Edge Cache Manager
Multi-tier caching system for edge devices with intelligent eviction policies
"""

import asyncio
import logging
import json
import hashlib
import pickle
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import aioredis
from collections import OrderedDict
import os

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels"""
    MEMORY = "memory"  # Redis - fastest, limited capacity
    DISK = "disk"      # Local SSD/disk - medium speed, medium capacity
    NAS = "nas"        # Network storage - slower, large capacity


class EvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"   # Least Recently Used
    LFU = "lfu"   # Least Frequently Used
    TTL = "ttl"   # Time To Live
    FIFO = "fifo" # First In First Out


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    tier: CacheTier
    size_bytes: int
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl_seconds is None:
            return False
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def age_seconds(self) -> float:
        """Get entry age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


@dataclass
class CacheConfig:
    """Cache configuration"""
    # Redis (Memory tier)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_max_memory: int = 2 * 1024 * 1024 * 1024  # 2GB

    # Disk tier
    disk_cache_path: str = "/tmp/prime_spark_cache"
    disk_max_size: int = 50 * 1024 * 1024 * 1024  # 50GB

    # NAS tier
    nas_enabled: bool = False
    nas_mount_path: str = "/mnt/nas/cache"
    nas_max_size: int = 500 * 1024 * 1024 * 1024  # 500GB

    # Eviction policies
    memory_policy: EvictionPolicy = EvictionPolicy.LRU
    disk_policy: EvictionPolicy = EvictionPolicy.LFU
    nas_policy: EvictionPolicy = EvictionPolicy.TTL

    # TTL defaults
    default_ttl: Optional[int] = None
    inference_ttl: int = 3600  # 1 hour for inference results
    preprocessing_ttl: int = 1800  # 30 minutes for preprocessed data


class MemoryCacheManager:
    """Redis-based memory cache (Tier 1)"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        self.metadata: Dict[str, CacheEntry] = {}

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.create_redis_pool(
                f'redis://{self.config.redis_host}:{self.config.redis_port}',
                db=self.config.redis_db,
                encoding='utf-8'
            )
            logger.info("Redis memory cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if not self.redis:
            return None

        try:
            data = await self.redis.get(key)
            if data:
                # Update metadata
                if key in self.metadata:
                    self.metadata[key].accessed_at = datetime.now()
                    self.metadata[key].access_count += 1

                # Deserialize
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get failed for {key}: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        if not self.redis:
            return False

        try:
            # Serialize
            data = pickle.dumps(value)
            size = len(data)

            # Store in Redis
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)

            # Update metadata
            self.metadata[key] = CacheEntry(
                key=key,
                tier=CacheTier.MEMORY,
                size_bytes=size,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                ttl_seconds=ttl
            )

            return True
        except Exception as e:
            logger.error(f"Redis set failed for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from memory cache"""
        if not self.redis:
            return False

        try:
            await self.redis.delete(key)
            if key in self.metadata:
                del self.metadata[key]
            return True
        except Exception as e:
            logger.error(f"Redis delete failed for {key}: {e}")
            return False

    async def clear(self):
        """Clear all entries"""
        if self.redis:
            await self.redis.flushdb()
            self.metadata.clear()

    def get_size(self) -> int:
        """Get total cache size"""
        return sum(entry.size_bytes for entry in self.metadata.values())

    async def evict_lru(self, target_size: int):
        """Evict least recently used entries"""
        if not self.redis:
            return

        # Sort by access time
        sorted_entries = sorted(
            self.metadata.values(),
            key=lambda x: x.accessed_at
        )

        current_size = self.get_size()
        for entry in sorted_entries:
            if current_size <= target_size:
                break
            await self.delete(entry.key)
            current_size -= entry.size_bytes


class DiskCacheManager:
    """Local disk cache (Tier 2)"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_path = Path(config.disk_cache_path)
        self.metadata: Dict[str, CacheEntry] = {}
        self.lfu_counts: Dict[str, int] = {}

    async def initialize(self):
        """Initialize disk cache directory"""
        try:
            self.cache_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Disk cache initialized at {self.cache_path}")

            # Load existing metadata
            await self._load_metadata()
        except Exception as e:
            logger.error(f"Failed to initialize disk cache: {e}")

    def _get_file_path(self, key: str) -> Path:
        """Get file path for key"""
        # Hash key to avoid filesystem issues
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_path / f"{key_hash}.cache"

    def _get_metadata_path(self) -> Path:
        """Get metadata file path"""
        return self.cache_path / "metadata.json"

    async def _load_metadata(self):
        """Load metadata from disk"""
        metadata_path = self._get_metadata_path()
        if metadata_path.exists():
            try:
                async with aiofiles.open(metadata_path, 'r') as f:
                    data = await f.read()
                    metadata_dict = json.loads(data)

                    # Reconstruct CacheEntry objects
                    for key, entry_dict in metadata_dict.items():
                        self.metadata[key] = CacheEntry(
                            key=entry_dict['key'],
                            tier=CacheTier(entry_dict['tier']),
                            size_bytes=entry_dict['size_bytes'],
                            created_at=datetime.fromisoformat(entry_dict['created_at']),
                            accessed_at=datetime.fromisoformat(entry_dict['accessed_at']),
                            access_count=entry_dict.get('access_count', 0),
                            ttl_seconds=entry_dict.get('ttl_seconds'),
                            metadata=entry_dict.get('metadata', {})
                        )
                        self.lfu_counts[key] = entry_dict.get('access_count', 0)
            except Exception as e:
                logger.warning(f"Could not load disk cache metadata: {e}")

    async def _save_metadata(self):
        """Save metadata to disk"""
        try:
            metadata_dict = {
                key: {
                    'key': entry.key,
                    'tier': entry.tier.value,
                    'size_bytes': entry.size_bytes,
                    'created_at': entry.created_at.isoformat(),
                    'accessed_at': entry.accessed_at.isoformat(),
                    'access_count': entry.access_count,
                    'ttl_seconds': entry.ttl_seconds,
                    'metadata': entry.metadata
                }
                for key, entry in self.metadata.items()
            }

            async with aiofiles.open(self._get_metadata_path(), 'w') as f:
                await f.write(json.dumps(metadata_dict, indent=2))
        except Exception as e:
            logger.error(f"Failed to save disk cache metadata: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        # Check if expired
        if key in self.metadata and self.metadata[key].is_expired():
            await self.delete(key)
            return None

        try:
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
                value = pickle.loads(data)

            # Update metadata
            if key in self.metadata:
                self.metadata[key].accessed_at = datetime.now()
                self.metadata[key].access_count += 1
                self.lfu_counts[key] = self.metadata[key].access_count
                await self._save_metadata()

            return value
        except Exception as e:
            logger.error(f"Disk cache get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in disk cache"""
        try:
            # Serialize
            data = pickle.dumps(value)
            size = len(data)

            # Write to disk
            file_path = self._get_file_path(key)
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(data)

            # Update metadata
            self.metadata[key] = CacheEntry(
                key=key,
                tier=CacheTier.DISK,
                size_bytes=size,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                ttl_seconds=ttl
            )
            self.lfu_counts[key] = 1

            await self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"Disk cache set failed for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from disk cache"""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()

            if key in self.metadata:
                del self.metadata[key]
            if key in self.lfu_counts:
                del self.lfu_counts[key]

            await self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"Disk cache delete failed for {key}: {e}")
            return False

    def get_size(self) -> int:
        """Get total cache size"""
        return sum(entry.size_bytes for entry in self.metadata.values())

    async def evict_lfu(self, target_size: int):
        """Evict least frequently used entries"""
        # Sort by frequency
        sorted_keys = sorted(self.lfu_counts.keys(), key=lambda k: self.lfu_counts[k])

        current_size = self.get_size()
        for key in sorted_keys:
            if current_size <= target_size:
                break
            if key in self.metadata:
                current_size -= self.metadata[key].size_bytes
                await self.delete(key)


class EdgeCacheManager:
    """Main edge cache manager coordinating all tiers"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.memory_cache = MemoryCacheManager(self.config)
        self.disk_cache = DiskCacheManager(self.config)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0,
            "evictions": 0,
            "total_size": 0
        }

    async def initialize(self):
        """Initialize all cache tiers"""
        await self.memory_cache.initialize()
        await self.disk_cache.initialize()
        logger.info("Edge cache manager initialized")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks all tiers)"""
        # Try memory first (fastest)
        value = await self.memory_cache.get(key)
        if value is not None:
            self.stats["hits"] += 1
            self.stats["memory_hits"] += 1
            return value

        # Try disk
        value = await self.disk_cache.get(key)
        if value is not None:
            self.stats["hits"] += 1
            self.stats["disk_hits"] += 1

            # Promote to memory cache (cache warming)
            await self.memory_cache.set(key, value)
            return value

        # Cache miss
        self.stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any,
                  tier: CacheTier = CacheTier.MEMORY,
                  ttl: Optional[int] = None) -> bool:
        """Set value in specified tier"""
        if tier == CacheTier.MEMORY:
            success = await self.memory_cache.set(key, value, ttl)
        elif tier == CacheTier.DISK:
            success = await self.disk_cache.set(key, value, ttl)
        else:
            # NAS not yet implemented
            logger.warning(f"Tier {tier} not implemented")
            success = False

        # Check if eviction needed
        await self._check_eviction()

        return success

    async def delete(self, key: str) -> bool:
        """Delete from all tiers"""
        memory_deleted = await self.memory_cache.delete(key)
        disk_deleted = await self.disk_cache.delete(key)
        return memory_deleted or disk_deleted

    async def clear(self, tier: Optional[CacheTier] = None):
        """Clear cache (all tiers or specific tier)"""
        if tier is None or tier == CacheTier.MEMORY:
            await self.memory_cache.clear()
        if tier is None or tier == CacheTier.DISK:
            for key in list(self.disk_cache.metadata.keys()):
                await self.disk_cache.delete(key)

    async def _check_eviction(self):
        """Check if eviction is needed and perform it"""
        # Memory tier eviction
        memory_size = self.memory_cache.get_size()
        if memory_size > self.config.redis_max_memory * 0.9:  # 90% threshold
            target_size = int(self.config.redis_max_memory * 0.7)  # Evict to 70%
            await self.memory_cache.evict_lru(target_size)
            self.stats["evictions"] += 1

        # Disk tier eviction
        disk_size = self.disk_cache.get_size()
        if disk_size > self.config.disk_max_size * 0.9:
            target_size = int(self.config.disk_max_size * 0.7)
            await self.disk_cache.evict_lfu(target_size)
            self.stats["evictions"] += 1

    async def warm_cache(self, keys: List[str], source_tier: CacheTier,
                        target_tier: CacheTier):
        """Warm cache by moving frequently accessed items to faster tier"""
        for key in keys:
            if source_tier == CacheTier.DISK and target_tier == CacheTier.MEMORY:
                value = await self.disk_cache.get(key)
                if value is not None:
                    await self.memory_cache.set(key, value)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = (
            self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
            if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
        )

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "memory_size": self.memory_cache.get_size(),
            "disk_size": self.disk_cache.get_size(),
            "memory_entries": len(self.memory_cache.metadata),
            "disk_entries": len(self.disk_cache.metadata),
        }

    async def cleanup_expired(self):
        """Remove expired entries from all tiers"""
        expired_count = 0

        # Check disk cache (memory cache TTL handled by Redis)
        for key, entry in list(self.disk_cache.metadata.items()):
            if entry.is_expired():
                await self.disk_cache.delete(key)
                expired_count += 1

        logger.info(f"Cleaned up {expired_count} expired cache entries")


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> EdgeCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = EdgeCacheManager()
    return _cache_manager
