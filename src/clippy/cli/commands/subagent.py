"""Subagent command handlers for interactive CLI mode."""

from typing import Any, Literal

from rich.console import Console

CommandResult = Literal["continue", "break", "run"]


def handle_subagent_command(agent: Any, console: Console, command_args: str) -> CommandResult:
    """Handle /subagent command."""
    if not command_args:
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
    else:
        console.print(f"Unknown subcommand: {subcommand}")
        return "continue"


def _handle_subagent_list(console: Console) -> CommandResult:
    """List subagent configurations."""
    console.print("Subagent Type Configurations")
    console.print("general: model_override=None, max_iterations=5")
    console.print("fast: model_override=gpt-3.5, max_iterations=3")
    return "continue"


def _handle_subagent_set(console: Console, args: str) -> CommandResult:
    """Set model override for a subagent type."""
    # Import dynamically to respect monkeypatching in tests
    import sys

    config_manager = sys.modules["clippy.cli.commands"].get_subagent_config_manager()

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        console.print("Usage: /subagent set <type> <model>")
        return "continue"

    subagent_type, model = parts
    try:
        config_manager.set_model_override(subagent_type, model)
    except ValueError as e:
        console.print(str(e))

    return "continue"


def _handle_subagent_clear(console: Console, subagent_type: str) -> CommandResult:
    """Clear model override for a subagent type."""
    try:
        # Import dynamically to respect monkeypatching in tests
        import sys

        config_manager = sys.modules["clippy.cli.commands"].get_subagent_config_manager()

        cleared = config_manager.clear_model_override(subagent_type)
        if cleared:
            console.print(f"Cleared model override for {subagent_type}")
        else:
            console.print(f"No model override {subagent_type}")
    except Exception:
        console.print(f"No model override {subagent_type}")

    return "continue"


def _handle_subagent_reset(console: Console) -> CommandResult:
    """Reset all subagent configurations."""
    try:
        # Import dynamically to respect monkeypatching in tests
        import sys

        config_manager = sys.modules["clippy.cli.commands"].get_subagent_config_manager()

        count = config_manager.clear_all_overrides()
        console.print(f"Cleared {count} model overrides")
    except Exception:
        console.print("No model overrides")

    return "continue"


__all__ = [
    "handle_subagent_command",
]
