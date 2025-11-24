"""CLI command modules - organized by functionality."""

from typing import Any

# Re-export all command handlers for backwards compatibility
# Import subagent functions for backwards compatibility with tests
from ...agent.subagent_config_manager import get_subagent_config_manager
from ...agent.subagent_types import list_subagent_types

# Import user manager for backwards compatibility with tests
from ...models import get_user_manager
from .auto import handle_auto_command
from .init import handle_init_command
from .mcp import handle_mcp_command
from .model import _handle_model_add, handle_model_command
from .provider import handle_provider_command, handle_providers_command

# Import conversation functions for backwards compatibility with tests
from .session import (
    CommandResult,
    _get_all_conversations_with_timestamps,
    handle_exit_command,
    handle_reset_command,
    handle_resume_command,
    handle_truncate_command,
)
from .subagent import handle_subagent_command
from .system import (
    handle_compact_command,
    handle_help_command,
    handle_status_command,
    handle_yolo_command,
)


# Simple command dispatcher for backwards compatibility with tests
def handle_command(command: str, agent: Any, console: Any) -> CommandResult | None:
    """Handle a CLI command. Returns None for non-commands."""
    if not command.startswith("/"):
        return None

    parts = command[1:].split(maxsplit=1)
    command_name = parts[0].lower()
    command_args = parts[1] if len(parts) > 1 else ""

    # Try custom commands first
    try:
        from ..custom_commands import handle_custom_command

        result = handle_custom_command(command_name, command_args, agent, console)
        if result is not None:
            return result
    except (ImportError, Exception):
        pass  # Custom commands not available or failed

    # Route to appropriate handler
    if command_name == "exit":
        return handle_exit_command(console)
    elif command_name == "reset":
        return handle_reset_command(agent, console)
    elif command_name == "help":
        return handle_help_command(console)
    elif command_name == "status":
        return handle_status_command(agent, console)
    elif command_name == "auto":
        return handle_auto_command(agent, console, command_args)
    elif command_name == "mcp":
        return handle_mcp_command(agent, console, command_args)
    elif command_name == "subagent":
        return handle_subagent_command(agent, console, command_args)
    elif command_name == "resume":
        return handle_resume_command(agent, console, command_args)
    else:
        return None


__all__ = [
    "handle_auto_command",
    "handle_init_command",
    "handle_model_command",
    "_handle_model_add",
    "handle_mcp_command",
    "handle_provider_command",
    "handle_providers_command",
    "handle_exit_command",
    "handle_reset_command",
    "handle_resume_command",
    "handle_truncate_command",
    "handle_subagent_command",
    "handle_compact_command",
    "handle_help_command",
    "handle_status_command",
    "handle_yolo_command",
    "handle_command",
    "get_subagent_config_manager",
    "list_subagent_types",
    "_get_all_conversations_with_timestamps",
    "get_user_manager",
    "CommandResult",
]
