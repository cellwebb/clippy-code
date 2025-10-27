"""Main entry point for clippy-code CLI."""

import os
import sys

from rich.console import Console
from rich.markup import escape

from ..agent import ClippyAgent
from ..executor import ActionExecutor
from ..mcp.config import load_config
from ..mcp.manager import Manager
from ..models import get_default_model_config, get_model_config
from ..permissions import PermissionConfig, PermissionManager
from .oneshot import run_one_shot
from .parser import create_parser
from .repl import run_interactive
from .setup import load_env, setup_logging


def resolve_model(
    model_input: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Resolve a model input to (model_id, base_url, api_key_env).

    Args:
        model_input: User model name, raw model ID, or None for default

    Returns:
        Tuple of (model_id, base_url, api_key_env)
        Returns (None, None, None) if model_input is None
    """
    if model_input is None:
        return None, None, None

    # Try to look up as a user model name first
    user_model, provider = get_model_config(model_input)
    if user_model and provider:
        return user_model.model_id, provider.base_url, provider.api_key_env

    # If not found in user models, treat as a raw model ID
    # In this case, we need to use the default provider settings
    return model_input, None, None


def main() -> None:
    """Main entry point for clippy-code."""
    # Load environment variables
    load_env()

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Suppress asyncio cleanup errors that occur during shutdown
    # These are caused by MCP async contexts that can't be cleanly closed across event loops
    import logging

    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.setLevel(logging.CRITICAL)

    # Get default model configuration
    default_model, default_provider = get_default_model_config()

    if not default_model or not default_provider:
        console = Console()
        console.print("[bold red]Error:[/bold red] No default model configuration found.")
        console.print("This should never happen - GPT-5 should be set as default.")
        sys.exit(1)

    # Resolve model input (handles user model names and raw model IDs)
    resolved_model, resolved_base_url, resolved_api_key_env = resolve_model(args.model)

    # Use resolved values if available, otherwise use defaults
    if resolved_model:
        # User specified a model (either name or raw ID)
        model = resolved_model
        # Use resolved base_url if available, otherwise check for --base-url, otherwise use default
        base_url = (
            resolved_base_url
            if resolved_base_url
            else (args.base_url if args.base_url else default_provider.base_url)
        )
        # Use resolved api_key_env if available, otherwise use default
        api_key_env = resolved_api_key_env if resolved_api_key_env else default_provider.api_key_env
    else:
        # No model specified, use defaults
        model = default_model.model_id
        base_url = args.base_url if args.base_url else default_provider.base_url
        api_key_env = default_provider.api_key_env

    # Get API key from environment
    api_key = os.getenv(api_key_env)

    if not api_key:
        console = Console()
        console.print(
            f"[bold red]Error:[/bold red] {api_key_env} not found in environment.\n\n"
            "Please set your API key:\n"
            "  1. Create a .env file in the current directory, or\n"
            "  2. Create a .clippy.env file in your home directory, or\n"
            "  3. Set the environment variable\n\n"
            f"Example .env file:\n"
            f"  {api_key_env}=your_api_key_here\n"
            "  OPENAI_BASE_URL=https://api.cerebras.ai/v1  # Optional, for alternate providers\n"
        )
        sys.exit(1)

    # Load MCP configuration
    mcp_config = load_config()

    # Create MCP manager if config is available
    mcp_manager = None
    console = Console()
    if mcp_config:
        try:
            mcp_manager = Manager(config=mcp_config, console=console)
            mcp_manager.start()  # Now synchronous - runs in background thread
        except Exception as e:
            console.print(
                f"[yellow]⚠ Warning: Failed to initialize MCP manager: {escape(str(e))}[/yellow]"
            )
            mcp_manager = None

    # Create permission manager
    permission_manager = PermissionManager(PermissionConfig())

    # Create executor and agent
    executor = ActionExecutor(permission_manager)
    if mcp_manager:
        executor.set_mcp_manager(mcp_manager)

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key=api_key,
        model=model,
        base_url=base_url,
        mcp_manager=mcp_manager,
    )

    # Determine mode
    if args.prompt:
        # One-shot mode - user provided a prompt
        prompt = " ".join(args.prompt)
        run_one_shot(agent, prompt, args.yes)
    else:
        # Interactive mode - no prompt provided, start REPL
        run_interactive(agent, args.yes)


if __name__ == "__main__":
    main()
