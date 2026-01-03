"""
Advanced caching service for Credit Clarity
Provides multi-level caching with Redis support and in-memory fallback
"""
import asyncio
import json
import logging
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import weakref

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class InMemoryCache:
    """High-performance in-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, datetime] = {}
        self._expiry_times: Dict[str, datetime] = {}
        self._hits = 0
        self._misses = 0
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self._expiry_times.items()
            if expiry < now
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            self._expiry_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used entries if at capacity."""
        if len(self._cache) >= self.max_size:
            # Find least recently used key
            lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            
            # Remove LRU entry
            self._cache.pop(lru_key, None)
            self._access_times.pop(lru_key, None)
            self._expiry_times.pop(lru_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._cleanup_expired()
        
        if key in self._cache:
            self._access_times[key] = datetime.now()
            self._hits += 1
            return self._cache[key]
        
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        self._cleanup_expired()
        self._evict_lru()
        
        ttl = ttl or self.default_ttl
        now = datetime.now()
        
        self._cache[key] = value
        self._access_times[key] = now
        self._expiry_times[key] = now + timedelta(seconds=ttl)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            self._expiry_times.pop(key, None)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_times.clear()
        self._expiry_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'size': len(self._cache),
            'max_size': self.max_size
        }


class RedisCache:
    """Redis-based cache implementation."""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client = None
        self._available = False
        self._initialized = False
        self._init_task: Optional[asyncio.Task] = None
        
        # Try to initialize Redis
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop:
            self._init_task = loop.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize Redis connection."""
        try:
            # Only import redis if we're going to use it
            import redis.asyncio as redis
            
            if self.redis_url:
                self._client = redis.from_url(self.redis_url)
            else:
                self._client = redis.Redis()
            
            # Test connection
            await self._client.ping()
            self._available = True
            logger.info("✅ Redis cache initialized")
            
        except ImportError:
            logger.info("Redis not available - install with: pip install redis")
            self._available = False
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            self._available = False
        finally:
            self._initialized = True

    async def ensure_initialized(self) -> None:
        """Ensure Redis initialization has been attempted inside an event loop."""
        if self._initialized:
            return
        if self._init_task:
            await self._init_task
            return
        
        self._init_task = asyncio.create_task(self._initialize())
        await self._init_task
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        await self.ensure_initialized()
        if not self._available or not self._client:
            return None
        
        try:
            data = await self._client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.debug(f"Redis get failed for key {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        await self.ensure_initialized()
        if not self._available or not self._client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            data = pickle.dumps(value)
            await self._client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.debug(f"Redis set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        await self.ensure_initialized()
        if not self._available or not self._client:
            return False
        
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.debug(f"Redis delete failed for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all Redis cache entries."""
        await self.ensure_initialized()
        if not self._available or not self._client:
            return False
        
        try:
            await self._client.flushall()
            return True
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._available


class MultiLevelCache:
    """
    Multi-level cache with Redis (L1) and in-memory (L2) fallback.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        memory_max_size: int = 1000,
        default_ttl: int = 3600
    ):
        self.default_ttl = default_ttl
        
        # Initialize cache levels
        self.redis_cache = RedisCache(redis_url, default_ttl)
        self.memory_cache = InMemoryCache(memory_max_size, default_ttl)
        
        self._stats = {
            'redis_hits': 0,
            'memory_hits': 0,
            'misses': 0,
            'sets': 0
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        await self.redis_cache.ensure_initialized()
        # Try Redis first (L1)
        if self.redis_cache.is_available():
            value = await self.redis_cache.get(key)
            if value is not None:
                # Store in memory cache for faster access
                self.memory_cache.set(key, value)
                self._stats['redis_hits'] += 1
                return value
        
        # Try memory cache (L2)
        value = self.memory_cache.get(key)
        if value is not None:
            self._stats['memory_hits'] += 1
            return value
        
        self._stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in multi-level cache."""
        ttl = ttl or self.default_ttl
        await self.redis_cache.ensure_initialized()
        
        # Set in memory cache first (always works)
        self.memory_cache.set(key, value, ttl)
        
        # Try to set in Redis
        if self.redis_cache.is_available():
            await self.redis_cache.set(key, value, ttl)
        
        self._stats['sets'] += 1
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache levels."""
        redis_deleted = False
        memory_deleted = False
        
        await self.redis_cache.ensure_initialized()
        
        if self.redis_cache.is_available():
            redis_deleted = await self.redis_cache.delete(key)
        
        memory_deleted = self.memory_cache.delete(key)
        
        return redis_deleted or memory_deleted
    
    async def clear(self) -> None:
        """Clear all cache levels."""
        await self.redis_cache.ensure_initialized()
        if self.redis_cache.is_available():
            await self.redis_cache.clear()
        
        self.memory_cache.clear()
        
        # Reset stats
        for key in self._stats:
            self._stats[key] = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.stats()
        
        total_hits = self._stats['redis_hits'] + self._stats['memory_hits']
        total_requests = total_hits + self._stats['misses']
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'overall': {
                'hit_rate': f"{overall_hit_rate:.2f}%",
                'total_requests': total_requests,
                'redis_hits': self._stats['redis_hits'],
                'memory_hits': self._stats['memory_hits'],
                'misses': self._stats['misses'],
                'sets': self._stats['sets']
            },
            'redis': {
                'available': self.redis_cache.is_available()
            },
            'memory': memory_stats
        }


# Global cache instance
cache = MultiLevelCache()


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    exclude_args: Optional[List[str]] = None
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        exclude_args: Arguments to exclude from cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            filtered_kwargs = kwargs.copy()
            if exclude_args:
                for arg in exclude_args:
                    filtered_kwargs.pop(arg, None)
            
            cache_key = cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **filtered_kwargs
            )
            
            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we'll use a basic approach
            # In a real implementation, you might want to use threading
            cache_key = cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # Use memory cache only for sync functions
            result = cache.memory_cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.memory_cache.set(cache_key, result, ttl)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class CacheWarmer:
    """Service to pre-warm cache with frequently accessed data."""
    
    def __init__(self, cache_instance: MultiLevelCache):
        self.cache = cache_instance
        self.warming_tasks = []
    
    async def warm_user_data(self, user_id: str):
        """Pre-warm cache with user's frequently accessed data."""
        try:
            from services.database_optimizer import db_optimizer
            
            # Warm user tradelines
            user_tradelines = await db_optimizer.get_user_tradelines_optimized(
                user_id=user_id,
                limit=50
            )
            
            cache_key = f"user_tradelines_{user_id}"
            await self.cache.set(cache_key, user_tradelines, ttl=1800)  # 30 minutes
            
            logger.debug(f"Warmed cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"Cache warming failed for user {user_id}: {e}")
    
    async def warm_common_data(self):
        """Pre-warm cache with commonly accessed data."""
        try:
            # You can add common data warming here
            # For example: creditor names, account types, etc.
            pass
            
        except Exception as e:
            logger.error(f"Common data cache warming failed: {e}")
    
    def schedule_warming(self, interval: int = 3600):
        """Schedule periodic cache warming."""
        async def warming_task():
            while True:
                try:
                    await self.warm_common_data()
                    await asyncio.sleep(interval)
                except Exception as e:
                    logger.error(f"Scheduled cache warming failed: {e}")
                    await asyncio.sleep(60)  # Retry after 1 minute
        
        task = asyncio.create_task(warming_task())
        self.warming_tasks.append(task)
        return task


# Global cache warmer
cache_warmer = CacheWarmer(cache)


# Utility functions for common caching patterns
async def cache_user_tradelines(user_id: str, tradelines: List[Dict], ttl: int = 1800):
    """Cache user tradelines."""
    cache_key = f"user_tradelines_{user_id}"
    await cache.set(cache_key, tradelines, ttl)


async def get_cached_user_tradelines(user_id: str) -> Optional[List[Dict]]:
    """Get cached user tradelines."""
    cache_key = f"user_tradelines_{user_id}"
    return await cache.get(cache_key)


async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user."""
    patterns = [
        f"user_tradelines_{user_id}",
        f"user_profile_{user_id}",
        f"user_stats_{user_id}"
    ]
    
    for pattern in patterns:
        await cache.delete(pattern)


# Example usage and performance testing
async def cache_performance_test():
    """Test cache performance."""
    import time
    
    logger.info("Running cache performance test...")
    
    # Test data
    test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
    
    # Test writes
    start_time = time.time()
    for key, value in test_data.items():
        await cache.set(key, value)
    write_time = time.time() - start_time
    
    # Test reads (should hit cache)
    start_time = time.time()
    for key in test_data.keys():
        await cache.get(key)
    read_time = time.time() - start_time
    
    stats = cache.stats()
    
    logger.info(f"Cache performance test results:")
    logger.info(f"  Write time: {write_time:.3f}s ({len(test_data)/write_time:.0f} ops/s)")
    logger.info(f"  Read time: {read_time:.3f}s ({len(test_data)/read_time:.0f} ops/s)")
    logger.info(f"  Cache stats: {stats}")
    
    # Cleanup
    await cache.clear()


if __name__ == "__main__":
    # Run performance test
    asyncio.run(cache_performance_test())
