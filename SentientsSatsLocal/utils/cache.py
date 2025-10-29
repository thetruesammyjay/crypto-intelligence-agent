"""
Caching System for Crypto Intelligence Agent

Provides both in-memory and disk-based caching with TTL support.
Uses cachetools for memory cache and diskcache for persistent storage.
"""

import functools
import hashlib
import inspect
import json
import os
from typing import Any, Callable, Optional
from cachetools import TTLCache
import diskcache
from utils.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    Manages both memory and disk caching for the agent.
    
    Features:
    - In-memory caching with TTL (fast, volatile)
    - Disk caching (persistent, slower)
    - Cache statistics (hits, misses)
    - Automatic cache key generation
    """
    
    def __init__(self, cache_type: str = "memory", cache_dir: str = "./data/cache", max_size: int = 1000):
        """
        Initialize the cache manager.
        
        Args:
            cache_type: "memory" or "disk"
            cache_dir: Directory for disk cache
            max_size: Maximum number of items in cache
        """
        self.cache_type = cache_type.lower()
        self.cache_dir = cache_dir
        self.max_size = max_size
        
        # Statistics
        self.hits = 0
        self.misses = 0
        
        # Initialize caches
        self._memory_caches = {}  # Different TTLs
        self._disk_cache = None
        
        if self.cache_type == "disk":
            self._init_disk_cache()
        
        logger.info(f"Cache manager initialized: type={cache_type}, max_size={max_size}")
    
    def _init_disk_cache(self):
        """Initialize disk cache"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
            self._disk_cache = diskcache.Cache(self.cache_dir)
            logger.info(f"Disk cache initialized at {self.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize disk cache: {e}")
            # Fallback to memory cache
            self.cache_type = "memory"
            logger.warning("Falling back to memory cache")
    
    def _get_memory_cache(self, ttl: int) -> TTLCache:
        """Get or create a memory cache with specific TTL"""
        if ttl not in self._memory_caches:
            self._memory_caches[ttl] = TTLCache(maxsize=self.max_size, ttl=ttl)
        return self._memory_caches[ttl]
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate a unique cache key from function name and arguments.
        
        Args:
            func_name: Name of the function
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            str: Unique cache key
        """
        # Create a string representation of the function call
        key_parts = [func_name]
        
        # Add args
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(type(arg).__name__))
        
        # Add kwargs
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}={v}")
            else:
                key_parts.append(f"{k}={type(v).__name__}")
        
        # Create hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{func_name}:{key_hash}"
    
    def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds (for memory cache)
            
        Returns:
            Cached value or None if not found
        """
        try:
            if self.cache_type == "memory":
                cache = self._get_memory_cache(ttl)
                value = cache.get(key)
            else:
                value = self._disk_cache.get(key)
            
            if value is not None:
                self.hits += 1
                logger.debug(f"Cache HIT: {key}")
                return value
            else:
                self.misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            if self.cache_type == "memory":
                cache = self._get_memory_cache(ttl)
                cache[key] = value
            else:
                self._disk_cache.set(key, value, expire=ttl)
            
            logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            if self.cache_type == "memory":
                for cache in self._memory_caches.values():
                    if key in cache:
                        del cache[key]
            else:
                self._disk_cache.delete(key)
            
            logger.debug(f"Cache DELETE: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all caches"""
        try:
            if self.cache_type == "memory":
                for cache in self._memory_caches.values():
                    cache.clear()
            else:
                self._disk_cache.clear()
            
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.2f}%",
            "cache_type": self.cache_type,
        }
        
        if self.cache_type == "memory":
            total_items = sum(len(cache) for cache in self._memory_caches.values())
            stats["total_items"] = total_items
        else:
            stats["total_items"] = len(self._disk_cache)
        
        return stats


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_type: str = "memory", cache_dir: str = "./data/cache") -> CacheManager:
    """
    Get or create the global cache manager.
    
    Args:
        cache_type: "memory" or "disk"
        cache_dir: Directory for disk cache
        
    Returns:
        CacheManager: Global cache manager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_type=cache_type, cache_dir=cache_dir)
    return _cache_manager


def cached(ttl: int = 300, cache_type: str = "memory"):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds
        cache_type: "memory" or "disk"
        
    Example:
        @cached(ttl=120)
        async def get_price(symbol: str):
            # Expensive API call
            return price
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager(cache_type=cache_type)
            
            # Generate cache key
            cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key, ttl=ttl)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager(cache_type=cache_type)
            
            # Generate cache key
            cache_key = cache_manager._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key, ttl=ttl)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Example usage
if __name__ == "__main__":
    import asyncio
    import time
    
    # Initialize cache
    cache = get_cache_manager(cache_type="memory")
    
    # Test basic operations
    print("Testing cache operations...")
    cache.set("test_key", "test_value", ttl=10)
    value = cache.get("test_key")
    print(f"Retrieved value: {value}")
    
    # Test decorator
    @cached(ttl=5)
    def expensive_function(x: int) -> int:
        print(f"Computing {x}...")
        time.sleep(1)
        return x * 2
    
    print("\nTesting cached decorator...")
    print(f"First call: {expensive_function(5)}")  # Will compute
    print(f"Second call: {expensive_function(5)}")  # Will use cache
    
    # Wait for TTL to expire
    print("\nWaiting for TTL to expire...")
    time.sleep(6)
    print(f"Third call: {expensive_function(5)}")  # Will compute again
    
    # Show statistics
    print("\nCache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Cache test completed!")
