"""Enhanced CLI utilities for better user experience."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class EnhancedProgressManager:
    """Enhanced progress management with context-aware operations."""

    def __init__(self, console: Console):
        self.console = console
        self.operations = {
            "analyze": {
                "message": "Analyzing code...",
                "steps": ["Reading files", "Processing structure", "Generating insights"],
            },
            "refactor": {
                "message": "Refactoring code...",
                "steps": ["Understanding code", "Planning changes", "Applying refactorings"],
            },
            "generate": {
                "message": "Generating code...",
                "steps": ["Analyzing requirements", "Generating code", "Validating output"],
            },
            "create": {
                "message": "Creating files...",
                "steps": ["Planning structure", "Creating files", "Validating syntax"],
            },
            "build": {
                "message": "Building project...",
                "steps": ["Preparing build", "Compiling code", "Running tests"],
            },
        }
        self.default_operation = {
            "message": "Processing...",
            "steps": ["Initializing", "Processing", "Finalizing"],
        }

    def get_operation_progress(self, operation_type: str) -> dict[str, Any]:
        """Get progress configuration for operation type."""
        return self.operations.get(operation_type.lower(), self.default_operation)

    def start_enhanced_progress(
        self, operation_type: str = "default"
    ) -> tuple[Progress, list[str]]:
        """Start enhanced progress with operation-specific steps."""
        config = self.get_operation_progress(operation_type)

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            refresh_per_second=10,
        )

        progress.add_task(config["message"], total=len(config["steps"]))

        return progress, config["steps"]

    def show_operation_tip(self, operation_type: str) -> None:
        """Show helpful tip based on operation type."""
        tips = {
            "analyze": "💡 Tip: Use @filename.json to include config files in analysis",
            "refactor": "💡 Tip: Large refactorings may take time - use Ctrl+C to interrupt",
            "generate": "💡 Tip: Be specific in your requirements for better generated code",
            "create": "💡 Tip: File paths are created automatically - focus on structure",
            "build": "💡 Tip: Make sure you have all dependencies installed before building",
        }

        tip = tips.get(operation_type.lower())
        if tip:
            self.console.print(f"[dim]{tip}[/dim]")


class SmartErrorHandler:
    """Enhanced error handling with contextual suggestions."""

    def __init__(self, console: Console):
        self.console = console
        self.error_patterns = {
            "permission": {
                "patterns": ["permission", "denied", "access"],
                "suggestions": [
                    "Check if the file/directory exists and is accessible",
                    "Try running with elevated permissions if needed",
                    "Use /auto list to see auto-approved actions",
                ],
            },
            "network": {
                "patterns": ["network", "connection", "timeout", "unreachable"],
                "suggestions": [
                    "Check your internet connection",
                    "Verify API keys are set correctly",
                    "Try switching to a different model with /model",
                    "Some providers may be experiencing issues",
                ],
            },
            "model": {
                "patterns": ["model", "api", "authentication"],
                "suggestions": [
                    "Check if the model is available with /model list",
                    "Verify API key is set in environment variables",
                    "Try /model use <provider> <model> to test without saving",
                    "Use /providers to see available providers",
                ],
            },
            "file": {
                "patterns": ["file not found", "no such file", "directory"],
                "suggestions": [
                    "Check the file path and spelling",
                    "Use @filename with Tab completion for file references",
                    "Verify the file exists in the current directory or subdirectories",
                    "Use list_directory to explore available files",
                ],
            },
            "syntax": {
                "patterns": ["syntax", "parse", "invalid", "malformed"],
                "suggestions": [
                    "Check command syntax with /help",
                    "Verify all required arguments are provided",
                    "Use proper quoting for arguments with spaces",
                    "Check for missing or extra commas/brackets",
                ],
            },
        }

    def handle_error(self, error: Exception, context: str = "") -> tuple[str, list[str]]:
        """Handle an error and return formatted message and suggestions."""
        error_message = str(error)
        error_lower = error_message.lower()

        # Determine error type
        error_type = "general"
        for type_name, type_info in self.error_patterns.items():
            if any(pattern in error_lower for pattern in type_info["patterns"]):
                error_type = type_name
                break

        suggestions = self._get_suggestions(error_type)
        formatted_error = self._format_error(error, error_type)

        return formatted_error, suggestions

    def _get_suggestions(self, error_type: str) -> list[str]:
        """Get suggestions for error type."""
        base_suggestions = self.error_patterns.get(error_type, {}).get("suggestions", [])

        # Add general suggestions for all errors
        general_suggestions = [
            "Use /help to see available commands",
            "Check /status for current session information",
        ]

        return base_suggestions + general_suggestions

    def _format_error(self, error: Exception, error_type: str) -> str:
        """Format error message with type indicator."""
        error_message = str(error)

        # Add icons based on error type
        icons = {
            "permission": "🔒",
            "network": "🌐",
            "model": "🤖",
            "file": "📁",
            "syntax": "📝",
            "general": "⚠️",
        }

        icon = icons.get(error_type, "⚠️")
        return f"{icon} {error_message}"

    def display_error_info(self, error: Exception, context: str = "") -> None:
        """Display comprehensive error information with suggestions."""
        formatted_error, suggestions = self.handle_error(error, context)

        self.console.print(f"\n[bold red]{formatted_error}[/bold red]")

        if context:
            self.console.print(f"[dim]Context: {context}[/dim]")

        if suggestions:
            self.console.print("\n[yellow]💡 Suggestions to resolve:[/yellow]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"  [dim]{i}.[/dim] {suggestion}")

        self.console.print()


class CommandValidator:
    """Validate commands before execution to prevent common errors."""

    def __init__(self, console: Console):
        self.console = console

    def validate_model_command(self, args: list[str]) -> tuple[bool, str]:
        """Validate model command arguments."""
        if not args:
            return True, ""  # Help is shown for empty args

        subcommand = args[0].lower() if args else ""

        if subcommand == "add":
            if len(args) < 2:
                return False, "Missing provider name"
            if len(args) < 3:
                return False, "Missing model ID"

            # Validate provider exists
            from ..models import list_available_providers

            providers = [p[0] for p in list_available_providers()]
            if args[1] not in providers:
                return False, f"Unknown provider '{args[1]}'. Available: {', '.join(providers)}"

        elif subcommand in ["remove", "default", "threshold", "load"]:
            if len(args) < 2:
                return False, f"Missing model name for '{subcommand}' command"

        elif subcommand == "use":
            if len(args) < 2:
                return False, "Missing provider name"
            if len(args) < 3:
                return False, "Missing model ID"

        return True, ""

    def validate_mcp_command(self, args: list[str]) -> tuple[bool, str]:
        """Validate MCP command arguments."""
        if not args:
            return True, ""  # Help is shown for empty args

        subcommand = args[0].lower()

        if subcommand in ["allow", "revoke", "enable", "disable"]:
            if len(args) < 2:
                return False, f"Missing server name for '{subcommand}' command"

        return True, ""


def show_enhanced_help(console: Console) -> None:
    """Show enhanced help with better organization and examples."""
    help_content = (
        "[bold cyan]📎 clippy-code Enhanced Commands[/bold cyan]\n\n"
        "[bold green]Session Control:[/bold green]\n"
        "  /help              - Show this enhanced help message\n"
        "  /exit, /quit       - Exit clippy-code\n"
        "  /reset, /clear     - Reset conversation history\n"
        "  /resume [name]     - Resume saved conversation (interactive)\n\n"
        "[bold green]Session Info:[/bold green]\n"
        "  /status            - Show token usage and session info\n"
        "  /compact           - Summarize to reduce context usage\n\n"
        "[bold green]Model Management:[/bold green]\n"
        "  /model             - Show model management options\n"
        "  /model list        - List your saved models\n"
        "  /model <name>      - Switch to saved model\n"
        "  /model use <p> <m> - Try model without saving\n\n"
        "[bold green]Enhanced Features:[/bold green]\n"
        "  • Smart file completion with @filename<Tab>\n"
        "  • Context-aware error suggestions\n"
        "  • Progress indicators for long operations\n"
        "  • Auto-completion for all commands\n\n"
        "[dim]💡 Pro tip: Use Tab completion everywhere - it works smartly![/dim]"
    )

    console.print(Panel.fit(help_content, border_style="cyan"))
    console.print("[dim]For detailed command help, use specific commands like /model or /mcp[/dim]")


def format_success_message(message: str, operation: str = "") -> str:
    """Format success message with operation context."""
    icons = {
        "create": "✅",
        "delete": "🗑️",
        "update": "🔄",
        "switch": "🔀",
        "load": "📂",
        "save": "💾",
        "connect": "🔗",
        "disconnect": "🔌",
    }

    icon = icons.get(operation.lower(), "✅")
    return f"[green]{icon} {message}[/green]"


def format_warning_message(message: str) -> str:
    """Format warning message with consistent styling."""
    return f"[yellow]⚠️ {message}[/yellow]"


def format_info_message(message: str, context: str = "") -> str:
    """Format info message with optional context."""
    base = f"[dim]ℹ️ {message}[/dim]"
    if context:
        base += f" [dim]({context})[/dim]"
    return base
