"""Custom slash command system for clippy-code.

Allows users to define their own slash commands through configuration files.
"""

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Literal

from rich.console import Console
from rich.markup import escape

from ..models import get_user_manager
from .commands import CommandResult

# Custom command types
CustomCommandType = Literal["shell", "text", "template", "function"]


class CustomCommand:
    """Represents a custom slash command."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self.command_type = config.get("type", "text")
        self.description = config.get("description", f"Custom command: {name}")
        self.hidden = config.get("hidden", False)

        # Validate command type
        if self.command_type not in ["shell", "text", "template", "function"]:
            raise ValueError(f"Invalid command type: {self.command_type}")

    def execute(self, args: str, agent: Any, console: Console) -> CommandResult:  # type: ignore[return]
        """Execute the custom command."""
        try:
            if self.command_type == "shell":
                return self._execute_shell(args, console)
            elif self.command_type == "text":
                return self._execute_text(args, console)
            elif self.command_type == "template":
                return self._execute_template(args, agent, console)
            elif self.command_type == "function":
                return self._execute_function(args, agent, console)
        except Exception as e:
            console.print(
                f"[red]✗ Error executing custom command '{self.name}': {escape(str(e))}[/red]"
            )
            return "continue"

    def _execute_shell(self, args: str, console: Console) -> CommandResult:
        """Execute a shell command."""
        shell_cmd = self.config.get("command", "")
        if not shell_cmd:
            console.print(f"[red]✗ No shell command specified for '{self.name}'[/red]")
            return "continue"

        # Replace {args} placeholder with actual args
        if "{args}" in shell_cmd:
            full_cmd = (
                shell_cmd.format(args=args) if args.strip() else shell_cmd.replace("{args}", "")
            )
        else:
            # Append args if no placeholder
            full_cmd = f"{shell_cmd} {args}" if args.strip() else shell_cmd

        # Check for dry_run mode
        dry_run = self.config.get("dry_run", False)
        if dry_run:
            console.print(f"[dim]Would execute: [cyan]{full_cmd}[/cyan][/dim]")
            return "continue"

        # Security check - warn before executing potentially dangerous commands
        dangerous_commands = ["rm", "sudo", "chmod", "chown", "dd", "mkfs", "format"]
        cmd_parts = shlex.split(full_cmd)
        if cmd_parts and any(dangerous in cmd_parts[0] for dangerous in dangerous_commands):
            if not self.config.get("dangerous", False):
                console.print(
                    f"[yellow]⚠ Dangerous command detected. "
                    f"Use 'dangerous: true' in config to enable: {escape(full_cmd)}[/yellow]"
                )
                return "continue"

        try:
            # Capture output
            working_dir = self.config.get("working_dir", ".")
            timeout = self.config.get("timeout", 30)

            console.print(f"[cyan]Executing: {escape(full_cmd)}[/cyan]")

            result = subprocess.run(
                shlex.split(full_cmd),
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Display output
            if result.stdout:
                console.print(f"[green]{escape(result.stdout)}[/green]")
            if result.stderr and not result.stdout:
                console.print(f"[yellow]{escape(result.stderr)}[/yellow]")

            if result.returncode != 0:
                console.print(f"[red]Command exited with code {result.returncode}[/red]")

        except subprocess.TimeoutExpired:
            console.print(f"[red]✗ Command timed out after {timeout} seconds[/red]")
        except Exception as e:
            console.print(f"[red]✗ Command execution failed: {escape(str(e))}[/red]")

        return "continue"

    def _execute_text(self, args: str, console: Console) -> CommandResult:
        """Display predefined text."""
        text = self.config.get("text", f"Custom command: {self.name}")

        # Simple variable substitution
        variables = {
            "args": args.strip(),
            "cwd": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
        }

        # Replace {var} patterns
        for var, value in variables.items():
            text = text.replace(f"{{{var}}}", str(value))

        # Use rich markup if formatted is True
        if self.config.get("formatted", True):
            console.print(text)
        else:
            console.print(escape(text))

        return "continue"

    def _execute_template(self, args: str, agent: Any, console: Console) -> CommandResult:
        """Execute a template with more complex variable substitution."""
        template = self.config.get("template", f"Custom command: {self.name}")

        # Enhanced variable set
        variables = {
            "args": args.strip(),
            "cwd": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
            "model": getattr(agent, "model", "unknown"),
            "provider": getattr(agent, "provider_name", "unknown"),
            "message_count": len(getattr(agent, "conversation_history", [])),
        }

        # Format the template
        try:
            formatted_text = template.format(**variables)

            if self.config.get("formatted", True):
                console.print(formatted_text)
            else:
                console.print(escape(formatted_text))
        except KeyError as e:
            console.print(f"[red]✗ Template variable not found: {escape(str(e))}[/red]")

        return "continue"

    def _execute_function(self, args: str, agent: Any, console: Console) -> CommandResult:
        """Execute a Python function."""
        function_path = self.config.get("function", "")
        if not function_path:
            console.print(f"[red]✗ No function specified for '{self.name}'[/red]")
            return "continue"

        try:
            # Support module.function format
            if "." in function_path:
                module_name, func_name = function_path.rsplit(".", 1)
                module = __import__(module_name, fromlist=[func_name])
            else:
                # Try to import from current package
                module = __import__(__name__, fromlist=[function_path])
                func_name = function_path

            func = getattr(module, func_name)

            # Call the function with appropriate arguments
            if hasattr(func, "__code__") and func.__code__.co_argcount > 0:
                result = func(args=args, agent=agent, console=console)
            else:
                result = func()

            # If the function returns a CommandResult, use it
            if isinstance(result, str) and result in ["continue", "break", "run"]:
                return result  # type: ignore[return-value]

            # Otherwise, just display the result
            if result is not None:
                console.print(str(result))

        except Exception as e:
            console.print(f"[red]✗ Function execution failed: {escape(str(e))}[/red]")

        return "continue"


class CustomCommandManager:
    """Manages custom slash commands."""

    def __init__(self) -> None:
        self.commands: dict[str, CustomCommand] = {}
        self._load_commands()

    def _load_commands(self) -> None:
        """Load custom commands from configuration files (project + global)."""
        config_paths = self._get_config_paths()

        # Track if we found any config files
        found_any = False

        # Load from all paths (global first, then project to allow override)
        for config_path in reversed(config_paths):  # Reverse so project overrides global
            if not config_path.exists():
                continue

            found_any = True

            try:
                with open(config_path) as f:
                    config_data = json.load(f)

                commands_config = config_data.get("commands", {})

                for name, cmd_config in commands_config.items():
                    try:
                        self.commands[name] = CustomCommand(name, cmd_config)
                    except Exception as e:
                        msg = f"Warning: Failed to load '{name}' from {config_path}: {e}"
                        print(msg)

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse custom commands config at {config_path}: {e}")
            except Exception as e:
                print(f"Warning: Failed to load custom commands from {config_path}: {e}")

        # If no config files exist, create the global one
        if not found_any:
            global_path = self._get_global_config_path()
            self._create_example_config(global_path)

    def _get_config_paths(self) -> list[Path]:
        """Get paths to check for custom commands (project, then global)."""
        paths = []

        # Project-level config (current directory)
        project_path = Path.cwd() / ".clippy" / "custom_commands.json"
        paths.append(project_path)

        # Global config (home directory)
        global_path = self._get_global_config_path()
        paths.append(global_path)

        return paths

    def _get_global_config_path(self) -> Path:
        """Get the path to the global custom commands configuration file."""
        user_manager = get_user_manager()
        return user_manager.config_dir / "custom_commands.json"

    def _create_example_config(self, config_path: Path) -> None:
        """Create an empty configuration file."""
        empty_config: dict[str, Any] = {"commands": {}}

        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(empty_config, f, indent=2)
            print(f"Created empty custom commands config at: {config_path}")
            print("See docs/CUSTOM_COMMANDS.md for examples and documentation")
        except Exception as e:
            print(f"Warning: Failed to create config: {e}")

    def get_command(self, name: str) -> CustomCommand | None:
        """Get a custom command by name."""
        return self.commands.get(name)

    def list_commands(self) -> dict[str, CustomCommand]:
        """Get all custom commands."""
        return self.commands.copy()

    def reload_commands(self) -> None:
        """Reload custom commands from disk."""
        self.commands.clear()
        self._load_commands()

    def help_text(self) -> str:
        """Generate help text for custom commands."""
        if not self.commands:
            return ""

        help_parts = ["[bold]Custom Commands:[/bold]\n"]

        for name, cmd in sorted(self.commands.items()):
            if cmd.hidden:
                continue
            help_parts.append(f"  /{name} - {cmd.description}")

        return "\n".join(help_parts)


# Global instance
_custom_manager: CustomCommandManager | None = None


def get_custom_manager() -> CustomCommandManager:
    """Get the global custom command manager instance."""
    global _custom_manager
    if _custom_manager is None:
        _custom_manager = CustomCommandManager()
    return _custom_manager


def handle_custom_command(
    command_name: str, args: str, agent: Any, console: Console
) -> CommandResult | None:
    """Handle a custom command."""
    manager = get_custom_manager()
    custom_cmd = manager.get_command(command_name)

    if custom_cmd:
        return custom_cmd.execute(args, agent, console)

    return None


# Example function for custom commands
def show_session_stats(args: str, agent: Any, console: Console) -> CommandResult:
    """Example function that can be called from custom commands."""
    try:
        history = getattr(agent, "conversation_history", [])
        message_count = len(history)

        stats = f"""
📊 Session Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Messages: {message_count}
Model: {getattr(agent, "model", "unknown")}
Provider: {getattr(agent, "provider_name", "unknown")}
User: {os.getenv("USER", "unknown")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip()

        console.print(stats)
        return "continue"
    except Exception as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        return "continue"
