"""Interactive REPL mode for CLI."""

import logging
import threading
import time
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.status import Status

from ..agent import ClippyAgent, InterruptedExceptionError
from .commands import handle_command
from .completion import create_completer


class ProgressIndicator:
    """Enhanced progress indicator for long-running operations."""

    def __init__(self, console: Console):
        self.console = console
        self.status: Status | None = None
        self.live: Live | None = None
        self.progress: Progress | None = None
        self.task_id: Any | None = None
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_spinner: int = 0
        self.start_time: float | None = None
        self.active: bool = False

    def start_simple_spinner(self, message: str = "Processing...") -> None:
        """Start a simple spinner with message."""
        self.active = True
        self.status = Status(
            f"[cyan]{self.spinner_chars[self.current_spinner]}[/cyan] {message}",
            console=self.console,
        )
        self.start_time = time.time()

        def update_spinner() -> None:
            while self.active:
                self.current_spinner = (self.current_spinner + 1) % len(self.spinner_chars)
                if self.start_time is not None and self.status is not None:
                    elapsed = time.time() - self.start_time
                    self.status.update(
                        f"[cyan]{self.spinner_chars[self.current_spinner]}[/cyan] {message} "
                        f"[dim]({elapsed:.1f}s)[/dim]"
                    )
                time.sleep(0.1)

        self.thread = threading.Thread(target=update_spinner, daemon=True)
        self.thread.start()
        self.status.start()

    def start_progress_bar(self, message: str = "Processing...", total_steps: int = 100) -> None:
        """Start a progress bar for multi-step operations."""
        self.active = True
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self.task_id = self.progress.add_task(message, total=total_steps)
        self.live = Live(self.progress, console=self.console, refresh_per_second=10)
        self.live.start()

    def update_progress(self, advance: int = 1, message: str | None = None) -> None:
        """Update progress bar."""
        if self.progress and self.task_id:
            self.progress.advance(self.task_id, advance)
            if message:
                self.progress.update(self.task_id, description=message)

    def stop(self, final_message: str | None = None) -> None:
        """Stop the progress indicator."""
        self.active = False
        if self.status:
            self.status.stop()
            self.status = None
        if self.live:
            self.live.stop()
            self.live = None
            self.progress = None
            self.task_id = None
        if final_message:
            self.console.print(f"[green]✓[/green] {final_message}")


class ErrorRecoveryHelper:
    """Helper class for error recovery and suggestions."""

    def __init__(self, console: Console):
        self.console = console

    def suggest_fixes(self, error_message: str, context: str | None = None) -> None:
        """Suggest potential fixes based on common error patterns."""
        suggestions = []

        # Common error patterns and suggestions
        error_lower = error_message.lower()

        if "permission" in error_lower or "denied" in error_lower:
            suggestions.extend(
                [
                    "Try running with sudo if you need elevated permissions",
                    "Check if the file/directory exists and is accessible",
                    "Use /auto list to see auto-approved actions",
                ]
            )

        if "file not found" in error_lower or "no such file" in error_lower:
            suggestions.extend(
                [
                    "Check the file path and spelling",
                    "Use @filename with Tab completion for file references",
                    "Verify the file exists in the current directory or subdirectories",
                ]
            )

        if "network" in error_lower or "connection" in error_lower or "timeout" in error_lower:
            suggestions.extend(
                [
                    "Check your internet connection",
                    "Verify API keys are set correctly",
                    "Try switching to a different model with /model",
                    "Use /providers to check provider status",
                ]
            )

        if "model" in error_lower or "api" in error_lower:
            suggestions.extend(
                [
                    "Check if the model is available with /model list",
                    "Verify API key is set in environment",
                    "Try a different provider with /model use <provider> <model>",
                ]
            )

        if "syntax" in error_lower or "parse" in error_lower:
            suggestions.extend(
                [
                    "Check command syntax with /help",
                    "Verify all required arguments are provided",
                    "Use proper quoting for arguments with spaces",
                ]
            )

        if suggestions:
            self.console.print("\n[yellow]💡 Suggestions:[/yellow]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"  [dim]{i}.[/dim] {suggestion}")
            self.console.print()

        # Show context-specific help
        if context:
            self.console.print(f"[dim]Context: {context}[/dim]")


def run_interactive(agent: ClippyAgent, auto_approve: bool) -> None:
    """Run clippy-code in interactive mode (REPL)."""
    console = Console()
    progress_indicator = ProgressIndicator(console)
    error_helper = ErrorRecoveryHelper(console)

    # Create key bindings for double-ESC detection
    kb = KeyBindings()
    last_esc_time = {"time": 0.0}
    esc_timeout = 0.5  # 500ms window for double-ESC

    @kb.add("escape")
    def _(event: Any) -> None:
        """Handle ESC key press - double-ESC to abort."""
        current_time = time.time()
        time_diff = current_time - last_esc_time["time"]

        if time_diff < esc_timeout:
            # Double-ESC detected - raise KeyboardInterrupt
            event.app.exit(exception=KeyboardInterrupt())
        else:
            # First ESC - just record the time
            last_esc_time["time"] = current_time

    # Create history file
    history_file = Path.home() / ".clippy_history"
    session: PromptSession[str] = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        key_bindings=kb,
        completer=create_completer(agent),
    )

    # Get current model and provider info
    current_model = agent.model
    if agent.base_url and agent.base_url != "https://api.openai.com/v1":
        provider_info = f" ({agent.base_url})"
    else:
        provider_info = " (OpenAI)"

    console.print(
        Panel.fit(
            "[bold green]clippy-code Interactive Mode (Enhanced)[/bold green]\n\n"
            "Commands:\n"
            "  /exit, /quit - Exit clippy-code\n"
            "  /reset, /clear, /new - Reset conversation history (not in tab completion)\n"
            "  /resume [name] - Resume a saved conversation (interactive if no name)\n"
            "  /status - Show token usage and session info\n"
            "  /compact - Summarize conversation to reduce context usage\n"
            "  /providers - List available providers\n"
            "  /provider <name> - Show provider details\n"
            "  /model list - Show your saved models\n"
            "  /model <name> - Switch to saved model\n"
            "  /model load <name> - Load model (same as direct switch)\n"
            "  /model add <provider> <model_id> [options] - Add a new model\n"
            "  /model remove <name> - Remove a saved model\n"
            "  /model default <name> - Set model as default\n"
            "  /model use <provider> <model_id> - Try a model without saving\n"
            "  /auto list - List auto-approved actions\n"
            "  /auto revoke <action> - Revoke auto-approval for an action\n"
            "  /auto clear - Clear all auto-approvals\n"
            "  /mcp list - List configured MCP servers\n"
            "  /mcp tools [server] - List tools available from MCP servers\n"
            "  /mcp refresh - Refresh tool catalogs from MCP servers\n"
            "  /mcp allow <server> - Mark an MCP server as trusted for this session\n"
            "  /mcp revoke <server> - Revoke trust for an MCP server\n"
            "  /mcp enable <server> - Enable a disabled MCP server\n"
            "  /mcp disable <server> - Disable an enabled MCP server\n"
            "  /help - Show this help message\n\n"
            "Enhanced Features:\n"
            "  📎 File completion: Type @filename and press Tab\n"
            "  🔄 Progress indicators: Automatic for long operations\n"
            "  💡 Error suggestions: Context-aware help when things go wrong\n\n"
            f"[cyan]Current Model:[/cyan] [bold]{current_model}[/bold]{provider_info}\n\n"
            "Type your request and press Enter.\n"
            "Use Ctrl+C or double-ESC to interrupt execution.",
            border_style="green",
        )
    )

    while True:
        try:
            # Get user input
            user_input = session.prompt("\n[You] ➜ ").strip()

            if not user_input:
                continue

            # Handle commands
            result = handle_command(user_input, agent, console)
            if result == "break":
                break
            elif result == "continue":
                continue

            # Run the agent with user input - with enhanced progress handling
            try:
                # Start progress indicator for long-running operations
                if len(user_input) > 100 or any(
                    keyword in user_input.lower()
                    for keyword in ["analyze", "refactor", "generate", "create", "build"]
                ):
                    progress_indicator.start_simple_spinner("Processing your request...")

                agent.run(user_input, auto_approve_all=auto_approve)

                # Stop progress indicator with success message
                if progress_indicator.active:
                    progress_indicator.stop("Request completed successfully")

            except InterruptedExceptionError:
                console.print(
                    "\n[yellow]Execution interrupted. You can continue with a new request.[/yellow]"
                )
                if progress_indicator.active:
                    progress_indicator.stop("Execution interrupted")
                continue
            except Exception as e:
                console.print(f"\n[bold red]Error: {escape(str(e))}[/bold red]")
                context = user_input[:50] + "..." if len(user_input) > 50 else user_input
                error_helper.suggest_fixes(str(e), context)
                if progress_indicator.active:
                    progress_indicator.stop("Execution failed")
                continue

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /exit or /quit to exit clippy-code[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error: {escape(str(e))}[/bold red]")
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unexpected error in interactive mode: {type(e).__name__}: {e}", exc_info=True
            )
            error_helper.suggest_fixes(str(e))
            console.print("[dim]Please report this error with the above details.[/dim]")
            continue
