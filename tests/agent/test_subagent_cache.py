"""Tests for the subagent caching system."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from clippy.agent.subagent_cache import (
    SubagentCache,
    get_global_cache,
    reset_global_cache,
)


class TimeController:
    """Deterministic time helper for cache tests."""

    def __init__(self, start: float = 1_000.0) -> None:
        self._current = start

    def __call__(self) -> float:
        return self._current

    def advance(self, seconds: float) -> float:
        """Move the mocked clock forward."""
        self._current += seconds
        return self._current


def _patched_time(monkeypatch: pytest.MonkeyPatch) -> TimeController:
    """Patch ``time.time`` inside the cache module and return the controller."""
    controller = TimeController()
    monkeypatch.setattr("clippy.agent.subagent_cache.time.time", controller)
    return controller


def _first_cache_key(cache: SubagentCache) -> str:
    """Return the first key in the internal cache for convenience assertions."""
    return next(iter(cache._cache.keys()))


def test_put_get_updates_statistics(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = _patched_time(monkeypatch)
    cache = SubagentCache(max_size=5, default_ttl=60)

    cache.put("summarise file", "general", {"result": "done"})
    controller.advance(1)
    result = cache.get("summarise file", "general")

    assert result == {"result": "done"}

    entry = cache._cache[_first_cache_key(cache)]
    assert entry.access_count == 1
    assert entry.last_accessed == pytest.approx(controller())

    stats = cache.get_statistics()
    assert stats["total_entries"] == 1
    assert stats["average_access_count"] == 1
    assert stats["entries_by_type"]["general"] == 1


def test_get_returns_none_for_expired_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = _patched_time(monkeypatch)
    cache = SubagentCache(max_size=5, default_ttl=10)

    cache.put("draft email", "documentation", {"content": "hello"})
    controller.advance(11)

    assert cache.get("draft email", "documentation") is None
    assert cache.get_statistics()["total_entries"] == 0


def test_lru_eviction_removes_oldest_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = _patched_time(monkeypatch)
    cache = SubagentCache(max_size=2, default_ttl=60)

    cache.put("task-1", "general", {"id": 1})
    key_one = cache._generate_cache_key("task-1", "general")

    controller.advance(1)
    cache.put("task-2", "general", {"id": 2})
    controller.advance(1)
    cache.put("task-3", "general", {"id": 3})

    assert len(cache._cache) == 2
    assert key_one not in cache._cache


def test_disable_prevents_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = _patched_time(monkeypatch)
    cache = SubagentCache(max_size=3, default_ttl=30)

    cache.disable()
    cache.put("task", "general", {"state": "skip"})
    assert not cache._cache

    cache.enable()
    cache.put("task", "general", {"state": "store"})
    key = cache._generate_cache_key("task", "general")
    assert key in cache._cache

    cache.disable()
    controller.advance(1)
    assert cache.get("task", "general") is None

    cache.enable()
    assert cache.get("task", "general") == {"state": "store"}


def test_set_max_size_triggers_eviction(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = _patched_time(monkeypatch)
    cache = SubagentCache(max_size=3, default_ttl=120)

    for index in range(3):
        cache.put(f"task-{index}", "general", {"id": index})
        controller.advance(1)

    cache.set_max_size(1)

    assert cache.max_size == 1
    assert len(cache._cache) == 1
    remaining_entry: Iterator[str] = iter(cache._cache.keys())
    remaining_key = next(remaining_entry)
    assert cache._cache[remaining_key].result_data == {"id": 2}


def test_cleanup_expired_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    controller = _patched_time(monkeypatch)
    cache = SubagentCache(max_size=5, default_ttl=5)

    cache.put("fresh-task", "general", {"id": 1})
    controller.advance(1)
    cache.put("old-task", "general", {"id": 2})

    controller.advance(5)
    stats = cache.get_statistics()
    assert stats["expired_entries"] == 1

    removed = cache.cleanup_expired()
    assert removed == 1
    assert len(cache._cache) == 1


def test_global_cache_respects_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_global_cache()
    monkeypatch.setenv("CLIPPY_SUBAGENT_CACHE_SIZE", "7")
    monkeypatch.setenv("CLIPPY_SUBAGENT_CACHE_TTL", "42")

    cache = get_global_cache()
    assert cache.max_size == 7
    assert cache.default_ttl == 42
    assert get_global_cache() is cache

    reset_global_cache()
