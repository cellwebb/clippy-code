"""Init command handler for conversation initialization."""

from typing import Literal

from rich.console import Console

from ...agent import ClippyAgent

CommandResult = Literal["continue", "break", "run"]


def handle_init_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /init command for conversation initialization."""
    if not command_args:
        console.print("[red]Usage: /init <init_message>[/red]")
        return "continue"

    init_message = command_args.strip()

    # Send a message as the user to initialize the conversation
    agent.append_user_message(init_message)

    console.print("[green]✓ Conversation initialized with:[/green]")
    console.print(f"  [dim]{init_message}[/dim]")
    return "continue"


__all__ = [
    "handle_init_command",
]
