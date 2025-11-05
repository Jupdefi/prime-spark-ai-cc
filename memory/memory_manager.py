"""
Unified Memory Manager
Orchestrates three-tier memory architecture:
- Tier 1: Local Cache (Redis) - Hot data, fast access
- Tier 2: NAS Storage - Persistent shared edge storage
- Tier 3: Cloud Storage (MinIO) - Long-term cloud storage
"""
from typing import Any, Optional, Literal
from enum import Enum
from memory.cache.redis_cache import cache
from memory.nas.nas_storage import nas_storage
from memory.cloud.cloud_storage import cloud_storage


class MemoryTier(Enum):
    """Memory tier levels"""
    LOCAL = 1
    NAS = 2
    CLOUD = 3


class MemoryManager:
    """
    Three-tier memory manager with automatic tiering.

    Strategy:
    - GET: Check Tier 1 -> Tier 2 -> Tier 3, backfill upper tiers on hit
    - SET: Write to Tier 1, async persist to Tier 2
    - PERSIST: Explicitly write to Tier 3 for long-term storage
    """

    def __init__(self):
        self.cache = cache  # Tier 1
        self.nas = nas_storage  # Tier 2
        self.cloud = cloud_storage  # Tier 3

    async def get(
        self,
        key: str,
        max_tier: MemoryTier = MemoryTier.CLOUD
    ) -> Optional[Any]:
        """
        Get value from memory tiers.
        Checks tiers in order and backfills upper tiers on cache miss.
        """
        # Try Tier 1: Local Cache
        value = await self.cache.get(key)
        if value is not None:
            return value

        if max_tier.value < MemoryTier.NAS.value:
            return None

        # Try Tier 2: NAS Storage
        value = await self.nas.get(key)
        if value is not None:
            # Backfill Tier 1
            await self.cache.set(key, value)
            return value

        if max_tier.value < MemoryTier.CLOUD.value:
            return None

        # Try Tier 3: Cloud Storage
        value = await self.cloud.get(key)
        if value is not None:
            # Backfill Tier 1 and 2
            await self.cache.set(key, value)
            await self.nas.set(key, value)
            return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        persist_to_nas: bool = True,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in memory.
        Always writes to Tier 1, optionally persists to Tier 2.
        """
        # Write to Tier 1: Local Cache
        cache_success = await self.cache.set(key, value, ttl)

        # Optionally persist to Tier 2: NAS
        if persist_to_nas:
            await self.nas.set(key, value)

        return cache_success

    async def persist_to_cloud(self, key: str, value: Any) -> bool:
        """
        Explicitly persist to cloud storage (Tier 3).
        Use this for long-term storage or data that needs cloud backup.
        """
        return await self.cloud.set(key, value)

    async def delete(
        self,
        key: str,
        all_tiers: bool = True
    ) -> bool:
        """
        Delete from memory tiers.
        By default deletes from all tiers.
        """
        success = True

        # Delete from Tier 1
        if not await self.cache.delete(key):
            success = False

        if all_tiers:
            # Delete from Tier 2
            if not await self.nas.delete(key):
                success = False

            # Delete from Tier 3
            if not await self.cloud.delete(key):
                success = False

        return success

    async def exists(
        self,
        key: str,
        tier: Optional[MemoryTier] = None
    ) -> bool:
        """
        Check if key exists.
        If tier is specified, only check that tier.
        Otherwise, check all tiers in order.
        """
        if tier == MemoryTier.LOCAL:
            return await self.cache.exists(key)
        elif tier == MemoryTier.NAS:
            return await self.nas.exists(key)
        elif tier == MemoryTier.CLOUD:
            return await self.cloud.exists(key)
        else:
            # Check all tiers
            if await self.cache.exists(key):
                return True
            if await self.nas.exists(key):
                return True
            if await self.cloud.exists(key):
                return True
            return False

    async def get_stats(self) -> dict:
        """Get statistics from all memory tiers"""
        cache_stats = await self.cache.get_stats()
        nas_stats = await self.nas.get_stats()
        cloud_stats = await self.cloud.get_stats()

        return {
            "tier1_local_cache": cache_stats,
            "tier2_nas_storage": nas_stats,
            "tier3_cloud_storage": cloud_stats,
        }

    async def migrate_to_cloud(self, key: str) -> bool:
        """
        Migrate data from edge (NAS) to cloud for long-term storage.
        Useful for archiving or when edge storage is getting full.
        """
        # Get from NAS
        value = await self.nas.get(key)
        if value is None:
            return False

        # Persist to cloud
        success = await self.cloud.set(key, value)

        # Optionally remove from NAS after successful migration
        # (commented out for safety - enable if you want true migration)
        # if success:
        #     await self.nas.delete(key)

        return success

    async def prefetch_from_cloud(self, key: str) -> bool:
        """
        Prefetch data from cloud to edge tiers.
        Useful for anticipated access or power-aware operations.
        """
        # Get from cloud
        value = await self.cloud.get(key)
        if value is None:
            return False

        # Backfill to NAS and cache
        await self.nas.set(key, value)
        await self.cache.set(key, value)

        return True

    async def cache_model(
        self,
        model_name: str,
        model_data: bytes,
        tier: MemoryTier = MemoryTier.NAS
    ) -> bool:
        """
        Cache AI model in specified tier.
        Models are typically stored in NAS for fast edge access.
        """
        if tier == MemoryTier.NAS or tier == MemoryTier.CLOUD:
            return await self.nas.save_model(model_name, model_data)

        return False

    async def load_model(self, model_name: str) -> Optional[bytes]:
        """
        Load AI model from storage.
        Checks NAS first, falls back to cloud.
        """
        # Try NAS first
        model_data = await self.nas.load_model(model_name)
        if model_data:
            return model_data

        # TODO: Add cloud model loading if needed
        return None


# Global memory manager instance
memory = MemoryManager()
