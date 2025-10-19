"""Agent execution loop - the core iteration logic."""

import json
import logging
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from ..executor import ActionExecutor
from ..permissions import PermissionManager
from ..providers import LLMProvider
from ..tools import catalog as tool_catalog
from .errors import format_api_error
from .tool_handler import handle_tool_use

logger = logging.getLogger(__name__)


def run_agent_loop(
    conversation_history: list[dict[str, Any]],
    provider: LLMProvider,
    model: str,
    permission_manager: PermissionManager,
    executor: ActionExecutor,
    console: Console,
    auto_approve_all: bool,
    approval_callback: Callable[[str, dict[str, Any], str | None], bool] | None,
    check_interrupted: Callable[[], bool],
    mcp_manager: Any = None,
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

    Returns:
        Final response from the agent

    Raises:
        InterruptedExceptionError: If execution is interrupted
    """
    from .core import InterruptedExceptionError

    max_iterations = 50  # Prevent infinite loops

    for iteration in range(max_iterations):
        if check_interrupted():
            raise InterruptedExceptionError()

        # Get current tools (built-in + MCP)
        tools = tool_catalog.get_all_tools(mcp_manager)

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

        # Handle tool calls
        has_tool_calls = False
        if response.get("tool_calls"):
            has_tool_calls = True
            for tool_call in response["tool_calls"]:
                # Parse tool arguments (JSON string -> dict)
                try:
                    tool_input = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    console.print(f"[bold red]Error parsing tool arguments: {escape(str(e))}[/bold red]")
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
                    tool_call["function"]["name"],
                    tool_input,
                    tool_call["id"],
                    auto_approve_all,
                    permission_manager,
                    executor,
                    console,
                    conversation_history,
                    approval_callback,
                    mcp_manager,
                )
                if not success:
                    # Tool execution failed or was denied
                    continue

        # If no tool calls, we're done
        # (content was already streamed by the provider)
        if not has_tool_calls:
            content = response.get("content", "")
            return content if isinstance(content, str) else ""

        # Check finish reason
        # (content was already streamed by the provider)
        if response.get("finish_reason") == "stop":
            content = response.get("content", "")
            return content if isinstance(content, str) else ""

    # Max iterations reached - display warning
    console.print(
        Panel(
            "[bold yellow]⚠ Maximum Iterations Reached[/bold yellow]\n\n"
            "The agent has reached the maximum number of iterations (50) and has stopped.\n"
            "The task may be incomplete.\n\n"
            "[dim]This limit prevents infinite loops. You can:\n"
            "• Continue with a new request\n"
            "• Break down the task into smaller steps\n"
            "• Use /reset to start fresh[/dim]",
            title="[bold yellow]Iteration Limit[/bold yellow]",
            border_style="yellow",
        )
    )
    return "Maximum iterations reached. Task may be incomplete."
