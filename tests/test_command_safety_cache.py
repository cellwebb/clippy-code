"""Tests for command safety agent caching functionality."""

import time
from unittest.mock import Mock

from clippy.agent.command_safety_checker import SafetyCache, SafetyDecision, create_safety_checker


class TestSafetyCache:
    """Test the SafetyCache class directly."""

    def test_cache_basic_operations(self):
        """Test basic cache put/get operations."""
        cache = SafetyCache(max_size=3, ttl=1)

        # Test put
        cache.put("ls -la", "/home/user", True, "Simple listing")
        cache.put("rm -rf", "/tmp", False, "Dangerous command")

        # Test get
        result = cache.get("ls -la", "/home/user")
        assert result == (True, "Simple listing")

        result = cache.get("rm -rf", "/tmp")
        assert result == (False, "Dangerous command")

        # Test miss
        result = cache.get("cat", "/etc")
        assert result is None

    def test_cache_expiration(self):
        """Test that cache entries expire properly."""
        cache = SafetyCache(max_size=10, ttl=1)  # 1 second TTL

        # Add entry
        cache.put("test", "/home", True, "Test reason")

        # Should be available immediately
        result = cache.get("test", "/home")
        assert result == (True, "Test reason")

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result = cache.get("test", "/home")
        assert result is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = SafetyCache(max_size=2, ttl=3600)

        # Fill cache
        cache.put("cmd1", "/dir1", True, "Reason 1")
        cache.put("cmd2", "/dir2", False, "Reason 2")

        # Both should be present
        assert cache.get("cmd1", "/dir1") is not None
        assert cache.get("cmd2", "/dir2") is not None

        # Add third entry (should evict first)
        cache.put("cmd3", "/dir3", True, "Reason 3")

        # First should be evicted, others present
        assert cache.get("cmd1", "/dir1") is None
        assert cache.get("cmd2", "/dir2") is not None
        assert cache.get("cmd3", "/dir3") is not None

    def test_cache_access_order_update(self):
        """Test that accessing entries updates their position."""
        cache = SafetyCache(max_size=2, ttl=3600)

        # Fill cache
        cache.put("cmd1", "/dir1", True, "Reason 1")
        cache.put("cmd2", "/dir2", False, "Reason 2")

        # Access cmd1 to make it recently used
        cache.get("cmd1", "/dir1")

        # Add cmd3 (should evict cmd2, not cmd1)
        cache.put("cmd3", "/dir3", True, "Reason 3")

        # cmd2 should be evicted, cmd1 and cmd3 present
        assert cache.get("cmd1", "/dir1") is not None
        assert cache.get("cmd2", "/dir2") is None
        assert cache.get("cmd3", "/dir3") is not None

    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly."""
        cache = SafetyCache()

        # Same command/directory should generate same key
        key1 = cache._generate_key("ls -la", "/home/user")
        key2 = cache._generate_key("ls -la", "/home/user")
        assert key1 == key2

        # Different commands should generate different keys
        key3 = cache._generate_key("cat file", "/home/user")
        assert key1 != key3

        # Different directories should generate different keys
        key4 = cache._generate_key("ls -la", "/tmp")
        assert key1 != key4

        # Whitespace normalization
        key5 = cache._generate_key("  ls -la  ", "  /home/user  ")
        assert key1 == key5

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = SafetyCache(max_size=5, ttl=3600)
        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 5
        assert stats["ttl"] == 3600

        # Add some entries
        cache.put("cmd1", "/dir1", True, "Reason 1")
        cache.put("cmd2", "/dir2", False, "Reason 2")

        stats = cache.get_stats()
        assert stats["size"] == 2

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = SafetyCache()

        # Add entries
        cache.put("cmd1", "/dir1", True, "Reason 1")
        cache.put("cmd2", "/dir2", False, "Reason 2")

        assert cache.get("cmd1", "/dir1") is not None

        # Clear cache
        cache.clear()

        # Should be empty
        assert cache.get("cmd1", "/dir1") is None
        assert cache.get_stats()["size"] == 0


class TestCommandSafetyCheckerWithCache:
    """Test CommandSafetyChecker with caching enabled."""

    def test_cache_hit(self):
        """Test that cache hits avoid LLM calls."""
        mock_provider = Mock()
        mock_provider.get_streaming_response.return_value = ["ALLOW: Safe command"]

        checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=3600)

        # First call should hit LLM
        result1 = checker.check_command_safety("ls -la", "/home/user")
        assert result1 == (True, "Safe command")
        assert mock_provider.get_streaming_response.call_count == 1

        # Second call should hit cache
        result2 = checker.check_command_safety("ls -la", "/home/user")
        assert result2 == result1
        assert mock_provider.get_streaming_response.call_count == 1  # No additional calls

        # Check cache stats
        stats = checker.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_miss(self):
        """Test that different commands miss cache."""
        mock_provider = Mock()
        mock_provider.get_streaming_response.side_effect = [
            ["ALLOW: Safe command"],
            ["BLOCK: Dangerous command"],
        ]

        checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=3600)

        # Two different commands should both hit LLM
        result1 = checker.check_command_safety("ls -la", "/home/user")
        result2 = checker.check_command_safety("rm -rf", "/tmp")

        assert result1 == (True, "Safe command")
        assert result2 == (False, "Dangerous command")
        assert mock_provider.get_streaming_response.call_count == 2

        # Check cache stats
        stats = checker.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.0

    def test_cache_disabled(self):
        """Test safety checker with cache disabled."""
        mock_provider = Mock()
        mock_provider.get_streaming_response.return_value = ["ALLOW: Safe command"]

        checker = create_safety_checker(mock_provider, cache_size=0, cache_ttl=0)

        assert checker.cache is None

        # Multiple calls should all hit LLM
        result1 = checker.check_command_safety("ls -la", "/home/user")
        result2 = checker.check_command_safety("ls -la", "/home/user")

        assert result1 == result2
        assert mock_provider.get_streaming_response.call_count == 2  # No caching

        # Cache stats should indicate disabled
        stats = checker.get_cache_stats()
        assert stats["enabled"] is False
        assert stats["hits"] == 0
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.0

    def test_cache_not_used_for_errors(self):
        """Test that error results are not cached."""
        mock_provider = Mock()
        mock_provider.get_streaming_response.side_effect = Exception("LLM failed")

        checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=3600)

        # Error call should not be cached
        result1 = checker.check_command_safety("test", "/dir")
        assert result1[0] is False  # Should be blocked due to error
        assert "Safety check failed" in result1[1]

        # Second call should also fail and hit LLM again
        result2 = checker.check_command_safety("test", "/dir")
        assert result2 == result1
        assert mock_provider.get_streaming_response.call_count == 2  # Both calls hit LLM

    def test_cache_clear_functionality(self):
        """Test cache clearing functionality."""
        mock_provider = Mock()
        mock_provider.get_streaming_response.return_value = ["ALLOW: Safe command"]

        checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=3600)

        # Add to cache
        checker.check_command_safety("ls -la", "/home/user")
        stats = checker.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

        # Clear cache
        checker.clear_cache()
        stats = checker.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0  # Stats reset too

        # Call again - should be cache miss
        checker.check_command_safety("ls -la", "/home/user")
        stats = checker.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    def test_cache_performance_stats(self):
        """Test cache performance statistics accuracy."""
        mock_provider = Mock()
        mock_provider.get_streaming_response.return_value = ["ALLOW: Safe command"]

        checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=3600)

        # Multiple calls with mixing
        checker.check_command_safety("cmd1", "/dir1")  # miss
        checker.check_command_safety("cmd1", "/dir1")  # hit
        checker.check_command_safety("cmd2", "/dir2")  # miss
        checker.check_command_safety("cmd1", "/dir1")  # hit
        checker.check_command_safety("cmd3", "/dir3")  # miss

        stats = checker.get_cache_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 3
        assert stats["hit_rate"] == 2 / 5  # 2 hits out of 5 total
        assert stats["enabled"] is True
        assert stats["size"] == 3  # 3 unique commands cached


class TestSafetyDecision:
    """Test the SafetyDecision dataclass."""

    def test_decision_creation(self):
        """Test creating SafetyDecision objects."""
        decision = SafetyDecision(is_safe=True, reason="Safe command", timestamp=time.time())

        assert decision.is_safe is True
        assert decision.reason == "Safe command"
        assert isinstance(decision.timestamp, float)

    def test_decision_expiration(self):
        """Test expiration logic."""
        now = time.time()

        # Not expired
        decision1 = SafetyDecision(True, "Test", now)
        assert not decision1.is_expired(3600)  # 1 hour TTL

        # Expired
        decision2 = SafetyDecision(True, "Test", now - 3700)  # More than 1 hour ago
        assert decision2.is_expired(3600)

        # Not expired with very recent timestamp
        decision3 = SafetyDecision(True, "Test", now - 10)  # 10 seconds ago
        assert not decision3.is_expired(30)  # 30 second TTL
