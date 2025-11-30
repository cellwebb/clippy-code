"""CLI commands for managing custom slash commands.

Provides commands like:
- /custom add - Interactive wizard to create custom commands
- /custom edit <name> - Interactive wizard to edit commands
- /custom delete <name> - Delete custom commands
- /custom list - List all custom commands
- /custom reload - Reload custom commands
- /custom config - Edit config file directly
- /custom example - Show example configuration
"""

import json
import os
import subprocess

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from ..models import get_user_manager
from .commands import CommandResult
from .custom_commands import get_custom_manager
from .custom_cli_wizards import (
    handle_custom_add,
    handle_custom_delete,
    handle_custom_edit_wizard,
)



def handle_custom_command_management(args: str, console: Console) -> CommandResult:
    """Handle /custom commands for managing custom slash commands."""
    if not args.strip():
        return _handle_custom_help(console)

    parts = args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()
    subcommand_args = parts[1] if len(parts) > 1 else ""

    if subcommand == "list":
        return _handle_custom_list(console)
    elif subcommand == "reload":
        return _handle_custom_reload(console)
    elif subcommand == "add":
        return handle_custom_add(console)
    elif subcommand == "edit":
        return handle_custom_edit_wizard(console, subcommand_args)
    elif subcommand == "delete":
        return handle_custom_delete(console, subcommand_args)
    elif subcommand == "config":
        return _handle_custom_config(console, subcommand_args)
    elif subcommand == "example":
        return _handle_custom_example(console)
    elif subcommand == "help":
        return _handle_custom_help(console)
    else:
        console.print(f"[red]Unknown subcommand: {subcommand}[/red]")
        console.print("[dim]Use /custom help for available subcommands[/dim]")
        return "continue"




def _handle_custom_list(console: Console) -> CommandResult:
    """List all custom commands."""
    manager = get_custom_manager()
    commands = manager.list_commands()

    if not commands:
        console.print("[yellow]No custom commands configured[/yellow]")
        console.print("[dim]Use /custom example to see an example configuration[/dim]")
        return "continue"

    console.print(f"[bold]Custom Commands ({len(commands)}):[/bold]\n")

    for name, cmd in sorted(commands.items()):
        status = ""
        if cmd.hidden:
            status = " [dim](hidden)[/dim]"

        console.print(f"  [cyan]/{name}[/cyan]{status} - {cmd.description}")
        console.print(f"    [dim]Type: {cmd.command_type}[/dim]")

        # Show additional details based on type
        if cmd.command_type == "shell":
            shell_cmd = cmd.config.get("command", "")
            dry_run = cmd.config.get("dry_run", False)
            console.print(f"    [dim]Command: {escape(shell_cmd)}[/dim]")
            if dry_run:
                console.print("    [yellow][dim]Mode: dry-run[/dim][/yellow]")
        elif cmd.command_type == "text":
            text = cmd.config.get("text", "")[:50]
            if len(cmd.config.get("text", "")) > 50:
                text += "..."
            console.print(f"    [dim]Text: {escape(text)}[/dim]")
        elif cmd.command_type == "template":
            template = cmd.config.get("template", "")[:50]
            if len(cmd.config.get("template", "")) > 50:
                template += "..."
            console.print(f"    [dim]Template: {escape(template)}[/dim]")
        elif cmd.command_type == "function":
            function = cmd.config.get("function", "")
            console.print(f"    [dim]Function: {escape(function)}[/dim]")

        console.print("")  # Add spacing

    return "continue"


def _handle_custom_reload(console: Console) -> CommandResult:
    """Reload custom commands from disk."""
    manager = get_custom_manager()
    manager.reload_commands()

    commands = manager.list_commands()
    count = len(commands)

    console.print(f"[green]✓ Reloaded {count} custom command{'s' if count != 1 else ''}[/green]")
    return "continue"


def _handle_custom_config(console: Console, args: str) -> CommandResult:
    """Edit custom commands configuration file directly."""
    user_manager = get_user_manager()
    config_path = user_manager.config_dir / "custom_commands.json"

    # Create config if it doesn't exist
    if not config_path.exists():
        get_custom_manager()  # This will create the example config
        if not config_path.exists():
            console.print("[red]✗ Failed to create configuration file[/red]")
            return "continue"

    # Determine editor
    editor = os.getenv("EDITOR") or os.getenv("VISUAL") or "nano"
    if args:
        editor = args

    try:
        console.print(f"[cyan]Opening {config_path} with {editor}...[/cyan]")
        subprocess.run([editor, str(config_path)], check=True)
        console.print("[green]✓ Configuration updated[/green]")

        # Ask if user wants to reload
        try:
            import questionary

            reload_needed = questionary.confirm("Reload custom commands now?", default=True).ask()
            if reload_needed:
                return _handle_custom_reload(console)
        except ImportError:
            console.print("[dim]Run /custom reload to apply changes[/dim]")

    except subprocess.CalledProcessError:
        console.print(f"[red]✗ Failed to run {editor}[/red]")
        console.print("[dim]Try: /custom edit nano or export EDITOR=nano[/dim]")
    except Exception as e:
        console.print(f"[red]✗ Failed to open editor: {escape(str(e))}[/red]")

    return "continue"


def _handle_custom_example(console: Console) -> CommandResult:
    """Show example custom commands configuration."""
    example_config = {
        "commands": {
            "git": {
                "type": "shell",
                "description": "Execute git commands safely",
                "command": "git {args}",
                "working_dir": ".",
                "timeout": 30,
                "dry_run": False,
                "dangerous": False,
            },
            "ls": {
                "type": "shell",
                "description": "List directory contents",
                "command": "ls -la {args}",
                "dry_run": False,
                "dangerous": False,
            },
            "whoami": {
                "type": "text",
                "description": "Show current user and directory",
                "text": "👋 User: {user}\n📁 Directory: {cwd}",
                "formatted": True,
            },
            "todo": {
                "type": "template",
                "description": "Quick todo list template",
                "template": (
                    "📝 TODO List ({user} @ {cwd})\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "{args}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                ),
                "formatted": True,
            },
            "stats": {
                "type": "function",
                "description": "Show session statistics",
                "function": "clippy.cli.custom_commands.show_session_stats",
            },
            "deploy": {
                "type": "shell",
                "description": "Deploy application (dangerous)",
                "command": "deploy.sh {args}",
                "dangerous": True,
                "working_dir": ".",
                "timeout": 120,
            },
        }
    }

    console.print(
        Panel.fit(
            "[bold cyan]Custom Commands Configuration Example[/bold cyan]\n\n"
            "[dim]Save this as ~/.clippy/custom_commands.json[/dim]\n\n"
            f"[bold green]{json.dumps(example_config, indent=2)}[/bold green]\n\n"
            "[bold]Command Types:[/bold]\n"
            "  [cyan]shell[/cyan] - Execute shell commands (supports {args} placeholder)\n"
            "  [cyan]text[/cyan]   - Display static text with variable substitution\n"
            "  [cyan]template[/cyan] - Display formatted text with more variables\n"
            "  [cyan]function[/cyan] - Call Python functions\n\n"
            "[bold]Variables Available:[/bold]\n"
            "  [cyan]{args}[/cyan] - Command arguments after the command name\n"
            "  [cyan]{cwd}[/cyan] - Current working directory\n"
            "  [cyan]{user}[/cyan] - Current username\n"
            "  [cyan]{model}[/cyan] - Current LLM model\n"
            "  [cyan]{provider}[/cyan] - Current provider name\n"
            "  [cyan]{message_count}[/cyan] - Number of messages in conversation\n\n"
            "[bold]Shell Command Options:[/bold]\n"
            "  [cyan]working_dir[/cyan] - Directory to run command in (default: current)\n"
            "  [cyan]timeout[/cyan] - Command timeout in seconds (default: 30)\n"
            "  [cyan]dry_run[/cyan] - Show command without executing (default: false)\n"
            "  [cyan]dangerous[/cyan] - Allow dangerous commands (default: false)",
            title="Custom Commands",
            border_style="cyan",
        )
    )

    return "continue"


def _handle_custom_help(console: Console) -> CommandResult:
    """Show help for custom command management."""
    console.print(
        Panel.fit(
            "[bold]Custom Command Management:[/bold]\n"
            "  /custom - Show this help message\n"
            "  /custom add - Interactive wizard to create a new custom command\n"
            "  /custom edit <name> - Interactive wizard to edit an existing command\n"
            "  /custom delete <name> - Delete a custom command\n"
            "  /custom list - List all configured custom commands\n"
            "  /custom reload - Reload custom commands from disk\n"
            "  /custom config [editor] - Edit configuration file directly\n"
            "    Uses $EDITOR or 'nano' by default\n"
            "  /custom example - Show example configuration\n"
            "  /custom help - Show this help message\n\n"
            "[bold]Configuration:[/bold]\n"
            "  Project config: .clippy/custom_commands.json\n"
            "  Global config: ~/.clippy/custom_commands.json\n"
            "  Project commands override global commands with same name\n\n"
            "[bold]Examples:[/bold]\n"
            "  /custom add - Create a new custom command interactively\n"
            "  /custom edit mycommand - Edit 'mycommand' interactively\n"
            "  /custom delete mycommand - Delete 'mycommand'",
            title="Custom Commands Help",
            border_style="blue",
        )
    )

    return "continue"

