"""Command-line interface for CLIppy."""

import sys
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .permissions import PermissionManager, PermissionConfig
from .executor import ActionExecutor
from .agent import ClippyAgent, InterruptedException


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
        description="CLIppy - A CLI coding agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="The task or question for CLIppy (one-shot mode)",
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start in interactive mode (REPL)",
    )

    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Auto-approve all actions (use with caution!)",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Claude model to use (default: claude-3-5-sonnet-20241022)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom permission config file",
    )

    return parser


def run_one_shot(agent: ClippyAgent, prompt: str, auto_approve: bool):
    """Run CLIppy in one-shot mode."""
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
    """Run CLIppy in interactive mode (REPL)."""
    console = Console()

    # Create history file
    history_file = Path.home() / ".clippy_history"
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
    )

    console.print(Panel.fit(
        "[bold green]CLIppy Interactive Mode[/bold green]\n\n"
        "Commands:\n"
        "  /exit, /quit - Exit CLIppy\n"
        "  /reset - Reset conversation history\n"
        "  /help - Show this help message\n\n"
        "Type your request and press Enter. Use Ctrl+C to interrupt execution.",
        border_style="green"
    ))

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
                console.print(Panel.fit(
                    "[bold]Commands:[/bold]\n"
                    "  /exit, /quit - Exit CLIppy\n"
                    "  /reset - Reset conversation history\n"
                    "  /help - Show this help message",
                    border_style="blue"
                ))
                continue

            # Run the agent
            try:
                agent.run(user_input, auto_approve_all=auto_approve)
            except InterruptedException:
                console.print("\n[yellow]Execution interrupted. You can continue with a new request.[/yellow]")
                continue

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /exit or /quit to exit CLIppy[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]")
            continue


def main():
    """Main entry point for CLIppy."""
    # Load environment variables
    load_env()

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console = Console()
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not found in environment.\n\n"
            "Please set your API key:\n"
            "  1. Create a .env file in the current directory, or\n"
            "  2. Create a .clippy.env file in your home directory, or\n"
            "  3. Set the ANTHROPIC_API_KEY environment variable\n\n"
            "Example .env file:\n"
            "  ANTHROPIC_API_KEY=your_api_key_here"
        )
        sys.exit(1)

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

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
        model=args.model,
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
