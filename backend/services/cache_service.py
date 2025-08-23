# backend/services/cache_service.py

import asyncio
import json
import logging
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import weakref
import os

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
    """Redis-based cache implementation with robust error handling."""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client = None
        self._available = False
        self._initialization_attempted = False
    
    async def _initialize(self):
        """Initialize Redis connection with robust error handling."""
        if self._initialization_attempted:
            return
            
        self._initialization_attempted = True
        
        try:
            # Try to import redis
            try:
                import redis.asyncio as redis
            except ImportError:
                logger.info("📦 Redis not installed - install with: pip install redis")
                self._available = False
                return
            
            # Set up Redis connection
            if self.redis_url:
                self._client = redis.from_url(
                    self.redis_url,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                logger.warning("⚠️ No REDIS_URL provided, using localhost")
                self._client = redis.Redis(
                    host='localhost',
                    port=6379,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
            
            # Test connection with timeout
            await asyncio.wait_for(self._client.ping(), timeout=5.0)
            self._available = True
            logger.info("✅ Redis cache initialized successfully")
            
        except asyncio.TimeoutError:
            logger.warning("⏰ Redis connection timeout - falling back to memory cache")
            self._available = False
        except Exception as e:
            logger.warning(f"🔴 Redis initialization failed: {e} - falling back to memory cache")
            self._available = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._available:
            await self._initialize()
            
        if not self._available or not self._client:
            return None
        
        try:
            data = await asyncio.wait_for(self._client.get(key), timeout=1.0)
            if data:
                return pickle.loads(data)
        except asyncio.TimeoutError:
            logger.debug(f"Redis get timeout for key {key}")
        except Exception as e:
            logger.debug(f"Redis get failed for key {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self._available:
            await self._initialize()
            
        if not self._available or not self._client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            data = pickle.dumps(value)
            await asyncio.wait_for(self._client.setex(key, ttl, data), timeout=1.0)
            return True
        except asyncio.TimeoutError:
            logger.debug(f"Redis set timeout for key {key}")
        except Exception as e:
            logger.debug(f"Redis set failed for key {key}: {e}")
            
        return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        if not self._available:
            await self._initialize()
            
        if not self._available or not self._client:
            return False
        
        try:
            result = await asyncio.wait_for(self._client.delete(key), timeout=1.0)
            return result > 0
        except Exception as e:
            logger.debug(f"Redis delete failed for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all Redis cache entries."""
        if not self._available:
            await self._initialize()
            
        if not self._available or not self._client:
            return False
        
        try:
            await asyncio.wait_for(self._client.flushall(), timeout=5.0)
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
    Automatically handles Redis unavailability gracefully.
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
        
        # Lazy initialization flag
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure cache is initialized."""
        if not self._initialized:
            await self.redis_cache._initialize()
            self._initialized = True
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        await self._ensure_initialized()
        
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
        await self._ensure_initialized()
        
        ttl = ttl or self.default_ttl
        
        # Set in memory cache first (always works)
        self.memory_cache.set(key, value, ttl)
        
        # Try to set in Redis
        if self.redis_cache.is_available():
            await self.redis_cache.set(key, value, ttl)
        
        self._stats['sets'] += 1
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache levels."""
        await self._ensure_initialized()
        
        redis_deleted = False
        memory_deleted = False
        
        if self.redis_cache.is_available():
            redis_deleted = await self.redis_cache.delete(key)
        
        memory_deleted = self.memory_cache.delete(key)
        
        return redis_deleted or memory_deleted
    
    async def clear(self) -> None:
        """Clear all cache levels."""
        await self._ensure_initialized()
        
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


# Global cache instance - lazy initialization
_cache_instance = None

def get_cache() -> MultiLevelCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        redis_url = os.getenv("REDIS_URL")
        _cache_instance = MultiLevelCache(redis_url=redis_url)
    return _cache_instance

# Convenience accessor
cache = get_cache()

# Application startup hook - call this in your FastAPI startup
async def initialize_cache():
    """Initialize cache during application startup."""
    try:
        await cache._ensure_initialized()
        logger.info("🚀 Cache service initialized")
    except Exception as e:
        logger.error(f"❌ Cache initialization failed: {e}")


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
            # For synchronous functions, use memory cache only
            filtered_kwargs = kwargs.copy()
            if exclude_args:
                for arg in exclude_args:
                    filtered_kwargs.pop(arg, None)
                    
            cache_key = cache._generate_key(
                key_prefix or func.__name__,
                *args,
                **filtered_kwargs
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


if __name__ == "__main__":
    # Run performance test
    async def cache_performance_test():
        """Test cache performance."""
        import time
        
        print("Running cache performance test...")
        
        # Initialize cache
        await initialize_cache()
        
        # Test data
        test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        
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
        
        print(f"Cache performance test results:")
        print(f"  Write time: {write_time:.3f}s ({len(test_data)/write_time:.0f} ops/s)")
        print(f"  Read time: {read_time:.3f}s ({len(test_data)/read_time:.0f} ops/s)")
        print(f"  Cache stats: {stats}")
        
        # Cleanup
        await cache.clear()
    
    asyncio.run(cache_performance_test())