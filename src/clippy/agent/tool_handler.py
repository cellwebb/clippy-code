"""Tool handling utilities for the agent system."""

import logging
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.markup import escape

from ..diff_utils import format_diff_for_display
from ..executor import ActionExecutor
from ..mcp.naming import is_mcp_tool, parse_mcp_qualified_name
from ..permissions import ActionType, PermissionLevel, PermissionManager
from .utils import generate_preview_diff

logger = logging.getLogger(__name__)

# Import InterruptedExceptionError from agent to avoid circular import
# Will be imported at runtime when needed


def format_mcp_result(result: Any) -> str:
    """
    Format an MCP CallToolResult into a clean string.

    Args:
        result: MCP CallToolResult object

    Returns:
        Formatted string containing the actual content
    """
    try:
        from mcp import types

        if isinstance(result, types.CallToolResult):
            # Extract text content from the result
            content_parts = []
            for content_item in result.content:
                if isinstance(content_item, types.TextContent):
                    content_parts.append(content_item.text)
                elif isinstance(content_item, types.ImageContent):
                    content_parts.append(f"[Image: {content_item.mimeType}]")
                elif isinstance(content_item, types.EmbeddedResource):
                    # Handle embedded resources
                    if hasattr(content_item.resource, "text"):
                        content_parts.append(content_item.resource.text)
                    else:
                        content_parts.append(f"[Resource: {content_item.resource.uri}]")
                else:
                    # Fallback for unknown content types
                    content_parts.append(str(content_item))

            return "\n".join(content_parts) if content_parts else str(result)
        else:
            # Not an MCP result, return as-is
            return str(result)
    except ImportError:
        # MCP not available, fallback to string
        return str(result)
    except Exception as e:
        # Error formatting, fallback to string
        return f"[Error formatting MCP result: {e}]\n{str(result)}"


def display_tool_request(
    console: Console, tool_name: str, tool_input: dict[str, Any], diff_content: str | None = None
) -> None:
    """
    Display what tool the agent wants to use.

    Args:
        console: Rich console instance for output
        tool_name: Name of the tool being requested
        tool_input: Input parameters for the tool
        diff_content: Optional diff content to display for file operations
    """
    # Special handling for MCP tools
    if is_mcp_tool(tool_name):
        try:
            server_id, tool = parse_mcp_qualified_name(tool_name)
            console.print(
                f"\n[bold cyan]→ MCP Tool: {tool}[/bold cyan] [dim](from {server_id})[/dim]"
            )
        except ValueError:
            console.print(f"\n[bold cyan]→ MCP Tool: {tool_name}[/bold cyan]")
    else:
        console.print(f"\n[bold cyan]→ {tool_name}[/bold cyan]")

    input_str = "\n".join(f"  {k}: {escape(str(v))}" for k, v in tool_input.items())
    if input_str:
        console.print(f"[cyan]{input_str}[/cyan]")

    # Enhanced diff display for MCP tools that affect files
    if diff_content is not None:
        if diff_content == "":
            if is_mcp_tool(tool_name):
                console.print("[yellow]No file changes (content identical)[/yellow]")
            else:
                console.print("[yellow]No changes (content identical)[/yellow]")
        else:
            if is_mcp_tool(tool_name):
                console.print("[bold yellow]MCP Tool File Changes:[/bold yellow]")
            else:
                console.print("[bold yellow]Preview of changes:[/bold yellow]")

            formatted_diff, _truncated = format_diff_for_display(diff_content, max_lines=100)
            if _truncated:
                console.print(f"[yellow]{escape(formatted_diff)}[/yellow]")
                console.print("[dim][... additional lines truncated][/dim]")
            else:
                console.print(f"[yellow]{escape(formatted_diff)}[/yellow]")


def handle_tool_use(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_id: str,
    auto_approve_all: bool,
    permission_manager: PermissionManager,
    executor: ActionExecutor,
    console: Console,
    conversation_history: list[dict[str, Any]],
    approval_callback: Callable[[str, dict[str, Any], str | None], bool] | None = None,
    mcp_manager: Any = None,
    parent_agent: Any = None,
) -> bool:
    """
    Handle a tool use request.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        tool_use_id: Unique ID for this tool use
        auto_approve_all: If True, auto-approve all actions
        permission_manager: Permission manager instance
        executor: Action executor instance
        console: Rich console instance
        conversation_history: Current conversation history (modified in place)
        approval_callback: Optional callback for approval (used in document mode)
        mcp_manager: Optional MCP manager for trusting MCP servers

    Returns:
        True if the tool was executed successfully, False otherwise
    """
    # Check for YOLO mode (override everything)
    yolo_mode = False
    if parent_agent is not None and hasattr(parent_agent, "yolo_mode"):
        yolo_mode = parent_agent.yolo_mode

    # In YOLO mode, everything is auto-approved
    if yolo_mode:
        auto_approve_all = True

    # Map tool names to action types
    action_map = {
        "read_file": ActionType.READ_FILE,
        "write_file": ActionType.WRITE_FILE,
        "delete_file": ActionType.DELETE_FILE,
        "list_directory": ActionType.LIST_DIR,
        "create_directory": ActionType.CREATE_DIR,
        "execute_command": ActionType.EXECUTE_COMMAND,
        "search_files": ActionType.SEARCH_FILES,
        "get_file_info": ActionType.GET_FILE_INFO,
        "read_files": ActionType.READ_FILE,  # Uses the same permission as read_file
        "grep": ActionType.GREP,  # Dedicated action type for grep
        "edit_file": ActionType.EDIT_FILE,  # Add mapping for edit_file tool
        "find_replace": ActionType.FIND_REPLACE,
        "delegate_to_subagent": ActionType.DELEGATE_TO_SUBAGENT,
        "run_parallel_subagents": ActionType.RUN_PARALLEL_SUBAGENTS,
    }

    # Handle MCP tools with special action types
    action_type: ActionType
    if is_mcp_tool(tool_name):
        try:
            server_id, tool = parse_mcp_qualified_name(tool_name)
            # MCP tools don't have a built-in list_tools function, so all MCP tool calls
            # use the MCP_TOOL_CALL action type
            action_type = ActionType.MCP_TOOL_CALL
        except ValueError:
            action_type = ActionType.MCP_TOOL_CALL
    else:
        action_type = action_map.get(tool_name, ActionType.READ_FILE)  # Default fallback

    if action_type is None:
        add_tool_result(
            conversation_history, tool_use_id, False, f"Unknown tool: {tool_name}", None
        )
        return False

    # Check if we need approval
    needs_approval = not auto_approve_all and not permission_manager.config.can_auto_execute(
        action_type
    )
    logger.debug(f"Tool: {tool_name}, Action: {action_type}, Needs approval: {needs_approval}")

    # For MCP tools, also check if the server is trusted
    if is_mcp_tool(tool_name) and mcp_manager and needs_approval:
        try:
            server_id, _ = parse_mcp_qualified_name(tool_name)
            if mcp_manager.is_trusted(server_id):
                logger.debug(f"MCP server '{server_id}' is trusted, bypassing approval")
                needs_approval = False
        except ValueError:
            pass

    # Generate diff preview for file operations
    diff_content = generate_preview_diff(tool_name, tool_input)

    # Show what the agent wants to do
    # (Skip if using approval callback - it will display as part of the approval prompt)
    if not (needs_approval and approval_callback):
        display_tool_request(console, tool_name, tool_input, diff_content)

    if permission_manager.config.is_denied(action_type):
        logger.warning(f"Action denied by policy: {tool_name} ({action_type})")
        console.print("[bold red]✗ Action denied by policy[/bold red]")
        add_tool_result(conversation_history, tool_use_id, False, "Action denied by policy", None)
        return False

    # Track whether user explicitly approved (to bypass trust check for MCP tools)
    user_approved = False

    if needs_approval:
        logger.debug(f"Requesting approval for: {tool_name}")
        approved = ask_approval(
            tool_name,
            tool_input,
            diff_content,
            action_type,
            permission_manager,
            console,
            approval_callback,
            mcp_manager,
        )
        if not approved:
            logger.info(f"User rejected tool execution: {tool_name}")
            console.print("[bold yellow]⊘ Action rejected by user[/bold yellow]")
            add_tool_result(
                conversation_history, tool_use_id, False, "Action rejected by user", None
            )
            return False
        logger.info(f"User approved tool execution: {tool_name}")
        user_approved = True

    # Execute the tool
    # For MCP tools, bypass trust check if user explicitly approved
    bypass_trust = user_approved and is_mcp_tool(tool_name)
    logger.debug(f"Executing tool: {tool_name}, bypass_trust: {bypass_trust}")
    # Special handling for delegate_to_subagent
    if tool_name == "delegate_to_subagent":
        if parent_agent is None:
            success, message, result = (
                False,
                "delegate_to_subagent requires parent agent context",
                None,
            )
        else:
            # Import here to avoid circular imports
            from ..tools.delegate_to_subagent import create_subagent_and_execute

            logger.debug("Handling delegate_to_subagent tool")
            success, message, result = create_subagent_and_execute(
                parent_agent=parent_agent, permission_manager=permission_manager, **tool_input
            )
    # Special handling for run_parallel_subagents
    elif tool_name == "run_parallel_subagents":
        if parent_agent is None:
            success, message, result = (
                False,
                "run_parallel_subagents requires parent agent context",
                None,
            )
        else:
            # Import here to avoid circular imports
            from ..tools.run_parallel_subagents import create_parallel_subagents_and_execute

            logger.debug("Handling run_parallel_subagents tool")
            success, message, result = create_parallel_subagents_and_execute(
                parent_agent=parent_agent, permission_manager=permission_manager, **tool_input
            )
    else:
        # Execute the tool
        success, message, result = executor.execute(tool_name, tool_input, bypass_trust)
    logger.debug(f"Tool execution result: success={success}, message={message}")

    # Enhanced error handling for MCP tools
    if not success and is_mcp_tool(tool_name):
        try:
            server_id, tool = parse_mcp_qualified_name(tool_name)

            # Provide enhanced error context for MCP tools
            if "not trusted" in message.lower():
                console.print(f"[bold red]✗ MCP server '{server_id}' is not trusted[/bold red]")
                console.print(
                    f"[dim]Use '/mcp allow {server_id}' to trust this server for this session[/dim]"
                )
            elif "not connected" in message.lower():
                console.print(f"[bold red]✗ Not connected to MCP server '{server_id}'[/bold red]")
                console.print("[dim]Try '/mcp refresh' to reconnect to MCP servers[/dim]")
            elif "not configured" in message.lower():
                console.print(f"[bold red]✗ MCP server '{server_id}' not configured[/bold red]")
                console.print("[dim]Check your mcp.json configuration file[/dim]")
            else:
                console.print(
                    f"[bold red]✗ MCP Tool Error ({server_id}): {escape(message)}[/bold red]"
                )
                console.print(f"[dim]Tool: {tool}[/dim]")

                # Provide specific suggestions based on error patterns
                if "timeout" in message.lower():
                    console.print(
                        "[dim]Suggestion: The operation timed out - try again or check "
                        "server status[/dim]"
                    )
                elif "permission" in message.lower():
                    console.print(
                        "[dim]Suggestion: Check file permissions or server access rights[/dim]"
                    )

        except ValueError:
            console.print(f"[bold red]✗ MCP Tool Error: {escape(message)}[/bold red]")
    else:
        # Standard success/error display for non-MCP tools
        if success:
            console.print(f"[bold green]✓ {escape(message)}[/bold green]")
        else:
            console.print(f"[bold red]✗ {escape(message)}[/bold red]")

    # Add result to conversation
    add_tool_result(conversation_history, tool_use_id, success, message, result)

    # Save conversation automatically after each tool execution
    if parent_agent is not None:
        save_success, save_message = parent_agent.save_conversation()
        if not save_success:
            logger.warning(f"Failed to auto-save conversation after tool execution: {save_message}")

    # Add blank line after tool result for visual separation
    console.print("")

    return success


def ask_approval(
    tool_name: str,
    tool_input: dict[str, Any],
    diff_content: str | None,
    action_type: ActionType | None,
    permission_manager: PermissionManager,
    console: Console,
    approval_callback: Callable[[str, dict[str, Any], str | None], bool] | None = None,
    mcp_manager: Any = None,
) -> bool:
    """
    Ask user for approval to execute an action.

    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters
        diff_content: Optional diff content for file operations
        action_type: Type of action being requested
        permission_manager: Permission manager instance
        console: Rich console instance
        approval_callback: Optional callback for approval (used in document mode)
        mcp_manager: Optional MCP manager for trusting MCP servers

    Returns:
        True if approved, False otherwise

    Raises:
        InterruptedExceptionError: If user interrupts execution
    """
    # Import here to avoid circular dependency
    from .core import InterruptedExceptionError

    # Use callback if provided (for document mode)
    if approval_callback:
        try:
            result = approval_callback(tool_name, tool_input, diff_content)
            return bool(result)  # Ensure we return a bool
        except InterruptedExceptionError:
            raise

    # Default behavior: use input() (for interactive mode)

    while True:
        try:
            response = input("\n[?] Approve this action? [(y)es/(n)o/(a)llow]: ").strip().lower()

            if response == "":
                # Empty input - reprompt
                continue
            elif response in ("no", "n"):
                # "no" or "n" interrupts execution
                logger.info(f"User rejected approval for: {tool_name}")
                raise InterruptedExceptionError()
            elif response == "allow" or response == "a":
                logger.info(f"User chose 'allow' for: {tool_name}")
                # Check if this is an MCP tool
                if is_mcp_tool(tool_name):
                    # Trust the MCP server
                    try:
                        server_id, _ = parse_mcp_qualified_name(tool_name)
                        if mcp_manager:
                            mcp_manager.set_trusted(server_id, True)
                            console.print(
                                f"[green]✓ Trusted MCP server '{server_id}' for this "
                                f"session[/green]"
                            )
                            console.print(
                                f"[green]All tools from '{server_id}' will be auto-approved[/green]"
                            )
                        else:
                            console.print("[yellow]⚠ MCP manager not available[/yellow]")
                    except Exception as e:
                        console.print(f"[yellow]⚠ Error trusting server: {escape(str(e))}[/yellow]")
                    return True
                else:
                    # Auto-approve this action type for non-MCP tools
                    if action_type:
                        permission_manager.update_permission(
                            action_type, PermissionLevel.AUTO_APPROVE
                        )
                        logger.info(f"Auto-approved action type: {action_type}")
                        console.print(f"[green]Auto-approving {tool_name} for this session[/green]")
                    return True
            elif response in ("yes", "y"):
                logger.debug(f"User approved (yes): {tool_name}")
                return True
            else:
                console.print(
                    "[yellow]Invalid response. Please enter (y)es, (n)o, or (a)llow.[/yellow]"
                )
                continue
        except (KeyboardInterrupt, EOFError):
            raise InterruptedExceptionError()


def add_tool_result(
    conversation_history: list[dict[str, Any]],
    tool_use_id: str,
    success: bool,
    message: str,
    result: Any,
) -> None:
    """
    Add a tool result to the conversation history.

    Args:
        conversation_history: Current conversation history (modified in place)
        tool_use_id: Unique ID for this tool use
        success: Whether the tool execution succeeded
        message: Result message
        result: Optional result data
    """
    content = message
    if result:
        # Format MCP results properly to extract actual content
        formatted_result = format_mcp_result(result)
        content += f"\n\n{formatted_result}"

    # Add error prefix if failed (OpenAI doesn't have is_error flag)
    if not success:
        content = f"ERROR: {content}"

    # Add tool result message (OpenAI format)
    conversation_history.append(
        {
            "role": "tool",
            "tool_call_id": tool_use_id,
            "content": content,
        }
    )
