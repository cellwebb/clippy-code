"""One-shot mode for CLI."""

import sys

from rich.console import Console
from rich.markup import escape

from ..agent import ClippyAgent, InterruptedExceptionError


def _suggest_similar_commands(command: str) -> list[str]:
    """
    Suggest similar commands for a given invalid command.

    Args:
        command: The invalid command string

    Returns:
        List of suggested valid commands
    """
    from difflib import get_close_matches

    # Extract command name (first word after /)
    parts = command.strip().split()
    if not parts:
        return []

    invalid_cmd = parts[0][1:].lower()  # Remove leading / and lowercase

    # List of valid commands
    valid_commands = [
        "help",
        "exit",
        "quit",
        "reset",
        "clear",
        "new",
        "resume",
        "status",
        "compact",
        "providers",
        "provider",
        "model",
        "subagent",
        "auto",
        "mcp",
        "truncate",
    ]

    # Find close matches using fuzzy matching
    suggestions = get_close_matches(invalid_cmd, valid_commands, n=3, cutoff=0.6)

    # Format suggestions with leading /
    return [f"/{suggestion}" for suggestion in suggestions]


def run_one_shot(agent: ClippyAgent, prompt: str, auto_approve: bool) -> None:
    """Run clippy-code in one-shot mode."""
    console = Console()

    # Check if this looks like a slash command
    if prompt.strip().startswith("/"):
        console.print(f"[red]✗ Unknown command: {prompt}[/red]")

        # Try to suggest similar commands
        command_suggestions = _suggest_similar_commands(prompt)
        if command_suggestions:
            console.print(f"[dim]Did you mean: {', '.join(command_suggestions)}?[/dim]")

        console.print("[dim]Slash commands are only available in interactive mode[/dim]")
        console.print("[dim]Run 'clippy' without arguments to start interactive mode[/dim]")
        sys.exit(1)

    try:
        agent.run(prompt, auto_approve_all=auto_approve)
    except InterruptedExceptionError:
        console.print("\n[yellow]Execution interrupted[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error: {escape(str(e))}[/bold red]")
        sys.exit(1)
