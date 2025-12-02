"""Interactive wizards for custom command management."""

import json
import re
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markup import escape

from ..models import get_user_manager
from .commands import CommandResult
from .custom_commands import get_custom_manager

# Helper functions

def _validate_command_name(name: str) -> tuple[bool, str]:
    """Validate a command name.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Command name cannot be empty"

    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return False, "Command name can only contain letters, numbers, hyphens, and underscores"

    if name.startswith("-"):
        return False, "Command name cannot start with a hyphen"

    return True, ""


def _get_config_path(scope: str) -> Path:
    """Get the configuration file path for the specified scope."""
    if scope == "project":
        return Path.cwd() / ".clippy" / "custom_commands.json"
    else:  # global
        user_manager = get_user_manager()
        return user_manager.config_dir / "custom_commands.json"


def _load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from a JSON file."""
    if not config_path.exists():
        return {"commands": {}}

    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return {"commands": {}}


def _save_config(config_path: Path, config: dict[str, Any]) -> bool:
    """Save configuration to a JSON file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False


# Type-specific configuration prompts

def _prompt_shell_config(console: Console, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Interactive prompts for shell command configuration."""
    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        raise

    defaults = defaults or {}

    config: dict[str, Any] = {"type": "shell"}

    # Command to execute
    command = questionary.text(
        "Shell command to execute:",
        default=defaults.get("command", ""),
        instruction="Use {args} as placeholder for arguments"
    ).ask()

    if command is None:  # User cancelled
        raise KeyboardInterrupt()

    config["command"] = command

    # Working directory
    working_dir = questionary.text(
        "Working directory:",
        default=defaults.get("working_dir", "."),
    ).ask()

    if working_dir is None:
        raise KeyboardInterrupt()

    config["working_dir"] = working_dir

    # Timeout
    timeout_str = questionary.text(
        "Timeout (seconds):",
        default=str(defaults.get("timeout", 30)),
    ).ask()

    if timeout_str is None:
        raise KeyboardInterrupt()

    try:
        config["timeout"] = int(timeout_str)
    except ValueError:
        config["timeout"] = 30

    # Dry run
    dry_run = questionary.confirm(
        "Dry run mode (show command without executing)?",
        default=defaults.get("dry_run", False),
    ).ask()

    if dry_run is None:
        raise KeyboardInterrupt()

    config["dry_run"] = dry_run

    # Dangerous
    dangerous = questionary.confirm(
        "Allow dangerous commands (rm, sudo, etc.)?",
        default=defaults.get("dangerous", False),
    ).ask()

    if dangerous is None:
        raise KeyboardInterrupt()

    config["dangerous"] = dangerous

    return config


def _prompt_text_config(console: Console, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Interactive prompts for text command configuration."""
    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        raise

    defaults = defaults or {}

    config: dict[str, Any] = {"type": "text"}

    # Text content
    text = questionary.text(
        "Text to display:",
        default=defaults.get("text", ""),
        multiline=False,
        instruction="Use {args}, {user}, {cwd} for variables"
    ).ask()

    if text is None:
        raise KeyboardInterrupt()

    config["text"] = text

    # Formatted
    formatted = questionary.confirm(
        "Use rich formatting (colors, bold, etc.)?",
        default=defaults.get("formatted", True),
    ).ask()

    if formatted is None:
        raise KeyboardInterrupt()

    config["formatted"] = formatted

    return config


def _prompt_template_config(console: Console, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Interactive prompts for template command configuration."""
    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        raise

    defaults = defaults or {}

    config: dict[str, Any] = {"type": "template"}

    # Template content
    template = questionary.text(
        "Template text:",
        default=defaults.get("template", ""),
        multiline=False,
        instruction="Use {args}, {user}, {cwd}, {model}, {provider}, {message_count}"
    ).ask()

    if template is None:
        raise KeyboardInterrupt()

    config["template"] = template

    # Formatted
    formatted = questionary.confirm(
        "Use rich formatting (colors, bold, etc.)?",
        default=defaults.get("formatted", True),
    ).ask()

    if formatted is None:
        raise KeyboardInterrupt()

    config["formatted"] = formatted

    return config


def _prompt_function_config(console: Console, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Interactive prompts for function command configuration."""
    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        raise

    defaults = defaults or {}

    config: dict[str, Any] = {"type": "function"}

    # Function path
    function = questionary.text(
        "Python function path (e.g., module.function):",
        default=defaults.get("function", ""),
        instruction="Format: module.submodule.function_name"
    ).ask()

    if function is None:
        raise KeyboardInterrupt()

    config["function"] = function

    return config


# Main wizard functions

def handle_custom_add(console: Console) -> CommandResult:
    """Interactive wizard to add a new custom command."""
    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        return "continue"

    console.print("[bold cyan]Add New Custom Command[/bold cyan]\n")

    try:
        # Select scope
        scope = questionary.select(
            "Scope:",
            choices=[
                questionary.Choice("Project (.clippy/custom_commands.json)", value="project"),
                questionary.Choice("Global (~/.clippy/custom_commands.json)", value="global"),
            ],
            instruction="Project commands override global commands"
        ).ask()

        if scope is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        # Command name
        while True:
            name = questionary.text(
                "Command name:",
                instruction="Letters, numbers, hyphens, and underscores only"
            ).ask()

            if name is None:
                console.print("[yellow]Cancelled[/yellow]")
                return "continue"

            name = name.strip().lower()
            is_valid, error = _validate_command_name(name)

            if not is_valid:
                console.print(f"[red]✗ {error}[/red]")
                continue

            # Check if command exists
            manager = get_custom_manager()
            existing_cmd = manager.get_command(name)

            if existing_cmd:
                overwrite = questionary.confirm(
                    f"Command '{name}' already exists. Overwrite?",
                    default=False
                ).ask()

                if not overwrite:
                    continue

            break

        # Description
        description = questionary.text(
            "Description:",
            default=f"Custom command: {name}"
        ).ask()

        if description is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        # Command type
        cmd_type = questionary.select(
            "Command type:",
            choices=[
                questionary.Choice("Shell - Execute shell commands", value="shell"),
                questionary.Choice("Text - Display static text", value="text"),
                questionary.Choice("Template - Display formatted text with variables", value="template"),
                questionary.Choice("Function - Call a Python function", value="function"),
            ]
        ).ask()

        if cmd_type is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        # Type-specific configuration
        if cmd_type == "shell":
            config = _prompt_shell_config(console)
        elif cmd_type == "text":
            config = _prompt_text_config(console)
        elif cmd_type == "template":
            config = _prompt_template_config(console)
        else:  # function
            config = _prompt_function_config(console)

        # Add description
        config["description"] = description

        # Hidden flag
        hidden = questionary.confirm(
            "Hide from help menu?",
            default=False
        ).ask()

        if hidden is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        config["hidden"] = hidden

        # Show summary
        console.print("\n[bold]Command Summary:[/bold]")
        console.print(f"  Name: [cyan]{name}[/cyan]")
        console.print(f"  Scope: [cyan]{scope}[/cyan]")
        console.print(f"  Type: [cyan]{cmd_type}[/cyan]")
        console.print(f"  Description: {description}")

        if cmd_type == "shell":
            console.print(f"  Command: [dim]{escape(config['command'])}[/dim]")
        elif cmd_type in ["text", "template"]:
            content_key = "text" if cmd_type == "text" else "template"
            content = config[content_key]
            if len(content) > 50:
                content = content[:50] + "..."
            console.print(f"  Content: [dim]{escape(content)}[/dim]")
        elif cmd_type == "function":
            console.print(f"  Function: [dim]{config['function']}[/dim]")

        # Confirm
        confirm = questionary.confirm(
            "\nCreate this custom command?",
            default=True
        ).ask()

        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        # Save to config file
        config_path = _get_config_path(scope)
        config_data = _load_config(config_path)

        if "commands" not in config_data:
            config_data["commands"] = {}

        config_data["commands"][name] = config

        if _save_config(config_path, config_data):
            console.print(f"\n[green]✓ Custom command '{name}' created successfully![/green]")
            console.print(f"[dim]Config saved to: {config_path}[/dim]")

            # Reload commands
            manager.reload_commands()
            console.print("[green]✓ Commands reloaded[/green]")
        else:
            console.print(f"\n[red]✗ Failed to save command to {config_path}[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {escape(str(e))}[/red]")

    return "continue"


def handle_custom_edit_wizard(console: Console, name: str) -> CommandResult:
    """Interactive wizard to edit an existing custom command."""
    if not name:
        console.print("[red]Usage: /custom edit <command-name>[/red]")
        return "continue"

    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        return "continue"

    manager = get_custom_manager()
    cmd = manager.get_command(name)

    if not cmd:
        console.print(f"[red]✗ Command '{name}' not found[/red]")
        console.print("[dim]Use /custom list to see available commands[/dim]")
        return "continue"

    console.print(f"[bold cyan]Edit Custom Command: {name}[/bold cyan]\n")

    try:
        # Determine scope
        scopes = manager.get_command_scope(name)

        if not scopes:
            console.print(f"[red]✗ Could not determine scope for command '{name}'[/red]")
            return "continue"

        scope = scopes[0]  # Default to first scope

        if len(scopes) > 1:
            # Command exists in multiple scopes, ask which to edit
            scope = questionary.select(
                "Command exists in multiple scopes. Edit which one?",
                choices=[
                    questionary.Choice("Project (.clippy/custom_commands.json)", value="project"),
                    questionary.Choice("Global (~/.clippy/custom_commands.json)", value="global"),
                ]
            ).ask()

            if scope is None:
                console.print("[yellow]Cancelled[/yellow]")
                return "continue"

        # Load config from the selected scope
        config_path = _get_config_path(scope)
        config_data = _load_config(config_path)
        existing_config = config_data.get("commands", {}).get(name, {})

        # Get current type
        cmd_type = existing_config.get("type", "text")

        # Ask if user wants to change type
        change_type = questionary.confirm(
            f"Current type is '{cmd_type}'. Change type?",
            default=False
        ).ask()

        if change_type is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        if change_type:
            cmd_type = questionary.select(
                "New command type:",
                choices=[
                    questionary.Choice("Shell - Execute shell commands", value="shell"),
                    questionary.Choice("Text - Display static text", value="text"),
                    questionary.Choice("Template - Display formatted text with variables", value="template"),
                    questionary.Choice("Function - Call a Python function", value="function"),
                ]
            ).ask()

            if cmd_type is None:
                console.print("[yellow]Cancelled[/yellow]")
                return "continue"

        # Type-specific configuration with defaults
        if cmd_type == "shell":
            config = _prompt_shell_config(console, existing_config if not change_type else None)
        elif cmd_type == "text":
            config = _prompt_text_config(console, existing_config if not change_type else None)
        elif cmd_type == "template":
            config = _prompt_template_config(console, existing_config if not change_type else None)
        else:  # function
            config = _prompt_function_config(console, existing_config if not change_type else None)

        # Description
        description = questionary.text(
            "Description:",
            default=existing_config.get("description", f"Custom command: {name}")
        ).ask()

        if description is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        config["description"] = description

        # Hidden flag
        hidden = questionary.confirm(
            "Hide from help menu?",
            default=existing_config.get("hidden", False)
        ).ask()

        if hidden is None:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        config["hidden"] = hidden

        # Confirm
        confirm = questionary.confirm(
            f"\nSave changes to '{name}'?",
            default=True
        ).ask()

        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        # Save to config file
        config_data["commands"][name] = config

        if _save_config(config_path, config_data):
            console.print(f"\n[green]✓ Custom command '{name}' updated successfully![/green]")
            console.print(f"[dim]Config saved to: {config_path}[/dim]")

            # Reload commands
            manager.reload_commands()
            console.print("[green]✓ Commands reloaded[/green]")
        else:
            console.print(f"\n[red]✗ Failed to save changes to {config_path}[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {escape(str(e))}[/red]")

    return "continue"


def handle_custom_delete(console: Console, name: str) -> CommandResult:
    """Delete a custom command."""
    if not name:
        console.print("[red]Usage: /custom delete <command-name>[/red]")
        return "continue"

    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for confirmation[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        return "continue"

    manager = get_custom_manager()
    cmd = manager.get_command(name)

    if not cmd:
        console.print(f"[red]✗ Command '{name}' not found[/red]")
        console.print("[dim]Use /custom list to see available commands[/dim]")
        return "continue"

    try:
        # Determine scope
        scopes = manager.get_command_scope(name)

        if not scopes:
            console.print(f"[red]✗ Could not find command '{name}'[/red]")
            return "continue"

        scope_to_delete = scopes[0]  # Default to first scope

        if len(scopes) > 1:
            # Command exists in multiple scopes, ask which to delete
            scope_to_delete = questionary.select(
                "Command exists in multiple scopes. Delete from which one?",
                choices=[
                    questionary.Choice("Project (.clippy/custom_commands.json)", value="project"),
                    questionary.Choice("Global (~/.clippy/custom_commands.json)", value="global"),
                    questionary.Choice("Both", value="both"),
                ]
            ).ask()

            if scope_to_delete is None:
                console.print("[yellow]Cancelled[/yellow]")
                return "continue"

        # Show command details
        console.print("\n[bold]Command Details:[/bold]")
        console.print(f"  Name: [cyan]{name}[/cyan]")
        console.print(f"  Type: [cyan]{cmd.command_type}[/cyan]")
        console.print(f"  Description: {cmd.description}")
        console.print(f"  Scope: [cyan]{', '.join(scopes)}[/cyan]")

        # Confirm deletion
        confirm = questionary.confirm(
            f"\nAre you sure you want to delete '{name}'?",
            default=False
        ).ask()

        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return "continue"

        # Delete from selected scope(s)
        scopes_to_delete = scopes if scope_to_delete == "both" else [scope_to_delete]

        success = True
        for scope in scopes_to_delete:
            if not manager.remove_command(name, scope):
                console.print(f"[red]✗ Failed to delete from {scope} scope[/red]")
                success = False
            else:
                console.print(f"[green]✓ Deleted from {scope} scope[/green]")

        if success:
            # Reload commands
            manager.reload_commands()
            console.print(f"[green]✓ Command '{name}' deleted successfully![/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error: {escape(str(e))}[/red]")

    return "continue"
