"""Tool handling utilities for the agent system."""

from collections.abc import Callable
from typing import Any

from rich.console import Console

from ..diff_utils import format_diff_for_display
from ..executor import ActionExecutor
from ..mcp.naming import is_mcp_tool, parse_mcp_qualified_name
from ..permissions import ActionType, PermissionLevel, PermissionManager
from .utils import generate_preview_diff

# Import InterruptedExceptionError from agent to avoid circular import
# Will be imported at runtime when needed


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

    input_str = "\n".join(f"  {k}: {v}" for k, v in tool_input.items())
    if input_str:
        console.print(f"[cyan]{input_str}[/cyan]")

    # Show diff preview when available (e.g., write_file), including during auto-approve
    if diff_content is not None:
        if diff_content == "":
            console.print("[yellow]No changes (content identical)[/yellow]")
        else:
            formatted_diff, _truncated = format_diff_for_display(diff_content, max_lines=100)
            console.print("[bold yellow]Preview of changes:[/bold yellow]")
            console.print(f"[yellow]{formatted_diff}[/yellow]")


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

    Returns:
        True if the tool was executed successfully, False otherwise
    """
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

    # Generate diff preview for file operations
    diff_content = generate_preview_diff(tool_name, tool_input)

    # Show what the agent wants to do
    # (Skip if using approval callback - it will display as part of the approval prompt)
    if not (needs_approval and approval_callback):
        display_tool_request(console, tool_name, tool_input, diff_content)

    if permission_manager.config.is_denied(action_type):
        console.print("[bold red]✗ Action denied by policy[/bold red]")
        add_tool_result(conversation_history, tool_use_id, False, "Action denied by policy", None)
        return False

    if needs_approval:
        approved = ask_approval(
            tool_name,
            tool_input,
            diff_content,
            action_type,
            permission_manager,
            console,
            approval_callback,
        )
        if not approved:
            console.print("[bold yellow]⊘ Action rejected by user[/bold yellow]")
            add_tool_result(
                conversation_history, tool_use_id, False, "Action rejected by user", None
            )
            return False

    # Execute the tool
    success, message, result = executor.execute(tool_name, tool_input)

    # Show result
    if success:
        console.print(f"[bold green]✓ {message}[/bold green]")
    else:
        console.print(f"[bold red]✗ {message}[/bold red]")

    # Add result to conversation
    add_tool_result(conversation_history, tool_use_id, success, message, result)

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
    try:
        response = input("\n[?] Approve this action? [y/N/stop/allow]: ").strip().lower()
        if response == "stop":
            raise InterruptedExceptionError()
        elif response == "allow" or response == "a":
            # Auto-approve this action type for the rest of the session
            if action_type:
                permission_manager.update_permission(action_type, PermissionLevel.AUTO_APPROVE)
                console.print(f"[green]Auto-approving {tool_name} for this session[/green]")
            return True
        return response == "y"
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
        content += f"\n\n{result}"

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
