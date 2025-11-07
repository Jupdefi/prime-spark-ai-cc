"""
Prime Spark AI - KVA (Key-Value Architecture) Cache Example

Demonstrates advanced caching strategies for high-performance edge-cloud systems:
- Multi-tier caching (Redis + Local)
- Cache warming and invalidation
- Cache hit rate optimization
- Distributed cache synchronization
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List


class KVACacheManager:
    """
    Advanced Key-Value Architecture Cache Manager

    Features:
    - Multi-tier caching (L1: local memory, L2: Redis)
    - Intelligent cache warming
    - TTL-based expiration
    - Cache statistics tracking
    - LRU eviction policy
    """

    def __init__(self, max_local_size: int = 1000):
        self.local_cache: Dict[str, Dict[str, Any]] = {}  # L1 cache
        self.max_local_size = max_local_size
        self.access_times: Dict[str, datetime] = {}

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        print("✓ KVA Cache Manager initialized")
        print(f"  Max local cache size: {max_local_size}")

    async def get(self, key: str) -> Any:
        """Get value from cache with L1 -> L2 lookup"""
        # L1 cache lookup
        if key in self.local_cache:
            entry = self.local_cache[key]

            # Check TTL
            if entry['expires_at'] and datetime.now() > entry['expires_at']:
                # Expired
                del self.local_cache[key]
                self.misses += 1
                return None

            # Cache hit
            self.hits += 1
            self.access_times[key] = datetime.now()
            return entry['value']

        # L2 cache lookup (simulated Redis)
        # In production, this would query Redis
        self.misses += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300
    ) -> bool:
        """Set value in cache with TTL"""
        # Check if we need to evict
        if len(self.local_cache) >= self.max_local_size:
            self._evict_lru()

        # Store in cache
        self.local_cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds else None,
        }
        self.access_times[key] = datetime.now()

        return True

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return

        # Find LRU key
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]

        # Remove
        del self.local_cache[lru_key]
        del self.access_times[lru_key]
        self.evictions += 1

    async def invalidate(self, key: str) -> bool:
        """Invalidate cache entry"""
        if key in self.local_cache:
            del self.local_cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False

    async def warm_cache(self, keys: List[str], data_loader: callable):
        """Warm cache with frequently accessed data"""
        print(f"\n→ Warming cache with {len(keys)} entries...")

        for key in keys:
            value = await data_loader(key)
            await self.set(key, value, ttl_seconds=600)

        print(f"  ✓ Cache warmed with {len(keys)} entries")

    def get_statistics(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_size': len(self.local_cache),
            'max_size': self.max_local_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions,
        }


async def demo_basic_caching():
    """Demo 1: Basic caching operations"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Caching Operations")
    print("=" * 80)

    cache = KVACacheManager(max_local_size=100)

    # Store data
    print("\n1. Storing data in cache:")
    await cache.set("user:1001", {"name": "Alice", "role": "admin"}, ttl_seconds=300)
    await cache.set("user:1002", {"name": "Bob", "role": "user"}, ttl_seconds=300)
    await cache.set("user:1003", {"name": "Charlie", "role": "user"}, ttl_seconds=300)
    print("   ✓ Stored 3 user records")

    # Retrieve data
    print("\n2. Retrieving data from cache:")
    user = await cache.get("user:1001")
    print(f"   user:1001 → {user}")

    user = await cache.get("user:1002")
    print(f"   user:1002 → {user}")

    # Cache miss
    print("\n3. Cache miss (key doesn't exist):")
    user = await cache.get("user:9999")
    print(f"   user:9999 → {user}")

    # Statistics
    print("\n4. Cache statistics:")
    stats = cache.get_statistics()
    print(f"   Cache size: {stats['cache_size']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")


async def demo_cache_warming():
    """Demo 2: Cache warming for frequently accessed data"""
    print("\n" + "=" * 80)
    print("DEMO 2: Cache Warming")
    print("=" * 80)

    cache = KVACacheManager(max_local_size=1000)

    # Simulate data loader (database query)
    async def load_product(product_id: str) -> Dict:
        """Simulate loading product from database"""
        await asyncio.sleep(0.01)  # Simulate DB latency
        return {
            'id': product_id,
            'name': f'Product {product_id}',
            'price': random.uniform(10, 100),
            'stock': random.randint(0, 1000),
        }

    # Warm cache with top 100 products
    print("\n1. Warming cache with top 100 products:")
    top_products = [f"product:{i}" for i in range(1, 101)]

    start_time = time.time()
    await cache.warm_cache(top_products, load_product)
    warm_time = time.time() - start_time

    print(f"   Warming time: {warm_time:.2f}s")

    # Benchmark cache hits vs misses
    print("\n2. Benchmark: Cached vs Uncached access:")

    # Cached access (should be fast)
    start_time = time.time()
    for i in range(1, 51):
        await cache.get(f"product:{i}")
    cached_time = time.time() - start_time

    print(f"   50 cached lookups: {cached_time * 1000:.2f}ms")

    # Uncached access (slower due to DB queries)
    start_time = time.time()
    for i in range(101, 151):
        result = await cache.get(f"product:{i}")
        if result is None:
            # Load from "database"
            data = await load_product(f"product:{i}")
            await cache.set(f"product:{i}", data)
    uncached_time = time.time() - start_time

    print(f"   50 uncached lookups: {uncached_time * 1000:.2f}ms")
    print(f"   Speedup: {uncached_time / cached_time:.1f}x")

    # Statistics
    stats = cache.get_statistics()
    print(f"\n3. Final statistics:")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")


async def demo_lru_eviction():
    """Demo 3: LRU eviction policy"""
    print("\n" + "=" * 80)
    print("DEMO 3: LRU Eviction Policy")
    print("=" * 80)

    # Small cache to demonstrate eviction
    cache = KVACacheManager(max_local_size=5)

    print("\n1. Filling cache to capacity (5 entries):")
    for i in range(1, 6):
        await cache.set(f"key:{i}", f"value-{i}")
        print(f"   Stored key:{i}")

    stats = cache.get_statistics()
    print(f"   Cache size: {stats['cache_size']}/{stats['max_size']}")

    print("\n2. Accessing keys 2, 3, 4 (updating LRU order):")
    await cache.get("key:2")
    await cache.get("key:3")
    await cache.get("key:4")
    print("   ✓ Keys 2, 3, 4 accessed")

    print("\n3. Adding new entry (should evict LRU key:1):")
    await cache.set("key:6", "value-6")
    print("   ✓ Added key:6")

    print("\n4. Verifying eviction:")
    result = await cache.get("key:1")
    print(f"   key:1 → {result} (evicted)")

    result = await cache.get("key:2")
    print(f"   key:2 → {result} (still cached)")

    stats = cache.get_statistics()
    print(f"\n5. Statistics:")
    print(f"   Evictions: {stats['evictions']}")
    print(f"   Cache size: {stats['cache_size']}/{stats['max_size']}")


async def demo_ttl_expiration():
    """Demo 4: TTL-based cache expiration"""
    print("\n" + "=" * 80)
    print("DEMO 4: TTL-Based Expiration")
    print("=" * 80)

    cache = KVACacheManager()

    print("\n1. Storing data with different TTL values:")
    await cache.set("session:1", {"user_id": 1001}, ttl_seconds=2)
    print("   ✓ session:1 with TTL=2s")

    await cache.set("session:2", {"user_id": 1002}, ttl_seconds=5)
    print("   ✓ session:2 with TTL=5s")

    await cache.set("config:app", {"version": "1.0"}, ttl_seconds=None)  # No expiration
    print("   ✓ config:app with no expiration")

    print("\n2. Immediate access (all should be cached):")
    s1 = await cache.get("session:1")
    s2 = await cache.get("session:2")
    cfg = await cache.get("config:app")
    print(f"   session:1 → {s1}")
    print(f"   session:2 → {s2}")
    print(f"   config:app → {cfg}")

    print("\n3. Waiting 3 seconds...")
    await asyncio.sleep(3)

    print("\n4. Access after 3s (session:1 should be expired):")
    s1 = await cache.get("session:1")
    s2 = await cache.get("session:2")
    cfg = await cache.get("config:app")
    print(f"   session:1 → {s1} (expired)")
    print(f"   session:2 → {s2} (still valid)")
    print(f"   config:app → {cfg} (no expiration)")


async def demo_distributed_sync():
    """Demo 5: Distributed cache synchronization simulation"""
    print("\n" + "=" * 80)
    print("DEMO 5: Distributed Cache Synchronization")
    print("=" * 80)

    # Simulate edge and cloud caches
    edge_cache = KVACacheManager(max_local_size=50)
    cloud_cache = KVACacheManager(max_local_size=10000)

    print("\n1. Simulating edge and cloud caches:")
    print("   ✓ Edge cache (50 max)")
    print("   ✓ Cloud cache (10000 max)")

    # Cloud has authoritative data
    print("\n2. Loading data to cloud cache:")
    for i in range(1, 101):
        await cloud_cache.set(
            f"model:v{i}",
            {"version": i, "accuracy": 0.9 + random.random() * 0.05},
            ttl_seconds=3600
        )
    print(f"   ✓ Loaded 100 models to cloud")

    # Edge syncs subset
    print("\n3. Syncing top 20 models to edge:")
    for i in range(1, 21):
        model = await cloud_cache.get(f"model:v{i}")
        if model:
            await edge_cache.set(f"model:v{i}", model)
    print(f"   ✓ Synced 20 models to edge")

    # Edge operations
    print("\n4. Edge cache operations:")
    edge_stats = edge_cache.get_statistics()
    cloud_stats = cloud_cache.get_statistics()

    print(f"   Edge cache size: {edge_stats['cache_size']}")
    print(f"   Cloud cache size: {cloud_stats['cache_size']}")

    # Simulate edge update propagation
    print("\n5. Edge updates model (sync back to cloud):")
    await edge_cache.set("model:v1", {"version": 1, "accuracy": 0.96})

    # Propagate to cloud
    updated_model = await edge_cache.get("model:v1")
    await cloud_cache.set("model:v1", updated_model)
    print("   ✓ Update propagated to cloud")

    # Verify
    cloud_model = await cloud_cache.get("model:v1")
    print(f"   Cloud model:v1 accuracy: {cloud_model['accuracy']:.2f}")


async def main():
    """Run all KVA cache demos"""
    print("=" * 80)
    print("PRIME SPARK AI - KVA CACHE ARCHITECTURE DEMO")
    print("=" * 80)
    print("\nDemonstrates advanced caching strategies:")
    print("  1. Basic Caching Operations")
    print("  2. Cache Warming")
    print("  3. LRU Eviction Policy")
    print("  4. TTL-Based Expiration")
    print("  5. Distributed Cache Synchronization")

    input("\nPress Enter to start demos...")

    await demo_basic_caching()
    input("\nPress Enter to continue...")

    await demo_cache_warming()
    input("\nPress Enter to continue...")

    await demo_lru_eviction()
    input("\nPress Enter to continue...")

    await demo_ttl_expiration()
    input("\nPress Enter to continue...")

    await demo_distributed_sync()

    print("\n" + "=" * 80)
    print("KVA CACHE DEMOS COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Multi-tier caching reduces latency by 10-100x")
    print("  • Cache warming improves hit rates for frequent queries")
    print("  • LRU eviction ensures optimal memory usage")
    print("  • TTL expiration maintains data freshness")
    print("  • Edge-cloud sync enables offline operation")


if __name__ == "__main__":
    asyncio.run(main())
