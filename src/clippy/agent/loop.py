"""Agent execution loop - the core iteration logic."""

import json
import logging
import sys
from collections.abc import Callable
from typing import Any

from rich.markup import escape
from rich.panel import Panel

from ..executor import ActionExecutor
from ..permissions import PermissionManager
from ..providers import LLMProvider, Spinner
from ..tools import catalog as tool_catalog
from .conversation import check_and_auto_compact
from .errors import format_api_error
from .tool_handler import handle_tool_use

logger = logging.getLogger(__name__)


def run_agent_loop(
    conversation_history: list[dict[str, Any]],
    provider: LLMProvider,
    model: str,
    permission_manager: PermissionManager,
    executor: ActionExecutor,
    console: Any,  # Console or SubAgentConsoleWrapper
    auto_approve_all: bool,
    approval_callback: Callable[[str, dict[str, Any], str | None], bool] | None,
    check_interrupted: Callable[[], bool],
    mcp_manager: Any = None,
    max_iterations: int = 100,
    allowed_tools: list[str] | None = None,
    parent_agent: Any = None,
) -> str:
    """
    Run the main agent loop.

    Args:
        conversation_history: Current conversation history (modified in place)
        provider: LLM provider instance
        model: Model identifier to use
        permission_manager: Permission manager instance
        executor: Action executor instance
        console: Rich console for output
        auto_approve_all: If True, auto-approve all actions
        approval_callback: Optional callback for approval requests
        check_interrupted: Callback to check if execution was interrupted
        mcp_manager: Optional MCP manager instance
        max_iterations: Maximum number of iterations (default: 100)
        allowed_tools: List of allowed tool names (default: all tools)
        parent_agent: Parent agent instance for subagent delegation

    Returns:
        Final response from the agent

    Raises:
        InterruptedExceptionError: If execution is interrupted
    """
    from .core import InterruptedExceptionError

    # Use the provided max_iterations parameter instead of hardcoding
    logger.info(f"Starting agent loop with model: {model}, max_iterations: {max_iterations}")

    # Track spinner between iterations
    spinner: Spinner | None = None

    for iteration in range(max_iterations):
        # Stop spinner from previous iteration
        if spinner:
            spinner.stop()
            spinner = None

        logger.debug(f"Agent loop iteration {iteration + 1}/{max_iterations}")

        if check_interrupted():
            logger.info("Agent loop interrupted by user")
            raise InterruptedExceptionError()

        # Check for auto-compaction based on model threshold
        compacted, compact_message, compact_stats = check_and_auto_compact(
            conversation_history, model, provider, getattr(provider, "base_url", None)
        )
        if compacted:
            logger.info(f"Auto-compaction triggered: {compact_message}")
            console.print(f"[cyan]Auto-compacted conversation: {compact_message}[/cyan]")

        # Get current tools (built-in + MCP)
        tools = tool_catalog.get_all_tools(mcp_manager)

        # Filter tools if allowed_tools is specified
        if allowed_tools is not None:
            filtered_tools = []
            for tool in tools:
                tool_name = tool["function"]["name"]
                if tool_name in allowed_tools:
                    filtered_tools.append(tool)
            tools = filtered_tools

        logger.debug(f"Loaded {len(tools)} tools for iteration {iteration + 1}")

        # Call provider (returns OpenAI message dict)
        try:
            response = provider.create_message(
                messages=conversation_history,
                tools=tools,
                model=model,
            )
        except Exception as e:
            # Handle API errors gracefully
            error_message = format_api_error(e)
            console.print(
                Panel(
                    f"[bold red]API Error:[/bold red]\n\n{error_message}",
                    title="[bold red]Error[/bold red]",
                    border_style="red",
                )
            )
            logger.error(f"API error in agent loop: {type(e).__name__}: {e}", exc_info=True)
            raise

        # Build assistant message for history
        assistant_message: dict[str, Any] = {
            "role": "assistant",
        }

        # Add content if present
        if response.get("content"):
            assistant_message["content"] = response["content"]

        # Add tool calls if present
        if response.get("tool_calls"):
            assistant_message["tool_calls"] = response["tool_calls"]

        # Add to conversation history
        conversation_history.append(assistant_message)

        # Save conversation automatically after each assistant message
        if parent_agent is not None:
            success, message = parent_agent.save_conversation()
            if not success:
                logger.warning(f"Failed to auto-save conversation: {message}")

        # Handle tool calls
        has_tool_calls = False
        if response.get("tool_calls"):
            has_tool_calls = True
            num_tool_calls = len(response["tool_calls"])
            logger.info(f"Processing {num_tool_calls} tool call(s) in iteration {iteration + 1}")

            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                logger.debug(f"Processing tool call: {tool_name}")

                # Parse tool arguments (JSON string -> dict)
                try:
                    tool_input = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool arguments for {tool_name}: {e}")
                    console.print(
                        f"[bold red]Error parsing tool arguments: {escape(str(e))}[/bold red]"
                    )
                    from .tool_handler import add_tool_result

                    add_tool_result(
                        conversation_history,
                        tool_call["id"],
                        False,
                        f"Error parsing tool arguments: {e}",
                        None,
                    )
                    continue

                success = handle_tool_use(
                    tool_name,
                    tool_input,
                    tool_call["id"],
                    auto_approve_all,
                    permission_manager,
                    executor,
                    console,
                    conversation_history,
                    approval_callback,
                    mcp_manager,
                    parent_agent,
                )
                if not success:
                    logger.warning(f"Tool execution failed or denied: {tool_name}")
                    # Tool execution failed or was denied
                    continue
                else:
                    logger.info(f"Tool executed successfully: {tool_name}")

        # If no tool calls, we're done
        # (content was already streamed by the provider)
        if not has_tool_calls:
            logger.info(f"Agent loop completed successfully after {iteration + 1} iteration(s)")
            content = response.get("content", "")
            return content if isinstance(content, str) else ""

        # Check finish reason
        # (content was already streamed by the provider)
        if response.get("finish_reason") == "stop":
            logger.info(
                f"Agent loop stopped (finish_reason=stop) after {iteration + 1} iteration(s)"
            )
            content = response.get("content", "")
            return content if isinstance(content, str) else ""

        # Start spinner for next iteration (since we're continuing the loop)
        spinner = Spinner("Thinking", enabled=sys.stdout.isatty())
        spinner.start()

    # Max iterations reached - cleanup and display warning
    if spinner:
        spinner.stop()
        spinner = None

    logger.warning(f"Maximum iterations ({max_iterations}) reached")
    console.print(
        Panel(
            "[bold yellow]⚠ Maximum Iterations Reached[/bold yellow]\n\n"
            "The agent has reached the maximum number of iterations (100) and has stopped.\n"
            "The task may be incomplete.\n\n"
            "[dim]This limit prevents infinite loops. You can:\n"
            '• Say "continue" to continue with the current request\n'
            "• Break down the task into smaller steps\n"
            "• Make a new request\n"
            "• Use /reset to start fresh[/dim]",
            title="[bold yellow]Iteration Limit[/bold yellow]",
            border_style="yellow",
        )
    )
    return "Maximum iterations reached. Task may be incomplete."
