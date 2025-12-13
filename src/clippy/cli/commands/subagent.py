"""Subagent command handlers for interactive CLI mode."""

from typing import Literal

from rich.console import Console

CommandResult = Literal["continue", "break", "run"]


def handle_subagent_command(console: Console, command_args: str) -> CommandResult:
    """Handle /subagent command."""
    if not command_args or command_args.strip() == "list":
        return _handle_subagent_list(console)

    # Check for unterminated quotes
    if command_args.count('"') % 2 != 0 or command_args.count("'") % 2 != 0:
        console.print("Error parsing arguments")
        return "continue"

    parts = command_args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()

    if subcommand == "set":
        if len(parts) < 2:
            console.print("Usage: /subagent set <type> <model>")
            return "continue"
        return _handle_subagent_set(console, parts[1])
    elif subcommand == "clear":
        if len(parts) < 2:
            console.print("Usage: /subagent clear <type>")
            return "continue"
        return _handle_subagent_clear(console, parts[1])
    elif subcommand == "reset":
        return _handle_subagent_reset(console)
    elif subcommand == "list":
        return _handle_subagent_list(console)
    else:
        console.print(f"Unknown subcommand: {subcommand}")
        return "continue"


def _handle_subagent_list(console: Console) -> CommandResult:
    """List subagent configurations."""
    try:
        from rich.table import Table

        from ...agent.subagent_config_manager import get_subagent_config_manager
        from ...agent.subagent_types import get_subagent_config, list_subagent_types

        config_manager = get_subagent_config_manager()
        subagent_types = sorted(list_subagent_types())

        table = Table(title="Subagent Type Configurations")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Model Override", style="green")
        table.add_column("Max Iterations", style="yellow")
        table.add_column("Tools", style="blue")

        # Try to get config manager for overrides
        model_overrides = {}
        max_iterations_overrides = {}
        try:
            configs = config_manager.get_all_configurations()
            for subagent_type in subagent_types:
                config = configs.get(subagent_type, {})
                model_overrides[subagent_type] = config.get("model_override", "None")
                max_iterations_overrides[subagent_type] = config.get("max_iterations", 25)
        except Exception:
            # Config manager not available, use defaults
            for subagent_type in subagent_types:
                model_overrides[subagent_type] = "None"
                max_iterations_overrides[subagent_type] = 25
        except Exception as e:
            console.print(f"[red]Error loading subagent configurations: {e}[/red]")
            return "continue"

        for subagent_type in subagent_types:
            type_config = get_subagent_config(subagent_type)
            tools = type_config["allowed_tools"]
            if tools == "all":
                tool_desc = "All"
            else:
                tool_desc = f"{len(tools)} tools"

            table.add_row(
                subagent_type,
                str(model_overrides.get(subagent_type, "None")),
                str(max_iterations_overrides.get(subagent_type, 25)),
                tool_desc,
            )

        console.print(table)
        console.print()
        console.print("[dim]Use '/subagent set <type> <model>' to configure models[/dim]")
        console.print("[dim]Use '/subagent clear <type>' to remove model override[/dim]")
        console.print("[dim]Use '/subagent reset' to clear all overrides[/dim]")
        console.print()
        console.print("[dim]Available subagent types:[/dim]")
        console.print(f"[dim]{', '.join(subagent_types)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading subagent configurations: {e}[/red]")

    return "continue"


def _handle_subagent_set(console: Console, args: str) -> CommandResult:
    """Set model override for a subagent type."""
    from ...agent.subagent_config_manager import get_subagent_config_manager

    config_manager = get_subagent_config_manager()

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        console.print("Usage: /subagent set <type> <model>")
        return "continue"

    subagent_type, model = parts
    try:
        config_manager.set_model_override(subagent_type, model)
        console.print(
            f"[green]✓[/green] Set model override for {subagent_type} to [cyan]{model}[/cyan]"
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")

    return "continue"


def _handle_subagent_clear(console: Console, subagent_type: str) -> CommandResult:
    """Clear model override for a subagent type."""
    try:
        from ...agent.subagent_config_manager import get_subagent_config_manager

        config_manager = get_subagent_config_manager()

        cleared = config_manager.clear_model_override(subagent_type)
        if cleared:
            console.print(f"[green]✓[/green] Cleared model override for {subagent_type}")
        else:
            console.print(f"[yellow]⚠️[/yellow] No model override for {subagent_type}")
    except Exception:
        console.print(f"[red]Error:[/red] No model override for {subagent_type}")

    return "continue"


def _handle_subagent_reset(console: Console) -> CommandResult:
    """Reset all subagent configurations."""
    try:
        from ...agent.subagent_config_manager import get_subagent_config_manager

        config_manager = get_subagent_config_manager()

        count = config_manager.clear_all_overrides()
        if count > 0:
            console.print(
                f"[green]✓[/green] Cleared {count} model override{'s' if count > 1 else ''}"
            )
        else:
            console.print("[yellow]⚠️[/yellow] No model overrides to clear")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

    return "continue"


__all__ = [
    "handle_subagent_command",
]
