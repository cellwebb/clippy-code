"""
Example: Using a code review subagent to analyze code quality.

This example demonstrates how to use the 'code_review' subagent type to
perform automated code reviews. The code review subagent is specialized for:
- Analyzing code quality and best practices
- Identifying security vulnerabilities
- Detecting potential bugs
- Providing actionable feedback

The code_review subagent has read-only access to files and uses a specialized
system prompt focused on code quality analysis.
"""

from clippy.agent.core import ClippyAgent
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager
from clippy.providers import LLMProvider


def example_code_review_subagent():
    """Example of using a code review subagent."""

    # Initialize the main agent
    provider = LLMProvider(api_key="your-api-key", model="gpt-4")

    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor()

    agent = ClippyAgent(
        provider=provider,
        permission_manager=permission_manager,
        executor=executor,
    )

    # User asks for a code review
    user_message = """
    Please review the Python files in src/clippy/agent/ for code quality issues.
    Focus on:
    - Code maintainability
    - Security concerns
    - Performance issues
    - Best practices violations
    """

    # The agent will use the delegate_to_subagent tool like this:
    # {
    #     "task": "Review Python files in src/clippy/agent/ for code quality, security, "
    #             "and best practices. Focus on maintainability, security concerns, "
    #             "performance issues, and best practices violations.",
    #     "subagent_type": "code_review",
    #     "context": {
    #         "focus_areas": ["maintainability", "security", "performance", "best_practices"],
    #         "severity_threshold": "medium"
    #     }
    # }

    # The code_review subagent will:
    # 1. List files in src/clippy/agent/
    # 2. Read each Python file
    # 3. Analyze code for issues
    # 4. Generate a comprehensive review report

    # Run the agent
    response = agent.run(user_message)
    print("\n=== Code Review Results ===")
    print(response)

    # Example output:
    # The subagent analyzed 6 Python files and found:
    #
    # HIGH PRIORITY:
    # - src/clippy/agent/core.py:45 - Missing input validation could lead to errors
    # - src/clippy/agent/loop.py:78 - Potential infinite loop condition
    #
    # MEDIUM PRIORITY:
    # - src/clippy/agent/tool_handler.py:123 - Complex function with high cyclomatic complexity
    # - src/clippy/agent/conversation.py:56 - Missing type hints on return value
    #
    # LOW PRIORITY:
    # - src/clippy/agent/utils.py:34 - Variable name could be more descriptive
    #
    # RECOMMENDATIONS:
    # 1. Add input validation at API boundaries
    # 2. Refactor complex functions into smaller units
    # 3. Complete type annotations across all modules


def example_focused_security_review():
    """Example of using code review subagent for security-focused analysis."""

    # User asks specifically for security review
    _user_message = """
    Perform a security audit of src/clippy/executor.py.
    Look for:
    - Command injection vulnerabilities
    - Path traversal issues
    - Unsafe file operations
    - Input validation gaps
    """

    # The agent will delegate to code_review subagent with security context:
    # {
    #     "task": "Security audit of src/clippy/executor.py. Identify command injection, "
    #             "path traversal, unsafe file operations, and input validation issues.",
    #     "subagent_type": "code_review",
    #     "allowed_tools": ["read_file", "grep", "search_files"],
    #     "context": {
    #         "focus": "security",
    #         "vulnerabilities_to_check": [
    #             "command_injection",
    #             "path_traversal",
    #             "unsafe_file_ops",
    #             "input_validation"
    #         ]
    #     },
    #     "timeout": 180
    # }

    # The subagent will provide security-focused analysis
    print("\n=== Security Review Example ===")
    print("Subagent would analyze executor.py for security issues...")


def example_custom_rules_review():
    """Example of code review with custom rules and patterns."""

    # User provides custom review criteria
    _user_message = """
    Review src/clippy/tools/ with these custom rules:
    1. All functions must have docstrings
    2. No function should be longer than 50 lines
    3. All public functions must have type hints
    4. No bare except clauses
    """

    # The agent delegates with custom context:
    # {
    #     "task": "Review src/clippy/tools/ against custom rules: docstrings required, "
    #             "max 50 lines per function, type hints required, no bare excepts.",
    #     "subagent_type": "code_review",
    #     "context": {
    #         "custom_rules": [
    #             "docstrings_required",
    #             "max_function_length_50",
    #             "type_hints_required",
    #             "no_bare_except"
    #         ]
    #     },
    #     "max_iterations": 20
    # }

    print("\n=== Custom Rules Review Example ===")
    print("Subagent would check compliance with custom coding standards...")


if __name__ == "__main__":
    print("=" * 60)
    print("CLIppy Code Review Subagent Examples")
    print("=" * 60)

    print("\nExample 1: General code review")
    print("-" * 60)
    example_code_review_subagent()

    print("\n\nExample 2: Security-focused review")
    print("-" * 60)
    example_focused_security_review()

    print("\n\nExample 3: Custom rules review")
    print("-" * 60)
    example_custom_rules_review()

    print("\n\nKey Benefits of Code Review Subagents:")
    print("- Isolated context focused on code quality")
    print("- Read-only access prevents accidental modifications")
    print("- Specialized prompt for thorough analysis")
    print("- Can review multiple files systematically")
    print("- Provides actionable feedback without changing code")
