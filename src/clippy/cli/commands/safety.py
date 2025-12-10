"""Safety checker control commands for interactive CLI mode."""

from typing import Literal

from rich.console import Console
from rich.panel import Panel

from ...agent import ClippyAgent

CommandResult = Literal["continue", "break", "run"]


def handle_safety_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /safety command to control the safety checker."""

    # Parse subcommand
    parts = command_args.strip().split()
    if not parts:
        # Show current safety status
        _show_safety_status(agent, console)
        return "continue"

    subcommand = parts[0].lower()

    if subcommand in ("on", "enable", "start"):
        _enable_safety_checker(agent, console)
    elif subcommand in ("off", "disable", "stop"):
        _disable_safety_checker(agent, console)
    elif subcommand in ("status", "show", "info"):
        _show_safety_status(agent, console)
    elif subcommand in ("help", "--help", "-h"):
        _show_safety_help(console)
    else:
        console.print(
            Panel.fit(
                f"[bold red]✗ Unknown safety subcommand: {subcommand}[/bold red]\n\n"
                "[dim]Use /safety help to see available subcommands[/dim]",
                title="Safety Error",
                border_style="red",
            )
        )

    return "continue"


def _enable_safety_checker(agent: ClippyAgent, console: Console) -> None:
    """Enable the safety checker."""
    try:
        # Check if executor has safety checker capabilities
        if hasattr(agent.executor, "set_llm_provider") and hasattr(agent.executor, "_llm_provider"):
            if agent.executor._llm_provider is None:
                console.print(
                    Panel.fit(
                        "[bold yellow]⚠ Cannot Enable Safety Checker[/bold yellow]\n\n"
                        "No LLM provider configured. Safety checking requires an LLM provider "
                        "to evaluate command safety.\n\n"
                        "[dim]Please configure a model with an LLM provider first.[/dim]",
                        title="Safety Error",
                        border_style="yellow",
                    )
                )
                return

        # Enable safety checking
        agent.executor.set_safety_checker_enabled(True)

        console.print(
            Panel.fit(
                "[bold green]✓ Safety Checker ENABLED[/bold green]\n\n"
                "[bold]Command safety checking is now active.[/bold]\n"
                "[dim]Potentially dangerous commands will be evaluated by the LLM "
                "before execution.[/dim]\n\n"
                "[dim]Use /safety off to disable.[/dim]",
                title="Safety Status",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]✗ Failed to enable safety checker[/bold red]\n\nError: {str(e)}",
                title="Safety Error",
                border_style="red",
            )
        )


def _disable_safety_checker(agent: ClippyAgent, console: Console) -> None:
    """Disable the safety checker."""
    try:
        # Disable safety checking
        agent.executor.set_safety_checker_enabled(False)

        console.print(
            Panel.fit(
                "[bold yellow]⚠ Safety Checker DISABLED[/bold yellow]\n\n"
                "[bold]Command safety checking is now inactive.[/bold]\n"
                "[dim]⚠️ WARNING: All commands will execute without safety evaluation![/dim]\n\n"
                "[dim]Use /safety on to re-enable.[/dim]",
                title="Safety Status",
                border_style="yellow",
            )
        )
    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]✗ Failed to disable safety checker[/bold red]\n\nError: {str(e)}",
                title="Safety Error",
                border_style="red",
            )
        )


def _show_safety_status(agent: ClippyAgent, console: Console) -> None:
    """Show current safety checker status."""
    try:
        # Check if safety checker is enabled
        is_enabled = agent.executor.is_safety_checker_enabled()

        # Check if safety checker is available
        has_safety_checker = (
            hasattr(agent.executor, "_safety_checker")
            and agent.executor._safety_checker is not None
        )

        # Check if LLM provider is available
        has_llm_provider = (
            hasattr(agent.executor, "_llm_provider") and agent.executor._llm_provider is not None
        )

        if is_enabled and has_safety_checker:
            status = "[bold green]ENABLED[/bold green]"
            border_style = "green"
            status_icon = "✅"
        elif not is_enabled and has_safety_checker:
            status = "[bold yellow]DISABLED[/bold yellow]"
            border_style = "yellow"
            status_icon = "⚠️"
        elif has_llm_provider:
            status = "[bold yellow]AVAILABLE (disabled)[/bold yellow]"
            border_style = "yellow"
            status_icon = "⚠️"
        else:
            status = "[bold red]NOT AVAILABLE[/bold red]"
            border_style = "red"
            status_icon = "❌"

        # Get safety checker stats if available
        cache_info = ""
        if has_safety_checker and not is_enabled and agent.executor._safety_checker is not None:
            try:
                stats = agent.executor._safety_checker.get_cache_stats()
                if stats.get("enabled", False):
                    cache_info = (
                        f"\n[bold]Cache Status:[/bold]\n"
                        f"  Enabled: [green]Yes[/green]\n"
                        f"  Size: [cyan]{stats['size']}[/cyan]/[cyan]{stats['max_size']}[/cyan] "
                        f"entries\n"
                        f"  Hit Rate: [cyan]{stats['hit_rate']:.1%}[/cyan]\n"
                        f"  Hits: [cyan]{stats['hits']}[/cyan], "
                        f"Misses: [cyan]{stats['misses']}[/cyan]"
                    )
                else:
                    cache_info = "\n[bold]Cache Status:[/bold] [red]Disabled[/red]"
            except Exception:
                cache_info = "\n[bold]Cache Status:[/bold] [dim]Unable to retrieve[/dim]"

        # Build status info
        safety_status = "Available" if has_safety_checker else "Not Available"
        llm_status = "✅ Available" if has_llm_provider else "❌ Not Available"
        active_status = "✅ Yes" if is_enabled else "❌ No"

        status_info = (
            f"[bold]Safety Checker Status:[/bold] {status}\n\n"
            f"[bold]Configuration:[/bold]\n"
            f"  Safety Checker: {status_icon} {safety_status}\n"
            f"  LLM Provider: {llm_status}\n"
            f"  Currently Active: {active_status}{cache_info}"
        )

        console.print(
            Panel.fit(
                status_info,
                title="Safety Status",
                border_style=border_style,
            )
        )

        # Show usage tips
        if not is_enabled:
            console.print("\n[dim]💡 Use /safety on to enable safety checking[/dim]")
        elif not has_safety_checker and has_llm_provider:
            console.print(
                "\n[dim]💡 Safety checker available but not initialized - this is unusual[/dim]"
            )
        elif not has_llm_provider:
            console.print(
                "\n[dim]💡 Configure a model with an LLM provider to enable safety checking[/dim]"
            )

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]✗ Unable to retrieve safety status[/bold red]\n\nError: {str(e)}",
                title="Safety Error",
                border_style="red",
            )
        )


def _show_safety_help(console: Console) -> None:
    """Show safety command help."""
    help_content = (
        "[bold]Safety Checker Control:[/bold]\n\n"
        "[cyan]/safety[/cyan] - Show current safety checker status\n"
        "[cyan]/safety on[/cyan] or [cyan]/safety enable[/cyan] - Enable safety checking\n"
        "[cyan]/safety off[/cyan] or [cyan]/safety disable[/cyan] - Disable safety checking\n"
        "[cyan]/safety status[/cyan] - Show detailed status information\n"
        "[cyan]/safety help[/cyan] - Show this help message\n\n"
        "[bold]About Safety Checking:[/bold]\n\n"
        "The safety checker uses an LLM to evaluate potentially dangerous commands "
        "before they are executed. When enabled, commands like those involving:\n\n"
        "• Recursive deletion (rm -rf)\n"
        "• System file modification\n"
        "• Network downloads and execution\n"
        "• Privileged operations\n\n"
        "will be evaluated and either allowed or blocked based on their potential risk.\n\n"
        "[bold]Cache:[/bold]\n\n"
        "Safety checking results are cached to improve performance. The cache stores "
        "the safety evaluation for previously seen commands to avoid repeated LLM calls.\n\n"
        "[bold]⚠️ Warning:[/bold]\n\n"
        "Disabling safety checking removes an important safety layer. Only disable "
        "if you're working in a trusted environment and understand the risks."
    )

    console.print(
        Panel.fit(
            help_content,
            title="Safety Command Help",
            border_style="blue",
        )
    )
