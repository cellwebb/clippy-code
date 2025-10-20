"""Tool for running multiple subagents in parallel."""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

# Module-level references for test mocking
# These are set to None and imported lazily to avoid circular imports

if TYPE_CHECKING:
    from ..agent.subagent import SubAgent as SubAgentType
    from ..agent.subagent import SubAgentConfig as SubAgentConfigType

SubAgent: type["SubAgentType"] | None = None
SubAgentConfig: type["SubAgentConfigType"] | None = None
get_default_config: Callable[[str], dict[str, Any]] | None = None


def _ensure_imports() -> None:
    """Ensure imports are loaded for use."""
    global SubAgent, SubAgentConfig, get_default_config
    # Only import if not already set (allows tests to mock before calling)
    if SubAgent is None or SubAgentConfig is None or get_default_config is None:
        # Only import the ones that are None
        if SubAgent is None or SubAgentConfig is None:
            from ..agent import subagent as subagent_module

            if SubAgent is None:
                SubAgent = subagent_module.SubAgent
            if SubAgentConfig is None:
                SubAgentConfig = subagent_module.SubAgentConfig
        if get_default_config is None:
            from ..agent import subagent_types as subagent_types_module

            get_default_config = subagent_types_module.get_default_config


# Re-export for test mocking - these are imported lazily in functions
def list_subagent_types() -> list[str]:
    """Get list of available subagent types."""
    from ..agent.subagent_types import list_subagent_types as lst

    return lst()


# Tool schema for run_parallel_subagents
def get_tool_schema() -> dict[str, Any]:
    """Get the tool schema dynamically."""
    try:
        return {
            "type": "function",
            "function": {
                "name": "run_parallel_subagents",
                "description": (
                    "Run multiple subagents in parallel to handle independent tasks concurrently. "
                    "Use this when you have multiple independent subtasks that can be executed "
                    "simultaneously to save time and improve efficiency."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subagents": {
                            "type": "array",
                            "description": "List of subagent configurations to run in parallel",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task": {
                                        "type": "string",
                                        "description": (
                                            "Clear description of the task for this subagent"
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
                                            "List of tools the subagent is allowed to use "
                                            "(optional)"
                                        ),
                                    },
                                    "context": {
                                        "type": "object",
                                        "description": (
                                            "Additional context to provide to the subagent "
                                            "(optional)"
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
                                            "Maximum iterations for the subagent "
                                            "(default: from type config)"
                                        ),
                                        "default": None,
                                    },
                                },
                                "required": ["task", "subagent_type"],
                            },
                        },
                        "max_concurrent": {
                            "type": "integer",
                            "description": (
                                "Maximum number of subagents to run concurrently (default: 3)"
                            ),
                            "default": 3,
                        },
                        "fail_fast": {
                            "type": "boolean",
                            "description": (
                                "If True, stop all subagents if one fails (default: False)"
                            ),
                            "default": False,
                        },
                        "aggregate_results": {
                            "type": "boolean",
                            "description": (
                                "If True, aggregate results into a single summary (default: True)"
                            ),
                            "default": True,
                        },
                    },
                    "required": ["subagents"],
                },
            },
        }
    except ImportError:
        # Fallback if subagent_types is not available
        return {
            "type": "function",
            "function": {
                "name": "run_parallel_subagents",
                "description": (
                    "Run multiple subagents in parallel to handle independent tasks concurrently. "
                    "Use this when you have multiple independent subtasks that can be executed "
                    "simultaneously to save time and improve efficiency."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subagents": {
                            "type": "array",
                            "description": "List of subagent configurations to run in parallel",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task": {
                                        "type": "string",
                                        "description": (
                                            "Clear description of the task for this subagent"
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
                                },
                                "required": ["task", "subagent_type"],
                            },
                        },
                        "max_concurrent": {
                            "type": "integer",
                            "description": (
                                "Maximum number of subagents to run concurrently (default: 3)"
                            ),
                            "default": 3,
                        },
                    },
                    "required": ["subagents"],
                },
            },
        }


TOOL_SCHEMA = get_tool_schema()


def execute_run_parallel_subagents(
    subagents: list[dict[str, Any]],
    max_concurrent: int = 3,
    fail_fast: bool = False,
    aggregate_results: bool = True,
    **kwargs: Any,
) -> tuple[bool, str, Any]:
    """
    Execute the run_parallel_subagents tool.

    Args:
        subagents: List of subagent configurations to run in parallel
        max_concurrent: Maximum number of subagents to run concurrently
        fail_fast: If True, stop all subagents if one fails
        aggregate_results: If True, aggregate results into a single summary
        **kwargs: Additional keyword arguments

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    # Import here to avoid circular imports
    raise NotImplementedError(
        "run_parallel_subagents tool must be called through the executor with agent context"
    )


def create_parallel_subagents_and_execute(
    parent_agent: Any,
    permission_manager: Any,
    subagents: list[dict[str, Any]],
    max_concurrent: int = 3,
    fail_fast: bool = False,
    aggregate_results: bool = True,
) -> tuple[bool, str, Any]:
    """
    Create and execute multiple subagents in parallel with the given parameters.

    This function should be called from the executor with proper context.

    Args:
        parent_agent: The parent ClippyAgent instance
        permission_manager: Permission manager instance
        subagents: List of subagent configurations to run in parallel
        max_concurrent: Maximum number of subagents to run concurrently
        fail_fast: If True, stop all subagents if one fails
        aggregate_results: If True, aggregate results into a single summary

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    try:
        # Ensure imports are loaded
        _ensure_imports()

        if get_default_config is None or SubAgentConfig is None:
            raise RuntimeError("Failed to load subagent dependencies")

        assert get_default_config is not None
        assert SubAgentConfig is not None

        logger.info(f"Creating {len(subagents)} subagents for parallel execution")

        # Handle empty list case
        if not subagents:
            message = "No subagents to execute"
            return True, message, []

        # Create subagent configurations
        subagent_configs: list[Any] = []
        for i, subagent_config in enumerate(subagents):
            # Get default configuration for the subagent type
            default_config = get_default_config(subagent_config["subagent_type"])

            # Create unique name for this subagent
            import time
            import uuid

            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            name = f"{subagent_config['subagent_type']}_{i + 1}_{timestamp}_{unique_id}"

            # Override defaults with provided parameters
            config = default_config.copy()
            if (
                "max_iterations" in subagent_config
                and subagent_config["max_iterations"] is not None
            ):
                config["max_iterations"] = subagent_config["max_iterations"]
            if "timeout" in subagent_config and subagent_config["timeout"] != 300:
                config["timeout"] = subagent_config["timeout"]
            if "allowed_tools" in subagent_config:
                config["allowed_tools"] = subagent_config["allowed_tools"]

            # Create subagent configuration
            subagent_config_obj = SubAgentConfig(
                name=name,
                task=subagent_config["task"],
                subagent_type=subagent_config["subagent_type"],
                system_prompt=config.get("system_prompt"),
                allowed_tools=config.get("allowed_tools"),
                model=config.get("model"),
                max_iterations=config.get("max_iterations", 25),
                timeout=config.get("timeout", 300),
                context=subagent_config.get("context", {}),
            )

            subagent_configs.append(subagent_config_obj)

        # Create subagent instances
        subagent_instances: list[Any] = []
        for config in subagent_configs:
            subagent = parent_agent.subagent_manager.create_subagent(config)
            subagent_instances.append(subagent)
            logger.info(f"Created subagent '{config.name}' for task: {config.task[:50]}...")

        # Execute subagents in parallel
        logger.info(
            f"Running {len(subagent_instances)} subagents in parallel "
            f"(max_concurrent={max_concurrent})"
        )
        results = parent_agent.subagent_manager.run_parallel(
            subagent_instances, max_concurrent=max_concurrent
        )

        # Analyze results
        successful_count = sum(1 for result in results if result.success)
        failed_count = len(results) - successful_count

        if fail_fast and failed_count > 0:
            message = (
                f"Parallel execution stopped early: {successful_count} succeeded, "
                f"{failed_count} failed"
            )
            logger.warning(message)
        else:
            message = (
                f"Parallel execution completed: {successful_count} succeeded, {failed_count} failed"
            )
            logger.info(message)

        # Aggregate results if requested
        if aggregate_results:
            summary = _aggregate_results(results)
            message += f"\n\n{summary}"
            result = {
                "individual_results": [
                    {
                        "name": subagent_instances[i].config.name,
                        "task": subagent_instances[i].config.task,
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                        "execution_time": result.execution_time,
                        "iterations_used": result.iterations_used,
                    }
                    for i, result in enumerate(results)
                ],
                "summary": summary,
                "total_successful": successful_count,
                "total_failed": failed_count,
                "total_execution_time": sum(r.execution_time for r in results),
            }
        else:
            result = results

        # Determine overall success
        overall_success = failed_count == 0 or (not fail_fast and successful_count > 0)

        return overall_success, message, result

    except Exception as e:
        error_msg = f"Failed to create or execute parallel subagents: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg, None


def _aggregate_results(results: list[Any]) -> str:
    """
    Aggregate results from multiple subagents into a summary.

    Args:
        results: List of SubAgentResult objects

    Returns:
        Summary string
    """
    from rich.markup import escape

    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]

    summary_parts = []

    # Summary statistics
    total_time = sum(r.execution_time for r in results)
    total_iterations = sum(r.iterations_used for r in results)

    summary_parts.append("📊 Execution Summary:")
    summary_parts.append(f"   • Total subagents: {len(results)}")
    summary_parts.append(f"   • Successful: {len(successful_results)}")
    summary_parts.append(f"   • Failed: {len(failed_results)}")
    summary_parts.append(f"   • Total execution time: {total_time:.2f}s")
    summary_parts.append(f"   • Total iterations: {total_iterations}")

    # Successful results summary
    if successful_results:
        summary_parts.append("\n✅ Successful Subagents:")
        for i, result in enumerate(successful_results, 1):
            # Escape Rich markup to prevent tag conflicts
            safe_output = escape(result.output[:100])
            summary_parts.append(
                f"   {i}. {safe_output}{'...' if len(result.output) > 100 else ''}"
            )

    # Failed results summary
    if failed_results:
        summary_parts.append("\n❌ Failed Subagents:")
        for i, result in enumerate(failed_results, 1):
            error_info = result.error or "Unknown error"
            # Escape Rich markup to prevent tag conflicts
            safe_error = escape(error_info[:100])
            summary_parts.append(f"   {i}. {safe_error}{'...' if len(error_info) > 100 else ''}")

    return "\n".join(summary_parts)
