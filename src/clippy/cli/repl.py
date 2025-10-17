"""Interactive REPL mode for CLI."""

import logging
import time
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.panel import Panel

from ..agent import ClippyAgent, InterruptedExceptionError
from .commands import handle_command


def run_interactive(agent: ClippyAgent, auto_approve: bool) -> None:
    """Run code-with-clippy in interactive mode (REPL)."""
    console = Console()

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
    )

    console.print(
        Panel.fit(
            "[bold green]code-with-clippy Interactive Mode[/bold green]\n\n"
            "Commands:\n"
            "  /exit, /quit - Exit code-with-clippy\n"
            "  /reset, /clear, /new - Reset conversation history\n"
            "  /status - Show token usage and session info\n"
            "  /compact - Summarize conversation to reduce context usage\n"
            "  /model list - Show available models\n"
            "  /model <name> - Switch model/provider\n"
            "  /auto list - List auto-approved actions\n"
            "  /auto revoke <action> - Revoke auto-approval\n"
            "  /auto clear - Clear all auto-approvals\n"
            "  /help - Show this help message\n\n"
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

            # Run the agent with user input
            try:
                agent.run(user_input, auto_approve_all=auto_approve)
            except InterruptedExceptionError:
                console.print(
                    "\n[yellow]Execution interrupted. You can continue with a new request.[/yellow]"
                )
                continue

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /exit or /quit to exit code-with-clippy[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unexpected error in interactive mode: {type(e).__name__}: {e}", exc_info=True
            )
            console.print("[dim]Please report this error with the above details.[/dim]")
            continue
