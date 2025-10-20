"""
Example: Using parallel testing subagents to generate tests efficiently.

This example demonstrates how to use multiple 'testing' subagents in parallel
to generate comprehensive test suites for multiple modules simultaneously.

Benefits of parallel testing subagents:
- Faster test generation (parallel execution)
- Isolated context per module being tested
- Specialized testing expertise per subagent
- Independent test suites without context pollution
- Better resource utilization
"""

from clippy.agent.core import ClippyAgent
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager
from clippy.providers import LLMProvider


def example_parallel_test_generation():
    """Example of generating tests for multiple modules in parallel."""

    # Initialize the main agent
    provider = LLMProvider(api_key="your-api-key", model="gpt-4")

    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor()

    agent = ClippyAgent(
        provider=provider,
        permission_manager=permission_manager,
        executor=executor,
    )

    # User asks for comprehensive test coverage
    user_message = """
    Generate comprehensive tests for all modules in src/clippy/agent/.
    Each module should have:
    - Unit tests for all public functions
    - Edge case coverage
    - Error handling tests
    - Integration tests where applicable
    """

    # The main agent will identify modules to test and create parallel subagents.
    # It would delegate to multiple testing subagents like this:

    # Subagent 1 - Test core.py
    # {
    #     "task": "Write comprehensive unit tests for src/clippy/agent/core.py including "
    #             "ClippyAgent class, all public methods, edge cases, and error scenarios.",
    #     "subagent_type": "testing",
    #     "context": {
    #         "test_file": "tests/agent/test_core.py",
    #         "coverage_target": 90,
    #         "test_framework": "pytest"
    #     },
    #     "timeout": 300
    # }

    # Subagent 2 - Test loop.py (runs in parallel)
    # {
    #     "task": "Write comprehensive unit tests for src/clippy/agent/loop.py including "
    #             "run_agent_loop function, iteration handling, and error scenarios.",
    #     "subagent_type": "testing",
    #     "context": {
    #         "test_file": "tests/agent/test_loop.py",
    #         "coverage_target": 90,
    #         "test_framework": "pytest"
    #     },
    #     "timeout": 300
    # }

    # Subagent 3 - Test tool_handler.py (runs in parallel)
    # {
    #     "task": "Write comprehensive unit tests for src/clippy/agent/tool_handler.py "
    #             "including handle_tool_use, approval flow, and error handling.",
    #     "subagent_type": "testing",
    #     "context": {
    #         "test_file": "tests/agent/test_tool_handler.py",
    #         "coverage_target": 90,
    #         "test_framework": "pytest"
    #     },
    #     "timeout": 300
    # }

    # All three subagents run concurrently, each:
    # 1. Reading the source file
    # 2. Understanding the code structure
    # 3. Identifying test scenarios
    # 4. Writing comprehensive tests
    # 5. Running tests to verify they work

    response = agent.run(user_message)
    print("\n=== Parallel Test Generation Results ===")
    print(response)

    # Example output:
    # Successfully generated tests for 3 modules in parallel:
    #
    # ✓ tests/agent/test_core.py (15 tests, 92% coverage)
    # ✓ tests/agent/test_loop.py (12 tests, 89% coverage)
    # ✓ tests/agent/test_tool_handler.py (18 tests, 94% coverage)
    #
    # Total execution time: 45 seconds (vs ~120s sequential)
    # All tests passing: 45/45


def example_targeted_test_generation():
    """Example of generating specific types of tests."""

    _user_message = """
    Generate integration tests for the subagent system.
    Focus on:
    - Subagent creation and lifecycle
    - Parallel execution coordination
    - Error handling and recovery
    - Result aggregation
    """

    # The agent delegates to a testing subagent with specific context:
    # {
    #     "task": "Write integration tests for subagent system covering creation, "
    #             "parallel execution, error handling, and result aggregation.",
    #     "subagent_type": "testing",
    #     "allowed_tools": [
    #         "read_file", "read_files", "write_file",
    #         "execute_command", "search_files", "grep"
    #     ],
    #     "context": {
    #         "test_type": "integration",
    #         "test_file": "tests/integration/test_subagent_workflow.py",
    #         "scenarios": [
    #             "subagent_creation",
    #             "parallel_execution",
    #             "error_recovery",
    #             "result_aggregation"
    #         ]
    #     },
    #     "max_iterations": 30,
    #     "timeout": 400
    # }

    print("\n=== Targeted Test Generation Example ===")
    print("Subagent would generate specialized integration tests...")


def example_test_improvement():
    """Example of improving existing tests."""

    _user_message = """
    Review and improve tests in tests/agent/test_core.py.
    Add missing edge cases, improve assertions, and increase coverage.
    """

    # The agent delegates to a testing subagent for test improvement:
    # {
    #     "task": "Review tests/agent/test_core.py and improve by adding edge cases, "
    #             "better assertions, and increasing coverage. Identify gaps.",
    #     "subagent_type": "testing",
    #     "context": {
    #         "source_file": "src/clippy/agent/core.py",
    #         "existing_tests": "tests/agent/test_core.py",
    #         "target_coverage": 95,
    #         "improvement_focus": [
    #             "edge_cases",
    #             "assertion_quality",
    #             "coverage_gaps",
    #             "test_clarity"
    #         ]
    #     },
    #     "timeout": 300
    # }

    print("\n=== Test Improvement Example ===")
    print("Subagent would analyze and enhance existing test suite...")


def example_performance_test_generation():
    """Example of generating performance and load tests."""

    _user_message = """
    Create performance tests for the LLM provider in src/clippy/providers.py.
    Test:
    - Streaming performance
    - Concurrent request handling
    - Memory usage under load
    - Retry logic efficiency
    """

    # The agent delegates with performance testing context:
    # {
    #     "task": "Create performance tests for src/clippy/providers.py covering "
    #             "streaming, concurrency, memory usage, and retry logic.",
    #     "subagent_type": "testing",
    #     "context": {
    #         "test_type": "performance",
    #         "test_file": "tests/performance/test_provider_performance.py",
    #         "metrics": [
    #             "streaming_throughput",
    #             "concurrent_requests",
    #             "memory_usage",
    #             "retry_latency"
    #         ],
    #         "load_levels": [1, 10, 50, 100]
    #     },
    #     "max_iterations": 35,
    #     "timeout": 500
    # }

    print("\n=== Performance Test Generation Example ===")
    print("Subagent would generate load and performance tests...")


def example_test_data_generation():
    """Example of generating test fixtures and data."""

    _user_message = """
    Generate test fixtures for MCP integration tests.
    Create realistic MCP server responses, tool schemas, and error scenarios.
    """

    # The agent delegates for test data generation:
    # {
    #     "task": "Generate test fixtures for MCP integration tests including server "
    #             "responses, tool schemas, and error scenarios.",
    #     "subagent_type": "testing",
    #     "context": {
    #         "fixture_types": [
    #             "mcp_server_responses",
    #             "tool_schemas",
    #             "error_scenarios"
    #         ],
    #         "output_format": "pytest_fixtures",
    #         "fixture_file": "tests/fixtures/mcp_fixtures.py"
    #     },
    #     "timeout": 200
    # }

    print("\n=== Test Data Generation Example ===")
    print("Subagent would create comprehensive test fixtures...")


if __name__ == "__main__":
    print("=" * 60)
    print("CLIppy Parallel Testing Subagent Examples")
    print("=" * 60)

    print("\nExample 1: Parallel test generation")
    print("-" * 60)
    example_parallel_test_generation()

    print("\n\nExample 2: Targeted test generation")
    print("-" * 60)
    example_targeted_test_generation()

    print("\n\nExample 3: Test improvement")
    print("-" * 60)
    example_test_improvement()

    print("\n\nExample 4: Performance test generation")
    print("-" * 60)
    example_performance_test_generation()

    print("\n\nExample 5: Test data generation")
    print("-" * 60)
    example_test_data_generation()

    print("\n\nKey Benefits of Testing Subagents:")
    print("- Parallel execution speeds up test generation")
    print("- Each subagent focuses on one module (better context)")
    print("- Specialized testing expertise and prompting")
    print("- Can generate, improve, and run tests")
    print("- Supports unit, integration, and performance tests")
    print("\nPerformance Comparison:")
    print("- Sequential: ~40s per module × 3 modules = 120s")
    print("- Parallel: ~45s total (3 subagents running concurrently)")
    print("- Speedup: 2.7x faster with parallel execution!")
