"""One-shot mode for CLI."""

import sys

from rich.console import Console
from rich.markup import escape

from ..agent import ClippyAgent, InterruptedExceptionError


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
        console.print(f"\n[bold red]Error: {escape(str(e))}[/bold red]")
        sys.exit(1)
