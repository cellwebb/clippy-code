#!/usr/bin/env python3
"""
Demonstration of the safety agent caching functionality.

This script shows how the safety agent caches decisions to improve performance
and reduce API calls for repeated commands.
"""

import sys
from pathlib import Path
from time import sleep
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clippy.agent.command_safety_checker import create_safety_checker


def demonstrate_cache_performance():
    """Demonstrate cache performance improvements."""
    print("🚀 Safety Agent Cache Performance Demo")
    print("=" * 50)

    # Create mock provider
    mock_provider = Mock()
    mock_provider.get_streaming_response.return_value = ["ALLOW: Safe file operation"]

    # Create safety checker with cache enabled
    checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=3600)

    # Test cache performance
    commands_to_test = [
        ("ls -la", "/home/user"),
        ("cat README.md", "/home/user/project"),
        ("python app.py", "/home/user/project"),
        ("git status", "/home/user/project"),
        ("npm run dev", "/home/user/project"),
    ]

    print("\n📊 Testing cache hits and misses:")
    print("-" * 30)

    # First round - should be all cache misses
    print("First round (all cache misses):")
    for cmd, directory in commands_to_test:
        is_safe, reason = checker.check_command_safety(cmd, directory)
        print(f"  {cmd} in {directory}: {'✅' if is_safe else '🚫'} {reason}")

    print(f"\nAPI calls made: {mock_provider.get_streaming_response.call_count}")

    # Get cache stats
    stats = checker.get_cache_stats()
    print(
        f"Cache stats: {stats['hits']} hits, {stats['misses']} misses, "
        f"{stats['hit_rate']:.1%} hit rate"
    )

    # Second round - should be all cache hits
    print("\nSecond round (all cache hits):")
    mock_provider.get_streaming_response.call_count = 0  # Reset counter

    for cmd, directory in commands_to_test:
        is_safe, reason = checker.check_command_safety(cmd, directory)
        print(f"  {cmd} in {directory}: {'✅' if is_safe else '🚫'} {reason}")

    print(f"\nAPI calls made: {mock_provider.get_streaming_response.call_count}")

    # Get cache stats again
    stats = checker.get_cache_stats()
    print(
        f"Cache stats: {stats['hits']} hits, {stats['misses']} misses, "
        f"{stats['hit_rate']:.1%} hit rate"
    )


def demonstrate_cache_expiration():
    """Demonstrate cache expiration functionality."""
    print("\n\n⏰ Cache Expiration Demo")
    print("=" * 30)

    mock_provider = Mock()
    mock_provider.get_streaming_response.return_value = ["ALLOW: Time-sensitive operation"]

    # Create checker with 2-second TTL
    checker = create_safety_checker(mock_provider, cache_size=100, cache_ttl=2)

    command = "ls -la"
    directory = "/tmp"

    print(f"\nTesting command: {command} in {directory}")

    # First call - should hit LLM
    print("1. First call (cache miss):")
    is_safe, reason = checker.check_command_safety(command, directory)
    api_calls_1 = mock_provider.get_streaming_response.call_count
    print(f"   Result: {'✅' if is_safe else '🚫'} {reason}")
    print(f"   API calls: {api_calls_1}")

    # Second call immediately - should hit cache
    print("2. Second call immediately (cache hit):")
    is_safe, reason = checker.check_command_safety(command, directory)
    api_calls_2 = mock_provider.get_streaming_response.call_count
    print(f"   Result: {'✅' if is_safe else '🚫'} {reason}")
    print(f"   Additional API calls: {api_calls_2 - api_calls_1}")

    # Wait for expiration
    print("3. Waiting 3 seconds for cache expiration...")
    sleep(3)

    # Third call after expiration - should miss cache again
    print("4. Third call after expiration (cache miss):")
    is_safe, reason = checker.check_command_safety(command, directory)
    api_calls_3 = mock_provider.get_streaming_response.call_count
    print(f"   Result: {'✅' if is_safe else '🚫'} {reason}")
    print(f"   Additional API calls: {api_calls_3 - api_calls_2}")


def demonstrate_cache_size_management():
    """Demonstrate LRU cache size management."""
    print("\n\n📦 Cache Size Management (LRU) Demo")
    print("=" * 40)

    mock_provider = Mock()
    mock_provider.get_streaming_response.return_value = ["ALLOW: Cached operation"]

    # Create small cache (size 3)
    checker = create_safety_checker(mock_provider, cache_size=3, cache_ttl=3600)

    commands = [
        ("cmd1", "/dir1"),
        ("cmd2", "/dir2"),
        ("cmd3", "/dir3"),
        ("cmd4", "/dir4"),  # Should evict cmd1
        ("cmd5", "/dir5"),  # Should evict cmd2
    ]

    print("Adding commands to cache (size=3):")

    for i, (cmd, directory) in enumerate(commands, 1):
        mock_provider.get_streaming_response.call_count = 0
        checker.check_command_safety(cmd, directory)
        api_calls = mock_provider.get_streaming_response.call_count

        stats = checker.get_cache_stats()
        print(f"{i}. {cmd} in {directory}: {api_calls} API calls, cache size: {stats['size']}")

    print(f"\nFinal cache: {checker.get_cache_stats()}")

    # Test which commands are cached
    print("\nTesting which commands remain in cache:")
    test_commands = [
        ("cmd1", "/dir1"),
        ("cmd2", "/dir2"),
        ("cmd3", "/dir3"),
        ("cmd4", "/dir4"),
        ("cmd5", "/dir5"),
    ]
    for cmd, directory in test_commands:
        mock_provider.get_streaming_response.call_count = 0
        checker.check_command_safety(cmd, directory)
        api_calls = mock_provider.get_streaming_response.call_count
        cached = "✅ cached" if api_calls == 0 else "❌ not cached (API call made)"
        print(f"  {cmd} in {directory}: {cached}")


def demonstrate_cache_disabled():
    """Demonstrate behavior with cache disabled."""
    print("\n\n⚙️ Cache Disabled Demo")
    print("=" * 25)

    mock_provider = Mock()
    mock_provider.get_streaming_response.return_value = ["ALLOW: Uncached operation"]

    # Create checker with cache disabled
    checker = create_safety_checker(mock_provider, cache_size=0, cache_ttl=0)

    command = "ls -la"
    directory = "/tmp"

    print("\nTesting repeated calls with cache disabled:")

    # Multiple calls - should all hit LLM
    for i in range(4):
        mock_provider.get_streaming_response.call_count = 0
        is_safe, reason = checker.check_command_safety(command, directory)
        api_calls = mock_provider.get_streaming_response.call_count

        print(f"  Call {i + 1}: {api_calls} API call(s) {'✅' if is_safe else '🚫'} {reason}")

    stats = checker.get_cache_stats()
    print(
        f"\nCache stats: enabled={stats['enabled']}, hits={stats['hits']}, misses={stats['misses']}"
    )


def main():
    """Run all cache demonstrations."""
    print("📎 Clippy Safety Agent Caching Demonstration")
    print("👀 This shows how caching improves performance and reduces API costs")
    print()

    try:
        demonstrate_cache_performance()
        demonstrate_cache_expiration()
        demonstrate_cache_size_management()
        demonstrate_cache_disabled()

        print("\n\n✨ Demo Complete!")
        print("\nKey Takeaways:")
        print("• Cache reduces API calls for repeated commands (same command + directory)")
        print("• LRU eviction manages cache size automatically")
        print("• TTL ensures cache entries expire periodically")
        print("• Cache can be disabled for memory-constrained environments")
        print("• Performance tracking shows cache effectiveness")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
