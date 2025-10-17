"""Main entry point for code-with-clippy CLI."""

import os
import sys

from rich.console import Console

from ..agent import ClippyAgent
from ..executor import ActionExecutor
from ..permissions import PermissionConfig, PermissionManager
from .oneshot import run_one_shot
from .parser import create_parser
from .repl import run_interactive
from .setup import load_env, setup_logging


def main() -> None:
    """Main entry point for code-with-clippy."""
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
        from ..ui import run_document_mode

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
