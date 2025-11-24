"""Main command dispatcher for interactive CLI mode."""

from typing import Any

from rich.console import Console

from ..agent import ClippyAgent
from .commands.auto import handle_auto_command
from .commands.init import handle_init_command
from .commands.mcp import handle_mcp_command
from .commands.model import handle_model_command
from .commands.provider import handle_provider_command, handle_providers_command
from .commands.session import (
    CommandResult,
    handle_exit_command,
    handle_reset_command,
    handle_resume_command,
    handle_truncate_command,
)
from .commands.subagent import handle_subagent_command
from .commands.system import (
    handle_compact_command,
    handle_help_command,
    handle_status_command,
    handle_yolo_command,
)
from .custom_cli import handle_custom_command_management


# Temporary model command (for using a model without saving it)
def handle_temp_model_command(
    agent: ClippyAgent, console: Console, command_args: str
) -> CommandResult:
    """Handle temporary model switching with provider and model_id."""
    if not command_args:
        console.print("[red]Usage: /temp_model <provider> <model_id>[/red]")
        return "continue"

    parts = command_args.strip().split(maxsplit=1)
    if len(parts) < 2:
        console.print("[red]Usage: /temp_model <provider> <model_id>[/red]")
        return "continue"

    provider = parts[0]
    model_id = parts[1]

    # Verify provider exists
    from ..models import get_provider

    provider_obj = get_provider(provider)
    if not provider_obj:
        console.print(f"[red]✗ Unknown provider: {provider}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    # Switch to the temporary model
    success, message = agent.switch_model(
        model=model_id,
        base_url=provider_obj.base_url,
        provider_config=provider_obj,
    )

    if success:
        console.print(f"[green]✓ {message}[/green]")
        console.print("[dim](Use /model add to save this model permanently)[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


# Auto mode configuration
def handle_auto_start_command(
    agent: ClippyAgent, console: Console, command_args: str
) -> CommandResult:
    """Handle /auto-start command to manually trigger auto mode."""
    if command_args:
        console.print("[yellow]❌ /auto-start doesn't accept any arguments[/yellow]")
        return "continue"

    # Check if auto mode is configured
    try:
        from ..agent.auto_mode import (
            check_auto_mode_dependencies,
            get_auto_mode_config,
        )
    except ImportError:
        console.print(
            "[yellow]Auto mode support not available. Install with: "
            "pip install clippy[auto][/yellow]"
        )
        return "continue"

    # Check dependencies
    missing_deps = check_auto_mode_dependencies()
    if missing_deps:
        console.print("[red]❌ Auto mode requires additional dependencies:[/red]")
        for dep in missing_deps:
            console.print(f"  [red]• {dep}[/red]")
        console.print("\n[dim]Install with: pip install clippy[auto][/dim]")
        return "continue"

    config = get_auto_mode_config()
    if config is None or not config.enabled:
        console.print("[red]❌ Auto mode is not enabled[/red]")
        console.print("[dim]Configure with /auto first[/dim]")
        return "continue"

    # Start auto mode
    try:
        agent.start_auto_mode()
        console.print("[green]✓ Auto mode started[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start auto mode: {e}[/red]")

    return "continue"


def handle_auto_stop_command(
    agent: ClippyAgent, console: Console, command_args: str
) -> CommandResult:
    """Handle /auto-stop command to manually stop auto mode."""
    if command_args:
        console.print("[yellow]❌ /auto-stop doesn't accept any arguments[/yellow]")
        return "continue"

    try:
        agent.stop_auto_mode()
        console.print("[green]✓ Auto mode stopped[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to stop auto mode: {e}[/red]")

    return "continue"


# Command registry and handler - mapped by signature type
COMMAND_HANDLERS_AGENT_CONSOLE_ARGS: dict[str, Any] = {
    "resume": handle_resume_command,
    "truncate": handle_truncate_command,
    "auto": handle_auto_command,
    "auto-start": handle_auto_start_command,
    "auto-stop": handle_auto_stop_command,
    "models": handle_model_command,
    "model": handle_model_command,
    "temp_model": handle_temp_model_command,
    "providers": handle_providers_command,
    "provider": handle_provider_command,
    "mcp": handle_mcp_command,
    "init": handle_init_command,
}

COMMAND_HANDLERS_AGENT_CONSOLE: dict[str, Any] = {
    "status": handle_status_command,
    "compact": handle_compact_command,
    "yolo": handle_yolo_command,
    "reset": handle_reset_command,
    "clear": handle_reset_command,  # Alias for reset
    "new": handle_reset_command,  # Alias for reset
}

COMMAND_HANDLERS_CONSOLE_ARGS: dict[str, Any] = {
    "subagent": handle_subagent_command,
    "custom": lambda console, args: handle_custom_command_management(args, console),
}

COMMAND_HANDLERS_CONSOLE_ONLY: dict[str, Any] = {
    "help": handle_help_command,
    "exit": handle_exit_command,
    "quit": handle_exit_command,
}


def parse_command(command: str) -> tuple[str, str] | None:
    """Parse a command string into (command_name, command_args)."""
    if not command.startswith("/"):
        return None

    parts = command[1:].split(maxsplit=1)
    command_name = parts[0].lower()
    command_args = parts[1] if len(parts) > 1 else ""

    return command_name, command_args


def handle_command(command: str, agent: ClippyAgent, console: Console) -> CommandResult | None:
    """Handle a CLI command. Returns None for non-commands."""
    parsed = parse_command(command)
    if parsed is None:
        return None  # Not a command, let the agent handle it

    command_name, command_args = parsed

    # Try each command handler dictionary based on signature type
    if command_name in COMMAND_HANDLERS_AGENT_CONSOLE_ARGS:
        handler = COMMAND_HANDLERS_AGENT_CONSOLE_ARGS[command_name]
        return handler(agent, console, command_args)  # type: ignore[no-any-return]
    elif command_name in COMMAND_HANDLERS_AGENT_CONSOLE:
        handler = COMMAND_HANDLERS_AGENT_CONSOLE[command_name]
        return handler(agent, console)  # type: ignore[no-any-return]
    elif command_name in COMMAND_HANDLERS_CONSOLE_ARGS:
        handler = COMMAND_HANDLERS_CONSOLE_ARGS[command_name]
        return handler(console, command_args)  # type: ignore[no-any-return]
    elif command_name in COMMAND_HANDLERS_CONSOLE_ONLY:
        handler = COMMAND_HANDLERS_CONSOLE_ONLY[command_name]
        return handler(console)  # type: ignore[no-any-return]
    else:
        # Try custom commands
        try:
            from .custom_commands import handle_custom_command

            result = handle_custom_command(command_name, command_args, agent, console)
            if result is not None:
                return result
        except (ImportError, Exception):
            pass  # Custom commands not available or failed

        return None  # Unknown command - let the agent handle it


def register_command_handler(name: str, handler: Any) -> None:
    """Register a new command handler."""
    # Default to agent, console, args signature for new handlers
    COMMAND_HANDLERS_AGENT_CONSOLE_ARGS[name] = handler


def get_command_handlers() -> dict[str, Any]:
    """Get a copy of the command handlers dictionary."""
    all_handlers = {}
    all_handlers.update(COMMAND_HANDLERS_AGENT_CONSOLE_ARGS)
    all_handlers.update(COMMAND_HANDLERS_AGENT_CONSOLE)
    all_handlers.update(COMMAND_HANDLERS_CONSOLE_ARGS)
    all_handlers.update(COMMAND_HANDLERS_CONSOLE_ONLY)
    return all_handlers


def list_available_commands() -> list[str]:
    """Get a list of all available commands."""
    all_handlers = get_command_handlers()
    return sorted(list(all_handlers.keys()))


__all__ = [
    "handle_command",
    "parse_command",
    "register_command_handler",
    "get_command_handlers",
    "list_available_commands",
    "handle_temp_model_command",
    "handle_auto_start_command",
    "handle_auto_stop_command",
    "COMMAND_HANDLERS_AGENT_CONSOLE_ARGS",
    "COMMAND_HANDLERS_AGENT_CONSOLE",
    "COMMAND_HANDLERS_CONSOLE_ARGS",
    "COMMAND_HANDLERS_CONSOLE_ONLY",
]
