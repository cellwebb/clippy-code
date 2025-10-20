"""
Example: Using refactoring subagents to improve code quality.

This example demonstrates how to use the 'refactor' subagent type to
restructure and improve code while preserving functionality.

Refactoring subagent capabilities:
- Extract common patterns and reduce duplication
- Improve code structure and readability
- Apply SOLID principles and design patterns
- Modernize legacy code
- Preserve functionality (tests still pass)
"""

from clippy.agent.core import ClippyAgent
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager
from clippy.providers import LLMProvider


def example_extract_common_patterns():
    """Example of refactoring to extract common patterns."""

    # Initialize the main agent
    provider = LLMProvider(api_key="your-api-key", model="gpt-4")

    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor()

    agent = ClippyAgent(
        provider=provider,
        permission_manager=permission_manager,
        executor=executor,
    )

    # User asks for refactoring to reduce duplication
    user_message = """
    Refactor the tools module (src/clippy/tools/) to extract common patterns.
    I notice a lot of duplicated error handling and validation logic.
    Create shared utilities to reduce duplication.
    """

    # The agent delegates to a refactor subagent:
    # {
    #     "task": "Analyze src/clippy/tools/ for common patterns in error handling and "
    #             "validation. Extract shared utilities to reduce duplication.",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "target_directory": "src/clippy/tools/",
    #         "patterns_to_extract": [
    #             "error_handling",
    #             "input_validation",
    #             "result_formatting"
    #         ],
    #         "preserve_tests": True,
    #         "run_tests_after": True
    #     },
    #     "timeout": 600
    # }

    # The refactor subagent will:
    # 1. Read all tool files
    # 2. Identify duplicated patterns
    # 3. Extract common utilities (e.g., src/clippy/tools/common.py)
    # 4. Update tool files to use shared utilities
    # 5. Verify tests still pass
    # 6. Provide refactoring summary

    response = agent.run(user_message)
    print("\n=== Refactoring Results ===")
    print(response)

    # Example output:
    # Refactoring complete! Extracted common patterns:
    #
    # Created: src/clippy/tools/common.py
    # - validate_path() - Used by 8 tools
    # - format_error_result() - Used by 12 tools
    # - check_file_exists() - Used by 6 tools
    #
    # Updated files:
    # - src/clippy/tools/read_file.py (-15 lines)
    # - src/clippy/tools/write_file.py (-18 lines)
    # - src/clippy/tools/delete_file.py (-12 lines)
    # ... (8 more files)
    #
    # Total reduction: 156 lines of duplicated code
    # Tests: 47/47 passing ✓


def example_improve_code_structure():
    """Example of restructuring code for better organization."""

    _user_message = """
    The executor.py file is too large and has too many responsibilities.
    Refactor it to follow Single Responsibility Principle.
    Split into smaller, focused modules.
    """

    # The agent delegates with structural refactoring context:
    # {
    #     "task": "Refactor src/clippy/executor.py to follow Single Responsibility "
    #             "Principle. Split into smaller focused modules.",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "source_file": "src/clippy/executor.py",
    #         "refactoring_type": "split_responsibilities",
    #         "principles": ["SRP", "separation_of_concerns"],
    #         "new_structure": {
    #             "executor/": [
    #                 "core.py",      # Main execution logic
    #                 "file_ops.py",  # File operation handlers
    #                 "cmd_ops.py",   # Command execution handlers
    #                 "validators.py" # Input validation
    #             ]
    #         }
    #     },
    #     "max_iterations": 35,
    #     "timeout": 600
    # }

    print("\n=== Structural Refactoring Example ===")
    print("Subagent would split large file into focused modules...")


def example_modernize_code():
    """Example of modernizing legacy code with new patterns."""

    _user_message = """
    Modernize src/clippy/permissions.py to use:
    - Python 3.10+ features (pattern matching, union types)
    - Dataclasses instead of manual __init__
    - Type hints throughout
    - Modern best practices
    """

    # The agent delegates for modernization:
    # {
    #     "task": "Modernize src/clippy/permissions.py with Python 3.10+ features, "
    #             "dataclasses, complete type hints, and modern best practices.",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "modernization_targets": [
    #             "pattern_matching",
    #             "union_types",
    #             "dataclasses",
    #             "type_hints",
    #             "walrus_operator"
    #         ],
    #         "python_version": "3.10+",
    #         "preserve_api": True
    #     },
    #     "timeout": 400
    # }

    print("\n=== Code Modernization Example ===")
    print("Subagent would update code to use modern Python features...")


def example_apply_design_pattern():
    """Example of applying a design pattern to improve architecture."""

    _user_message = """
    The tool execution logic could benefit from the Strategy pattern.
    Refactor to use Strategy pattern for different tool execution strategies.
    """

    # The agent delegates with design pattern context:
    # {
    #     "task": "Refactor tool execution logic to use Strategy pattern for different "
    #             "execution strategies (sync, async, cached, etc.).",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "design_pattern": "strategy",
    #         "target_component": "tool_execution",
    #         "strategies": [
    #             "SyncExecutionStrategy",
    #             "AsyncExecutionStrategy",
    #             "CachedExecutionStrategy"
    #         ],
    #         "benefits": [
    #             "easier_to_add_new_strategies",
    #             "cleaner_separation",
    #             "more_testable"
    #         ]
    #     },
    #     "max_iterations": 40,
    #     "timeout": 500
    # }

    print("\n=== Design Pattern Application Example ===")
    print("Subagent would refactor to use Strategy pattern...")


def example_simplify_complex_function():
    """Example of simplifying a complex function."""

    _user_message = """
    The run_agent_loop function in src/clippy/agent/loop.py is too complex.
    Simplify by extracting helper functions and reducing cognitive complexity.
    """

    # The agent delegates for complexity reduction:
    # {
    #     "task": "Simplify run_agent_loop in src/clippy/agent/loop.py by extracting "
    #             "helper functions and reducing cognitive complexity.",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "target_function": "run_agent_loop",
    #         "complexity_metrics": {
    #             "current_cyclomatic": 18,
    #             "target_cyclomatic": 10,
    #             "current_lines": 120,
    #             "target_lines": 60
    #         },
    #         "refactoring_techniques": [
    #             "extract_method",
    #             "simplify_conditionals",
    #             "reduce_nesting"
    #         ]
    #     },
    #     "timeout": 350
    # }

    print("\n=== Function Simplification Example ===")
    print("Subagent would break down complex function into simpler pieces...")


def example_improve_error_handling():
    """Example of refactoring to improve error handling."""

    _user_message = """
    Improve error handling throughout src/clippy/mcp/.
    Use custom exceptions instead of generic ones.
    Add proper error context and recovery strategies.
    """

    # The agent delegates for error handling improvements:
    # {
    #     "task": "Improve error handling in src/clippy/mcp/ with custom exceptions, "
    #             "better context, and recovery strategies.",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "improvements": [
    #             "create_custom_exceptions",
    #             "add_error_context",
    #             "implement_recovery",
    #             "improve_error_messages"
    #         ],
    #         "exception_hierarchy": {
    #             "MCPError": [
    #                 "MCPConnectionError",
    #                 "MCPToolError",
    #                 "MCPConfigError"
    #             ]
    #         }
    #     },
    #     "max_iterations": 30,
    #     "timeout": 450
    # }

    print("\n=== Error Handling Improvement Example ===")
    print("Subagent would refactor error handling with custom exceptions...")


def example_refactor_with_tests():
    """Example of refactoring while maintaining test coverage."""

    _user_message = """
    Refactor src/clippy/providers.py to separate concerns.
    Ensure all existing tests still pass and coverage remains above 85%.
    """

    # The agent delegates with test-driven refactoring:
    # {
    #     "task": "Refactor src/clippy/providers.py to separate concerns while "
    #             "maintaining test coverage above 85%.",
    #     "subagent_type": "refactor",
    #     "context": {
    #         "test_driven": True,
    #         "existing_tests": "tests/test_providers.py",
    #         "coverage_threshold": 85,
    #         "verification_steps": [
    #             "run_tests_before",
    #             "perform_refactoring",
    #             "run_tests_after",
    #             "check_coverage"
    #         ]
    #     },
    #     "timeout": 500
    # }

    print("\n=== Test-Driven Refactoring Example ===")
    print("Subagent would refactor while ensuring tests pass...")


if __name__ == "__main__":
    print("=" * 60)
    print("CLIppy Refactoring Subagent Examples")
    print("=" * 60)

    print("\nExample 1: Extract common patterns")
    print("-" * 60)
    example_extract_common_patterns()

    print("\n\nExample 2: Improve code structure")
    print("-" * 60)
    example_improve_code_structure()

    print("\n\nExample 3: Modernize code")
    print("-" * 60)
    example_modernize_code()

    print("\n\nExample 4: Apply design pattern")
    print("-" * 60)
    example_apply_design_pattern()

    print("\n\nExample 5: Simplify complex function")
    print("-" * 60)
    example_simplify_complex_function()

    print("\n\nExample 6: Improve error handling")
    print("-" * 60)
    example_improve_error_handling()

    print("\n\nExample 7: Test-driven refactoring")
    print("-" * 60)
    example_refactor_with_tests()

    print("\n\nKey Benefits of Refactoring Subagents:")
    print("- Specialized in code improvement patterns")
    print("- Preserves functionality (tests pass)")
    print("- Isolated context prevents unrelated changes")
    print("- Can handle large refactoring projects")
    print("- Follows SOLID and DRY principles")
    print("- Provides clear explanations of changes")
    print("\nRefactoring Techniques Supported:")
    print("- Extract common patterns")
    print("- Split responsibilities (SRP)")
    print("- Apply design patterns")
    print("- Modernize code")
    print("- Reduce complexity")
    print("- Improve error handling")
