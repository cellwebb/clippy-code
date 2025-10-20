"""Subagent result caching system."""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached subagent result."""

    task_hash: str
    subagent_type: str
    result_data: dict[str, Any]
    created_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class SubagentCache:
    """
    Cache system for subagent results to avoid re-executing identical tasks.

    Features:
    - Task-based hashing for cache keys
    - TTL (time-to-live) support
    - LRU eviction when cache is full
    - Access statistics
    """

    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._enabled = True

    def _generate_cache_key(
        self,
        task: str,
        subagent_type: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a cache key for a task.

        Args:
            task: The task description
            subagent_type: Type of subagent
            context: Additional context (optional)

        Returns:
            Cache key string
        """
        # Create a deterministic hash from task, type, and context
        cache_data = {
            "task": task,
            "subagent_type": subagent_type,
            "context": context or {},
        }

        # Convert to JSON string for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_json.encode()).hexdigest()

    def get(
        self,
        task: str,
        subagent_type: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Get a cached result if available and not expired.

        Args:
            task: The task description
            subagent_type: Type of subagent
            context: Additional context (optional)

        Returns:
            Cached result data or None if not found/expired
        """
        if not self._enabled:
            return None

        cache_key = self._generate_cache_key(task, subagent_type, context)

        if cache_key not in self._cache:
            logger.debug(f"Cache miss for key: {cache_key[:16]}...")
            return None

        entry = self._cache[cache_key]
        current_time = time.time()

        # Check if entry is expired
        if current_time - entry.created_at > self.default_ttl:
            logger.debug(f"Cache entry expired for key: {cache_key[:16]}...")
            del self._cache[cache_key]
            return None

        # Update access statistics
        entry.access_count += 1
        entry.last_accessed = current_time

        logger.debug(
            "Cache hit for key: %s... (accessed %d times)",
            cache_key[:16],
            entry.access_count,
        )
        return entry.result_data

    def put(
        self,
        task: str,
        subagent_type: str,
        result_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Store a result in the cache.

        Args:
            task: The task description
            subagent_type: Type of subagent
            result_data: Result data to cache
            context: Additional context (optional)
        """
        if not self._enabled:
            return

        cache_key = self._generate_cache_key(task, subagent_type, context)
        current_time = time.time()

        # Evict entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        # Create new cache entry
        entry = CacheEntry(
            task_hash=cache_key,
            subagent_type=subagent_type,
            result_data=result_data,
            created_at=current_time,
        )

        self._cache[cache_key] = entry
        logger.debug(f"Cached result for key: {cache_key[:16]}...")

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # Find the entry with the oldest last_accessed time
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        logger.debug(f"Evicted LRU entry: {lru_key[:16]}...")

    def clear(self) -> None:
        """Clear all cached entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached entries")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()

        # Count entries by subagent type
        type_counts: dict[str, int] = {}
        expired_count = 0

        for entry in self._cache.values():
            # Count by type
            type_counts[entry.subagent_type] = type_counts.get(entry.subagent_type, 0) + 1

            # Count expired entries
            if current_time - entry.created_at > self.default_ttl:
                expired_count += 1

        # Calculate average access count
        avg_access = (
            sum(entry.access_count for entry in self._cache.values()) / len(self._cache)
            if self._cache
            else 0
        )

        return {
            "enabled": self._enabled,
            "total_entries": len(self._cache),
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
            "expired_entries": expired_count,
            "entries_by_type": type_counts,
            "average_access_count": round(avg_access, 2),
            "memory_usage_mb": round(self._estimate_memory_usage() / (1024 * 1024), 2),
        }

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        total_size = 0
        for key, entry in self._cache.items():
            # Rough estimation: key size + entry data size
            total_size += len(key.encode())
            total_size += len(json.dumps(entry.result_data).encode())
        return total_size

    def enable(self) -> None:
        """Enable the cache."""
        self._enabled = True
        logger.info("Subagent cache enabled")

    def disable(self) -> None:
        """Disable the cache."""
        self._enabled = False
        logger.info("Subagent cache disabled")

    def is_enabled(self) -> bool:
        """Check if cache is enabled."""
        return self._enabled

    def set_ttl(self, ttl: int) -> None:
        """
        Set the default TTL.

        Args:
            ttl: TTL in seconds
        """
        self.default_ttl = ttl
        logger.info(f"Cache TTL set to {ttl} seconds")

    def set_max_size(self, max_size: int) -> None:
        """
        Set the maximum cache size.

        Args:
            max_size: Maximum number of entries
        """
        old_size = self.max_size
        self.max_size = max_size

        # Evict entries if new size is smaller
        while len(self._cache) > self.max_size:
            self._evict_lru()

        logger.info(f"Cache max size changed from {old_size} to {max_size}")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if current_time - entry.created_at > self.default_ttl
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)


# Global cache instance
_global_cache: SubagentCache | None = None


def get_global_cache() -> SubagentCache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        # Load configuration from environment
        import os

        max_size = int(os.getenv("CLIPPY_SUBAGENT_CACHE_SIZE", "100"))
        ttl = int(os.getenv("CLIPPY_SUBAGENT_CACHE_TTL", "3600"))

        _global_cache = SubagentCache(max_size=max_size, default_ttl=ttl)
        logger.info(f"Initialized global subagent cache: max_size={max_size}, ttl={ttl}s")

    return _global_cache


def reset_global_cache() -> None:
    """Reset the global cache instance."""
    global _global_cache
    _global_cache = None
    logger.info("Reset global subagent cache")
