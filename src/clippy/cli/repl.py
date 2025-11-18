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
from rich.markup import escape
from rich.panel import Panel

from ..agent import ClippyAgent, InterruptedExceptionError
from .commands import handle_command
from .completion import create_completer


def _suggest_similar_commands(command: str) -> list[str]:
    """
    Suggest similar commands for a given invalid command.

    Args:
        command: The invalid command string

    Returns:
        List of suggested valid commands
    """
    from difflib import get_close_matches

    # Extract command name (first word after /)
    parts = command.strip().split()
    if not parts:
        return []

    invalid_cmd = parts[0][1:].lower()  # Remove leading / and lowercase

    # List of valid commands
    valid_commands = [
        "help",
        "exit",
        "quit",
        "reset",
        "clear",
        "new",
        "resume",
        "status",
        "compact",
        "providers",
        "provider",
        "model",
        "subagent",
        "auto",
        "mcp",
        "truncate",
        "yolo",
    ]

    # Find close matches using fuzzy matching
    suggestions = get_close_matches(invalid_cmd, valid_commands, n=3, cutoff=0.6)

    # Format suggestions with leading /
    return [f"/{suggestion}" for suggestion in suggestions]


def run_interactive(agent: ClippyAgent, auto_approve: bool) -> None:
    """Run clippy-code in interactive mode (REPL)."""
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
        completer=create_completer(agent),
    )

    # Get current model and provider info
    current_model = agent.model
    if agent.base_url and agent.base_url != "https://api.openai.com/v1":
        provider_info = f" ({agent.base_url})"
    else:
        provider_info = " (OpenAI)"

    # Check if YOLO mode is active and add visual indicator
    yolo_indicator = ""
    if getattr(agent, "yolo_mode", False):
        yolo_indicator = (
            "\n[bold red]🔥 YOLO MODE IS ACTIVE - ALL ACTIONS AUTO-APPROVED! 🔥[/bold red]\n"
        )
        border_style = "red"
    else:
        border_style = "green"

    # ASCII Art for Clippy - the paperclip assistant!
    clippy_ascii = """[dim]
 ________  ___       ___  ________  ________  ___    ___ 
|\\   ____\\|\\  \\     |\\  \\|\\   __  \\|\\   __  \\|\\  \\  /  /|
\\ \\  \\___|\\ \\  \\    \\ \\  \\ \\  \\|\\  \\ \\  \\|\\  \\ \\  \\/  / /
 \\ \\  \\    \\ \\  \\    \\ \\  \\ \\   ____\\ \\   ____\\ \\    / / 
  \\ \\  \\____\\ \\  \\____\\ \\  \\ \\  \\___|\\ \\  \\___|\\/  /  /  
   \\ \\_______\\ \\_______\\ \\__\\ \\__\\    \\ \\__\\ __/  / /    
    \\|_______|\\|_______|\\|__|\\|__|     \\|__||\\___/ /     
                                            \\|___|/      
                                                         
                                                         [/dim]
[📎] It looks like you're trying to code!"""

    console.print(
        Panel.fit(
            f"{clippy_ascii}\n\n"
            "[bold green]clippy-code Interactive Mode[/bold green]\n\n"
            "Just type your request and press Enter to chat with Clippy!\n\n"
            "[bold]Essential Commands:[/bold]\n"
            "  /help - Show all available commands\n"
            "  /model - Show and switch between models\n"
            "  /exit, /quit - Exit clippy-code\n"
            "  /reset, /clear, /new - Start fresh conversation\n\n"
            "[bold]Tips:[/bold]\n"
            "  • Use Ctrl+C or double-ESC to stop any action\n"
            "  • Clippy will ask for permission before risky actions\n"
            "  • Type @filename and press Tab for file completion\n\n"
            f"[bold]Current Model:[/bold] [cyan]{current_model}[/cyan]{provider_info}",
            border_style=border_style,
        )
    )

    # Show YOLO mode indicator if active
    if yolo_indicator:
        console.print(yolo_indicator)

    while True:
        try:
            # Get user input with YOLO mode indicator in prompt
            prompt_text = "\n[You] ➜ "
            if getattr(agent, "yolo_mode", False):
                prompt_text = "\n[🔥 YOLO You] ➜ "

            user_input = session.prompt(prompt_text).strip()

            if not user_input:
                continue

            # Handle commands
            result = handle_command(user_input, agent, console)
            if result == "break":
                break
            elif result == "continue":
                continue
            elif result is None and user_input.startswith("/"):
                # Unrecognized slash command - show error instead of sending to LLM
                console.print(f"[red]✗ Unknown command: {user_input}[/red]")

                # Try to suggest similar commands
                command_suggestions = _suggest_similar_commands(user_input)
                if command_suggestions:
                    console.print(f"[dim]Did you mean: {', '.join(command_suggestions)}?[/dim]")

                console.print("[dim]Type /help to see available commands[/dim]")
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
            console.print("[dim]Please report this error with the above details.[/dim]")
            continue
