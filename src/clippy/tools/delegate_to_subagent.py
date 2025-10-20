"""Tool for delegating tasks to specialized subagents."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


# Tool schema for delegate_to_subagent
def get_tool_schema() -> dict[str, Any]:
    """Get the tool schema dynamically to avoid circular imports."""
    try:
        from ..agent.subagent_types import list_subagent_types

        return {
            "type": "function",
            "function": {
                "name": "delegate_to_subagent",
                "description": (
                    "Delegate a complex subtask to a specialized subagent. "
                    "Use this when you need to handle a well-defined subtask that would "
                    "benefit from isolated context, specialized prompting, or parallel execution."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": (
                                "Clear description of the task for the subagent to complete"
                            ),
                        },
                        "subagent_type": {
                            "type": "string",
                            "enum": list_subagent_types(),
                            "description": "Type of specialized subagent to use",
                        },
                        "allowed_tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of tools the subagent is allowed to use (optional)"
                            ),
                        },
                        "context": {
                            "type": "object",
                            "description": (
                                "Additional context to provide to the subagent (optional)"
                            ),
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 300)",
                            "default": 300,
                        },
                        "max_iterations": {
                            "type": "integer",
                            "description": (
                                "Maximum iterations for the subagent (default: from type config)"
                            ),
                            "default": None,
                        },
                    },
                    "required": ["task", "subagent_type"],
                },
            },
        }
    except ImportError:
        # Fallback if subagent_types is not available
        return {
            "type": "function",
            "function": {
                "name": "delegate_to_subagent",
                "description": (
                    "Delegate a complex subtask to a specialized subagent. "
                    "Use this when you need to handle a well-defined subtask that would "
                    "benefit from isolated context, specialized prompting, or parallel execution."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": (
                                "Clear description of the task for the subagent to complete"
                            ),
                        },
                        "subagent_type": {
                            "type": "string",
                            "enum": [
                                "general",
                                "code_review",
                                "testing",
                                "refactor",
                                "documentation",
                            ],
                            "description": "Type of specialized subagent to use",
                        },
                        "allowed_tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of tools the subagent is allowed to use (optional)"
                            ),
                        },
                        "context": {
                            "type": "object",
                            "description": (
                                "Additional context to provide to the subagent (optional)"
                            ),
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 300)",
                            "default": 300,
                        },
                        "max_iterations": {
                            "type": "integer",
                            "description": (
                                "Maximum iterations for the subagent (default: from type config)"
                            ),
                            "default": None,
                        },
                    },
                    "required": ["task", "subagent_type"],
                },
            },
        }


TOOL_SCHEMA = get_tool_schema()


def execute_delegate_to_subagent(
    task: str,
    subagent_type: str,
    allowed_tools: list[str] | None = None,
    context: dict[str, Any] | None = None,
    timeout: int = 300,
    max_iterations: int | None = None,
    **kwargs: Any,
) -> tuple[bool, str, Any]:
    """
    Execute the delegate_to_subagent tool.

    Args:
        task: Clear description of the task for the subagent to complete
        subagent_type: Type of specialized subagent to use
        allowed_tools: List of tools the subagent is allowed to use (optional)
        context: Additional context to provide to the subagent (optional)
        timeout: Timeout in seconds (default: 300)
        max_iterations: Maximum iterations for the subagent (optional)
        **kwargs: Additional keyword arguments

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    # Import here to avoid circular imports
    raise NotImplementedError(
        "delegate_to_subagent tool must be called through the executor with agent context"
    )


def create_subagent_and_execute(
    parent_agent: Any,
    permission_manager: Any,
    task: str,
    subagent_type: str,
    allowed_tools: list[str] | None = None,
    context: dict[str, Any] | None = None,
    timeout: int = 300,
    max_iterations: int | None = None,
) -> tuple[bool, str, Any]:
    """
    Create and execute a subagent with the given parameters.

    This function should be called from the executor with proper context.

    Args:
        parent_agent: The parent ClippyAgent instance
        permission_manager: Permission manager instance
        task: Clear description of the task for the subagent to complete
        subagent_type: Type of specialized subagent to use
        allowed_tools: List of tools the subagent is allowed to use (optional)
        context: Additional context to provide to the subagent (optional)
        timeout: Timeout in seconds (default: 300)
        max_iterations: Maximum iterations for the subagent (optional)

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    try:
        # Import here to avoid circular imports
        from ..agent.subagent import SubAgentConfig, SubAgentResult
        from ..agent.subagent_types import get_default_config

        # Get default configuration for the subagent type
        default_config = get_default_config(subagent_type)

        # Create unique name for this subagent
        import time
        import uuid

        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        name = f"{subagent_type}_{timestamp}_{unique_id}"

        # Override defaults with provided parameters
        if max_iterations is not None:
            default_config["max_iterations"] = max_iterations
        if timeout != 300:
            default_config["timeout"] = timeout
        if allowed_tools is not None:
            default_config["allowed_tools"] = allowed_tools

        # Create subagent configuration
        subagent_config = SubAgentConfig(
            name=name,
            task=task,
            subagent_type=subagent_type,
            system_prompt=default_config.get("system_prompt"),
            allowed_tools=default_config.get("allowed_tools"),
            model=default_config.get("model"),
            max_iterations=default_config.get("max_iterations", 25),
            timeout=default_config.get("timeout", 300),
            context=context or {},
        )

        # Create and run the subagent
        subagent = parent_agent.subagent_manager.create_subagent(subagent_config)
        logger.info(f"Created subagent '{name}' for task: {task[:100]}...")

        # Execute the subagent
        result = subagent.run()

        if result.success:
            message = f"Subagent '{name}' completed successfully. Output: {result.output}"
            logger.info(f"Subagent '{name}' completed successfully")
            return True, message, result
        else:
            message = f"Subagent '{name}' failed: {result.error}"
            logger.error(f"Subagent '{name}' failed: {result.error}")
            return False, message, result

    except Exception as e:
        error_msg = f"Failed to create or execute subagent: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return (
            False,
            error_msg,
            SubAgentResult(
                success=False,
                output="",
                error=error_msg,
                iterations_used=0,
                execution_time=0.0,
                metadata={"failure_reason": "exception"},
            ),
        )
