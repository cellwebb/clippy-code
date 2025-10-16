"""Command-line interface for clippy-code."""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.panel import Panel

from .agent import ClippyAgent, InterruptedExceptionError
from .executor import ActionExecutor
from .models import get_model_config, list_available_models
from .permissions import PermissionConfig, PermissionManager


def load_env() -> None:
    """Load environment variables from .env file."""
    # Check current directory first
    if Path(".env").exists():
        load_dotenv(".env")
    # Then check home directory
    elif Path.home().joinpath(".clippy.env").exists():
        load_dotenv(Path.home() / ".clippy.env")


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.WARNING

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    # Set library loggers to WARNING to reduce noise
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="clippy-code - A CLI coding agent powered by OpenAI-compatible LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="The task or question for clippy-code (one-shot mode)",
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Start in interactive mode (REPL)",
    )

    parser.add_argument(
        "-d",
        "--document",
        action="store_true",
        help="Start in document mode (Word-like TUI interface)",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Auto-approve all actions (use with caution!)",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (e.g., gpt-5, llama3.1-8b for Cerebras)",
    )

    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for OpenAI-compatible API (e.g., https://api.cerebras.ai/v1)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom permission config file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (shows retry attempts and API errors)",
    )

    return parser


def run_one_shot(agent: ClippyAgent, prompt: str, auto_approve: bool) -> None:
    """Run clippy-code in one-shot mode."""
    console = Console()

    try:
        agent.run(prompt, auto_approve_all=auto_approve)
    except InterruptedExceptionError:
        console.print("\n[yellow]Execution interrupted[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        sys.exit(1)


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
    )

    console.print(
        Panel.fit(
            "[bold green]clippy-code Interactive Mode[/bold green]\n\n"
            "Commands:\n"
            "  /exit, /quit - Exit clippy-code\n"
            "  /reset, /clear, /new - Reset conversation history\n"
            "  /status - Show token usage and session info\n"
            "  /compact - Summarize conversation to reduce context usage\n"
            "  /model list - Show available models\n"
            "  /model <name> - Switch model/provider\n"
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
            if user_input.lower() in ["/exit", "/quit"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif user_input.lower() in ["/reset", "/clear", "/new"]:
                agent.reset_conversation()
                console.print("[green]Conversation history reset[/green]")
                continue
            elif user_input.lower() == "/help":
                console.print(
                    Panel.fit(
                        "[bold]Commands:[/bold]\n"
                        "  /exit, /quit - Exit clippy-code\n"
                        "  /reset, /clear, /new - Reset conversation history\n"
                        "  /status - Show token usage and session info\n"
                        "  /compact - Summarize conversation to reduce context usage\n"
                        "  /model list - Show available model presets\n"
                        "  /model <name> - Switch to a preset model\n"
                        "  /help - Show this help message\n\n"
                        "[bold]Interrupt:[/bold]\n"
                        "  Ctrl+C or double-ESC - Stop current execution",
                        border_style="blue",
                    )
                )
                continue
            elif user_input.lower() == "/status":
                # Show session status and token usage
                status = agent.get_token_count()

                if "error" in status:
                    console.print(
                        Panel.fit(
                            f"[bold red]Error counting tokens:[/bold red]\n{status['error']}\n\n"
                            f"[bold]Session Info:[/bold]\n"
                            f"  Model: {status['model']}\n"
                            f"  Provider: {status.get('base_url') or 'OpenAI'}\n"
                            f"  Messages: {status['message_count']}",
                            title="Status",
                            border_style="yellow",
                        )
                    )
                else:
                    provider = status.get("base_url") or "OpenAI"
                    usage_bar_length = 20
                    usage_filled = int((status["usage_percent"] / 100) * usage_bar_length)
                    usage_bar = "█" * usage_filled + "░" * (usage_bar_length - usage_filled)

                    usage_pct = f"{status['usage_percent']:.1f}%"

                    # Build message breakdown
                    message_info = []
                    if status["system_messages"] > 0:
                        msg = (
                            f"System: {status['system_messages']} msgs, "
                            f"{status['system_tokens']:,} tokens"
                        )
                        message_info.append(msg)
                    if status["user_messages"] > 0:
                        msg = (
                            f"User: {status['user_messages']} msgs, "
                            f"{status['user_tokens']:,} tokens"
                        )
                        message_info.append(msg)
                    if status["assistant_messages"] > 0:
                        msg = (
                            f"Assistant: {status['assistant_messages']} msgs, "
                            f"{status['assistant_tokens']:,} tokens"
                        )
                        message_info.append(msg)
                    if status["tool_messages"] > 0:
                        msg = (
                            f"Tool: {status['tool_messages']} msgs, "
                            f"{status['tool_tokens']:,} tokens"
                        )
                        message_info.append(msg)

                    message_breakdown = (
                        "\n    ".join(message_info) if message_info else "No messages yet"
                    )

                    console.print(
                        Panel.fit(
                            f"[bold]Current Session:[/bold]\n"
                            f"  Model: [cyan]{status['model']}[/cyan]\n"
                            f"  Provider: [cyan]{provider}[/cyan]\n"
                            f"  Messages: [cyan]{status['message_count']}[/cyan]\n\n"
                            f"[bold]Token Usage:[/bold]\n"
                            f"  Context: [cyan]{status['total_tokens']:,}[/cyan] tokens\n"
                            f"  Usage: [{usage_bar}] [cyan]{usage_pct}[/cyan]\n\n"
                            f"[bold]Message Breakdown:[/bold]\n"
                            f"    {message_breakdown}\n\n"
                            f"[dim]Note: Usage % is estimated for ~128k context window[/dim]",
                            title="Session Status",
                            border_style="cyan",
                        )
                    )
                continue
            elif user_input.lower() == "/compact":
                # Compact conversation history
                console.print("[cyan]Compacting conversation...[/cyan]")

                success, message, stats = agent.compact_conversation()

                if success:
                    console.print(
                        Panel.fit(
                            f"[bold green]✓ Conversation Compacted[/bold green]\n\n"
                            f"[bold]Token Reduction:[/bold]\n"
                            f"  Before: [cyan]{stats['before_tokens']:,}[/cyan] tokens\n"
                            f"  After: [cyan]{stats['after_tokens']:,}[/cyan] tokens\n"
                            f"  Saved: [green]{stats['tokens_saved']:,}[/green] tokens "
                            f"([green]{stats['reduction_percent']:.1f}%[/green])\n\n"
                            f"[bold]Messages:[/bold]\n"
                            f"  Before: [cyan]{stats['messages_before']}[/cyan] messages\n"
                            f"  After: [cyan]{stats['messages_after']}[/cyan] messages\n"
                            f"  Summarized: "
                            f"[cyan]{stats['messages_summarized']}[/cyan] messages\n\n"
                            f"[dim]The conversation history has been condensed while "
                            f"preserving recent context.[/dim]",
                            title="Compact Complete",
                            border_style="green",
                        )
                    )
                else:
                    console.print(
                        Panel.fit(
                            f"[bold yellow]⚠ Cannot Compact[/bold yellow]\n\n{message}",
                            title="Compact",
                            border_style="yellow",
                        )
                    )
                continue
            elif user_input.lower().startswith("/model"):
                # Handle model switching
                parts = user_input.split(maxsplit=1)
                if len(parts) == 1 or parts[1].lower() == "list":
                    # Show available models
                    models = list_available_models()
                    model_list = "\n".join(
                        f"  [cyan]{name:20}[/cyan] - {desc}" for name, desc in models
                    )
                    current_model = agent.model
                    current_provider = agent.base_url or "OpenAI"
                    console.print(
                        Panel.fit(
                            f"[bold]Available Model Presets:[/bold]\n\n{model_list}\n\n"
                            f"[bold]Current:[/bold] {current_model} ({current_provider})\n\n"
                            f"[dim]Usage: /model <name>[/dim]",
                            title="Models",
                            border_style="cyan",
                        )
                    )
                else:
                    # Switch to specified model
                    model_name = parts[1].strip()
                    config = get_model_config(model_name)

                    if config:
                        # Use preset configuration
                        # Load API key from environment variable specified in config
                        api_key = os.getenv(config.api_key_env)

                        if not api_key:
                            console.print(
                                f"[yellow]⚠ Warning: {config.api_key_env} not set in "
                                f"environment[/yellow]\n"
                                f"[dim]The model may fail if it requires authentication.[/dim]"
                            )
                            # Continue anyway - some providers like Ollama might not need a key
                            api_key = "not-set"

                        success, message = agent.switch_model(
                            model=config.model_id, base_url=config.base_url, api_key=api_key
                        )
                    else:
                        # Treat as custom model ID (keep current base_url and api_key)
                        success, message = agent.switch_model(model=model_name)

                    if success:
                        console.print(f"[green]✓ {message}[/green]")
                    else:
                        console.print(f"[red]✗ {message}[/red]")
                continue

            # Run the agent
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
            console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
            logger = logging.getLogger(__name__)
            logger.error(
                f"Unexpected error in interactive mode: {type(e).__name__}: {e}", exc_info=True
            )
            console.print("[dim]Please report this error with the above details.[/dim]")
            continue


def main() -> None:
    """Main entry point for clippy-code."""
    # Load environment variables
    load_env()

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Get API key (required)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console = Console()
        console.print(
            "[bold red]Error:[/bold red] OPENAI_API_KEY not found in environment.\n\n"
            "Please set your API key:\n"
            "  1. Create a .env file in the current directory, or\n"
            "  2. Create a .clippy.env file in your home directory, or\n"
            "  3. Set the OPENAI_API_KEY environment variable\n\n"
            "Example .env file:\n"
            "  OPENAI_API_KEY=your_api_key_here\n"
            "  OPENAI_BASE_URL=https://api.cerebras.ai/v1  # Optional, for alternate providers\n"
            "  CLIPPY_MODEL=llama3.1-8b  # Optional, specify model"
        )
        sys.exit(1)

    # Create permission manager
    permission_manager = PermissionManager(PermissionConfig())

    # TODO: Load custom config if provided
    # if args.config:
    #     permission_manager = load_config(args.config)

    # Create executor and agent
    executor = ActionExecutor(permission_manager)
    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key=api_key,
        model=args.model,
        base_url=args.base_url or os.getenv("OPENAI_BASE_URL"),
    )

    # Determine mode
    if args.document:
        # Document mode (Word-like TUI)
        from .document_ui import run_document_mode

        run_document_mode(agent, args.yes)
    elif args.interactive or not args.prompt:
        # Interactive mode
        run_interactive(agent, args.yes)
    else:
        # One-shot mode
        prompt = " ".join(args.prompt)
        run_one_shot(agent, prompt, args.yes)


if __name__ == "__main__":
    main()
