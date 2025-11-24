"""Auto-approval command handlers."""

from rich.console import Console

from ...agent import ClippyAgent
from ...permissions import ActionType
from .session import CommandResult


def handle_auto_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /auto commands for managing auto-approved actions."""
    if not command_args:
        console.print("[red]Usage: /auto <command> [args][/red]")
        console.print("[dim]Commands: list, revoke <action>, clear[/dim]")
        return "continue"

    parts = command_args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()

    if subcommand == "list":
        return _handle_auto_list(agent, console)
    elif subcommand == "revoke":
        if len(parts) < 2:
            console.print("[red]Usage: /auto revoke <action>[/red]")
            return "continue"
        action_name = parts[1]
        return _handle_auto_revoke(agent, console, action_name)
    elif subcommand == "clear":
        return _handle_auto_clear(agent, console)
    else:
        console.print(f"[red]Unknown auto command: {subcommand}[/red]")
        console.print("[dim]Commands: list, revoke <action>, clear[/dim]")
        return "continue"


def _handle_auto_list(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /auto list command."""
    auto_actions = agent.get_auto_actions()

    if not auto_actions:
        console.print("[dim]No actions are currently auto-approved.[/dim]")
        return "continue"

    console.print("[bold cyan]Auto-approved Actions:[/bold cyan]")
    console.print("")

    for action in auto_actions:
        console.print(f"  • [green]{action}[/green]")

    console.print("")
    console.print("[dim]Use /auto revoke <action> to remove auto-approval.[/dim]")
    console.print("[dim]Use /auto clear to remove all auto-approvals.[/dim]")
    return "continue"


def _handle_auto_revoke(agent: ClippyAgent, console: Console, action_name: str) -> CommandResult:
    """Handle /auto revoke command."""
    # Parse action name
    try:
        action = ActionType(action_name)
    except ValueError:
        console.print(f"[red]✗ Unknown action: {action_name}[/red]")
        available_actions = ", ".join(a.value for a in ActionType)
        console.print("[dim]Available actions: " + available_actions + "[/dim]")
        return "continue"

    # Revoke the action
    success = agent.revoke_auto_action(action)

    if success:
        console.print(f"[green]✓ Auto-approval revoked for {action.value}[/green]")
    else:
        console.print(f"[yellow]⚠ Action {action.value} was not auto-approved[/yellow]")

    return "continue"


def _handle_auto_clear(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /auto clear command."""
    revoked_count = agent.clear_auto_actions()

    if revoked_count > 0:
        console.print(f"[green]✓ Auto-approval cleared for {revoked_count} action[/green]")
    else:
        console.print("[dim]No actions were auto-approved.[/dim]")

    return "continue"
