"""Agent execution loop - the core iteration logic."""

import json
import logging
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rich.markup import escape
from rich.panel import Panel

from ..executor import ActionExecutor
from ..permissions import PermissionManager
from ..providers import LLMProvider, Spinner
from ..tools import catalog as tool_catalog
from .conversation import check_and_auto_compact
from .errors import format_api_error
from .exceptions import InterruptedExceptionError
from .protocols import AgentProtocol, ConsoleProtocol
from .tool_handler import handle_tool_use

if TYPE_CHECKING:
    from ..mcp.manager import Manager

logger = logging.getLogger(__name__)


# Loop constants
DEFAULT_MAX_ITERATIONS = 100


@dataclass
class AgentLoopConfig:
    """Configuration for running an agent loop.

    Consolidates all parameters for run_agent_loop into a single configuration
    object for better API clarity and maintainability.
    """

    provider: LLMProvider
    model: str
    permission_manager: PermissionManager
    executor: ActionExecutor
    console: ConsoleProtocol
    auto_approve_all: bool = False
    approval_callback: Callable[[str, dict[str, Any], str | None], bool] | None = None
    check_interrupted: Callable[[], bool] | None = None
    mcp_manager: "Manager | None" = None
    allowed_tools: list[str] | None = None
    parent_agent: AgentProtocol | None = None
    max_iterations: int | None = DEFAULT_MAX_ITERATIONS
    max_duration: float | None = None


def run_agent_loop(
    conversation_history: list[dict[str, Any]],
    config: AgentLoopConfig,
) -> str:
    """
    Run the main agent loop.

    Args:
        conversation_history: Current conversation history (modified in place)
        config: AgentLoopConfig containing all configuration parameters

    Returns:
        Final response from the agent

    Raises:
        InterruptedExceptionError: If execution is interrupted
    """
    logger.info(f"Starting agent loop with model: {config.model}")

    # Track spinner between iterations
    spinner: Spinner | None = None
    loop_start = time.time()

    iteration = 0
    while True:
        # Stop spinner from previous iteration
        if spinner:
            spinner.stop()
            spinner = None

        if config.check_interrupted and config.check_interrupted():
            logger.info("Agent loop interrupted by user")
            raise InterruptedExceptionError()

        # Guardrails: duration/iteration caps
        elapsed = time.time() - loop_start
        if config.max_duration is not None and elapsed >= config.max_duration:
            logger.warning(
                f"Agent loop stopped due to max_duration: {elapsed:.2f}s "
                f"(limit {config.max_duration}s)"
            )
            return _emit_guardrail_summary(
                conversation_history=conversation_history,
                reason=f"Reached max duration of {config.max_duration}s",
                iterations=iteration,
                elapsed=elapsed,
            )

        if config.max_iterations is not None and iteration >= config.max_iterations:
            logger.warning(
                f"Agent loop stopped due to max_iterations: {iteration} "
                f"(limit {config.max_iterations})"
            )
            return _emit_guardrail_summary(
                conversation_history=conversation_history,
                reason=f"Reached max iterations of {config.max_iterations}",
                iterations=iteration,
                elapsed=elapsed,
            )

        iteration += 1
        logger.debug(f"Agent loop iteration {iteration}")

        # Check for auto-compaction based on model threshold
        compacted, compact_message, compact_stats, new_history = check_and_auto_compact(
            conversation_history,
            config.model,
            config.provider,
            getattr(config.provider, "base_url", None),
        )
        if compacted and new_history:
            # Update conversation history in place with compacted version
            conversation_history.clear()
            conversation_history.extend(new_history)
            logger.info(f"Auto-compaction triggered: {compact_message}")
            _display_auto_compaction_notification(config.console, compact_stats)

        # Get current tools (built-in + MCP)
        tools = tool_catalog.get_all_tools(config.mcp_manager)

        # Filter tools if allowed_tools is specified
        if config.allowed_tools is not None:
            filtered_tools = []
            for tool in tools:
                tool_name = tool["function"]["name"]
                if tool_name in config.allowed_tools:
                    filtered_tools.append(tool)
            tools = filtered_tools

        logger.debug(f"Loaded {len(tools)} tools for iteration {iteration}")

        # Call provider using streaming
        try:
            # Stop any existing spinner before streaming starts
            if spinner:
                spinner.stop()
                spinner = None

            response = _process_streaming_response(
                config.provider, conversation_history, tools, config.model, config.console
            )

            # Track token usage from this API call
            if response.get("usage"):
                from .token_tracker import get_session_tracker

                tracker = get_session_tracker()

                # Determine if this is a subagent or main agent call
                is_subagent = (
                    hasattr(config, "parent_agent")
                    and config.parent_agent is not None
                    and hasattr(config.console, "_subagent_name")
                )

                if is_subagent:
                    subagent_name = getattr(config.console, "_subagent_name", "unknown")
                    tracker.track_subagent_usage(response["usage"], subagent_name, config.model)
                else:
                    tracker.track_main_agent_usage(response["usage"], config.model)

        except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
            # Handle API errors gracefully
            error_message = format_api_error(e)
            config.console.print(
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

        # Preserve reasoning_content for reasoner models
        if response.get("reasoning_content"):
            assistant_message["reasoning_content"] = response["reasoning_content"]

        # Add to conversation history
        conversation_history.append(assistant_message)

        # Note: Response content is already displayed during streaming

        # Save conversation automatically after each assistant message
        if config.parent_agent is not None:
            success, message = config.parent_agent.save_conversation()
            if not success:
                logger.warning(f"Failed to auto-save conversation: {message}")

        # Handle tool calls
        has_tool_calls = False
        if response.get("tool_calls"):
            has_tool_calls = True
            num_tool_calls = len(response["tool_calls"])
            logger.info(f"Processing {num_tool_calls} tool call(s) in iteration {iteration}")

            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                logger.debug(f"Processing tool call: {tool_name}")

                # Parse tool arguments (JSON string -> dict)
                try:
                    tool_input = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool arguments for {tool_name}: {e}")
                    config.console.print(
                        f"[bold red]Error parsing tool arguments: {escape(str(e))}[/bold red]"
                    )
                    from .tool_handler import add_tool_result

                    add_tool_result(
                        conversation_history,
                        tool_call["id"],
                        False,
                        f"Error parsing tool arguments: {e}",
                        None,
                        tool_name=tool_name,
                    )
                    continue

                success = handle_tool_use(
                    tool_name,
                    tool_input,
                    tool_call["id"],
                    config.auto_approve_all,
                    config.permission_manager,
                    config.executor,
                    config.console,
                    conversation_history,
                    config.approval_callback,
                    config.mcp_manager,
                    config.parent_agent,
                )
                if not success:
                    logger.warning(f"Tool execution failed or denied: {tool_name}")
                    # Tool execution failed or was denied
                    continue
                else:
                    logger.info(f"Tool executed successfully: {tool_name}")

        # If no tool calls, we're done
        if not has_tool_calls:
            logger.info(f"Agent loop completed successfully after {iteration} iteration(s)")
            content = response.get("content", "")
            return content if isinstance(content, str) else ""

        # Check finish reason
        if response.get("finish_reason") == "stop":
            logger.info(f"Agent loop stopped (finish_reason=stop) after {iteration} iteration(s)")
            content = response.get("content", "")
            return content if isinstance(content, str) else ""

        # Start spinner for next iteration (since we're continuing the loop)
        spinner = Spinner("Thinking", enabled=sys.stdout.isatty())
        spinner.start()

    # Note: No maximum iterations limit - loop runs until agent completes or is interrupted


def _process_streaming_response(
    provider: LLMProvider,
    conversation_history: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    model: str,
    console: ConsoleProtocol,
) -> dict[str, Any]:
    """
    Process streaming response from provider and display in real-time.

    Args:
        provider: LLM provider instance
        conversation_history: Current conversation history
        tools: List of available tools
        model: Model identifier
        console: Console for output

    Returns:
        Final consolidated response
    """
    # Start with an empty header for the response
    console.print("\n[bold blue][📎][/bold blue] ", end="")

    # Track accumulated content and tool calls
    accumulated_content = ""
    accumulated_tool_calls: list[dict[str, Any]] = []

    for chunk in provider.stream_message(conversation_history, tools, model):
        # Handle streaming content deltas
        if chunk.get("delta") and chunk.get("content"):
            # Print the chunk directly for real-time display
            # Strip only leading newlines to prevent content appearing on wrong line
            # but preserve other whitespace like spaces between words
            display_content = chunk["content"].lstrip("\n\r")
            console.print(escape(display_content), end="")
            accumulated_content += chunk["content"]
        elif chunk.get("content") and not chunk.get("delta"):
            # Final full content (for non-streaming models like codex)
            # Only print if we haven't already been streaming content
            if not accumulated_content:
                # Strip only leading newlines to prevent content appearing on wrong line
                # but preserve other whitespace like spaces between words
                display_content = chunk["content"].lstrip("\n\r")
                console.print(escape(display_content), end="")
            accumulated_content = chunk["content"]
        elif not chunk.get("delta"):
            # Final chunk with complete response
            if chunk.get("content"):
                accumulated_content = chunk["content"]
                if not accumulated_content.strip() and accumulated_tool_calls:
                    # Only tool calls, no content - print newline
                    console.print()

            # Return the final consolidated response
            return {
                "role": "assistant",
                "content": accumulated_content if accumulated_content else None,
                "tool_calls": accumulated_tool_calls if accumulated_tool_calls else None,
                "finish_reason": chunk.get("finish_reason"),
            }

    # If we get here, return what we accumulated
    return {
        "role": "assistant",
        "content": accumulated_content if accumulated_content else None,
        "tool_calls": accumulated_tool_calls if accumulated_tool_calls else None,
        "finish_reason": "stop",
    }


def _display_auto_compaction_notification(console: ConsoleProtocol, stats: dict[str, Any]) -> None:
    """
    Display a subtle but informative auto-compaction notification.

    Shows before/after token counts and message reductions in a compact format
    that's visible but doesn't interrupt the conversation flow.

    Args:
        console: Rich console for output
        stats: Compaction statistics from check_and_auto_compact
    """
    if not stats:
        return

    before_tokens = stats.get("before_tokens", 0)
    after_tokens = stats.get("after_tokens", 0)
    reduction_percent = stats.get("reduction_percent", 0)
    messages_before = stats.get("messages_before", 0)
    messages_after = stats.get("messages_after", 0)
    messages_summarized = stats.get("messages_summarized", 0)

    # Format the numbers with commas for readability
    before_str = f"{before_tokens:,}"
    after_str = f"{after_tokens:,}"

    # Create a subtle, one-line notification with key information
    console.print(
        f"[dim]🔄 auto-compacted:[/dim] "
        f"[cyan]{before_str}[/cyan]→[cyan]{after_str}[/cyan] tokens "
        f"([green]{reduction_percent:.1f}%[/green] saved) • "
        f"[dim]{messages_before}→{messages_after}[/dim] messages "
        f"([dim]{messages_summarized}[/dim] summarized)"
    )


def _emit_guardrail_summary(
    conversation_history: list[dict[str, Any]],
    reason: str,
    iterations: int,
    elapsed: float,
) -> str:
    """
    Append and return a structured summary when a guardrail stops the loop.

    Args:
        conversation_history: Current conversation history
        reason: Human-readable stop reason
        iterations: Iterations completed
        elapsed: Seconds elapsed

    Returns:
        Summary content that was appended
    """

    def _last_tool_snapshot() -> str:
        last_tool = next(
            (msg for msg in reversed(conversation_history) if msg.get("role") == "tool"), None
        )
        if last_tool:
            tool_name = last_tool.get("name") or "unknown"
            first_line = str(last_tool.get("content", "")).splitlines()[0] if last_tool else ""
            return f"{tool_name}: {first_line}".strip()

        last_call_name = None
        last_call_args = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_call = msg["tool_calls"][-1]
                last_call_name = tool_call.get("function", {}).get("name")
                last_call_args = tool_call.get("function", {}).get("arguments")
                break

        if last_call_name:
            return f"{last_call_name} (pending args: {last_call_args})"
        return "none recorded"

    last_user = next(
        (msg for msg in reversed(conversation_history) if msg.get("role") == "user"), {}
    ).get("content", "")
    last_assistant = next(
        (
            msg
            for msg in reversed(conversation_history)
            if msg.get("role") == "assistant" and msg.get("content")
        ),
        {},
    ).get("content", "")

    summary = (
        f"⏱️ Stopped: {reason}. "
        f"Iterations run: {iterations}, elapsed: {elapsed:.2f}s.\n"
        f"Last tool: {_last_tool_snapshot()}\n"
        f"Last assistant content: {last_assistant or 'n/a'}\n"
        f"Last user request: {last_user}\n"
        "Suggested next step: resume with a higher cap or continue from the last tool result."
    )

    conversation_history.append({"role": "assistant", "content": summary})
    return summary
