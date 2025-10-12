"""Command-line interface for clippy-code."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel

from .agent import ClippyAgent, InterruptedException
from .executor import ActionExecutor
from .permissions import PermissionConfig, PermissionManager


def load_env():
    """Load environment variables from .env file."""
    # Check current directory first
    if Path(".env").exists():
        load_dotenv(".env")
    # Then check home directory
    elif Path.home().joinpath(".clippy.env").exists():
        load_dotenv(Path.home() / ".clippy.env")


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
        "-y",
        "--yes",
        action="store_true",
        help="Auto-approve all actions (use with caution!)",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (e.g., gpt-4o, llama3.1-8b for Cerebras)",
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

    return parser


def run_one_shot(agent: ClippyAgent, prompt: str, auto_approve: bool):
    """Run clippy-code in one-shot mode."""
    console = Console()

    try:
        agent.run(prompt, auto_approve_all=auto_approve)
    except InterruptedException:
        console.print("\n[yellow]Execution interrupted[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        sys.exit(1)


def run_interactive(agent: ClippyAgent, auto_approve: bool):
    """Run clippy-code in interactive mode (REPL)."""
    console = Console()

    # Create history file
    history_file = Path.home() / ".clippy_history"
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
    )

    console.print(
        Panel.fit(
            "[bold green]clippy-code Interactive Mode[/bold green]\n\n"
            "Commands:\n"
            "  /exit, /quit - Exit clippy-code\n"
            "  /reset - Reset conversation history\n"
            "  /help - Show this help message\n\n"
            "Type your request and press Enter. Use Ctrl+C to interrupt execution.",
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
            elif user_input.lower() == "/reset":
                agent.reset_conversation()
                console.print("[green]Conversation history reset[/green]")
                continue
            elif user_input.lower() == "/help":
                console.print(
                    Panel.fit(
                        "[bold]Commands:[/bold]\n"
                        "  /exit, /quit - Exit clippy-code\n"
                        "  /reset - Reset conversation history\n"
                        "  /help - Show this help message",
                        border_style="blue",
                    )
                )
                continue

            # Run the agent
            try:
                agent.run(user_input, auto_approve_all=auto_approve)
            except InterruptedException:
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
            console.print(f"\n[bold red]Error: {e}[/bold red]")
            continue


def main():
    """Main entry point for clippy-code."""
    # Load environment variables
    load_env()

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

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
    if args.interactive or not args.prompt:
        # Interactive mode
        run_interactive(agent, args.yes)
    else:
        # One-shot mode
        prompt = " ".join(args.prompt)
        run_one_shot(agent, prompt, args.yes)


if __name__ == "__main__":
    main()
