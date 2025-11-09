"""Main entry point for clippy-code CLI."""

import os
import sys

from rich.console import Console
from rich.markup import escape

from ..agent import ClippyAgent
from ..executor import ActionExecutor
from ..mcp.config import load_config
from ..mcp.manager import Manager
from ..models import ProviderConfig, get_default_model_config, get_model_config
from ..permissions import PermissionConfig, PermissionManager
from .oneshot import run_one_shot
from .parser import create_parser
from .repl import run_interactive
from .setup import load_env, setup_logging


def _is_openai_compatible(provider: ProviderConfig | None) -> bool:
    """Return True if the provider uses the OpenAI-compatible API surface."""

    if provider is None:
        return False
    system = provider.pydantic_system
    return system in (None, "openai")


def resolve_model(
    model_input: str | None,
) -> tuple[str | None, str | None, str | None, ProviderConfig | None]:
    """Resolve a model input to (model_id, base_url, api_key_env, provider).

    Args:
        model_input: User model name, raw model ID, or None for default

    Returns:
        Tuple of (model_id, base_url, api_key_env, provider_config)
        Returns (None, None, None, None) if model_input is None
    """
    if model_input is None:
        return None, None, None, None

    user_model, provider = get_model_config(model_input)
    if user_model:
        model_id = user_model.model_id
        if provider and _is_openai_compatible(provider):
            base_url = provider.base_url
        else:
            base_url = None
        api_key_env = provider.api_key_env if provider else None

        if provider and not _is_openai_compatible(provider):
            system = provider.pydantic_system or provider.name
            model_id = f"{system}:{model_id}"

        return model_id, base_url, api_key_env, provider

    return model_input, None, None, None


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
    (
        resolved_model,
        resolved_base_url,
        resolved_api_key_env,
        resolved_provider,
    ) = resolve_model(args.model)

    # Use resolved values if available, otherwise use defaults
    base_url: str | None = None
    if resolved_model:
        # User specified a model (either name or raw ID)
        model = resolved_model
        if resolved_provider:
            if _is_openai_compatible(resolved_provider):
                if resolved_base_url is not None:
                    base_url = resolved_base_url
                elif args.base_url:
                    base_url = args.base_url
                else:
                    base_url = resolved_provider.base_url or default_provider.base_url
            else:
                base_url = None
        elif resolved_base_url is not None:
            base_url = resolved_base_url
        elif args.base_url:
            base_url = args.base_url
        elif ":" in model:
            base_url = None
        else:
            base_url = default_provider.base_url
        # Use resolved api_key_env if available, otherwise use default
        api_key_env = resolved_api_key_env if resolved_api_key_env else default_provider.api_key_env
        if resolved_provider:
            provider_config_to_use = resolved_provider
        elif ":" in model:
            provider_config_to_use = None
        else:
            provider_config_to_use = default_provider
    else:
        # No model specified, use defaults
        model = default_model.model_id
        base_url = args.base_url if args.base_url else default_provider.base_url
        api_key_env = default_provider.api_key_env
        provider_config_to_use = default_provider

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
        provider_config=provider_config_to_use,
        mcp_manager=mcp_manager,
    )

    # Determine mode
    if args.prompt:
        # One-shot mode - user provided a prompt
        prompt = " ".join(args.prompt)
        # Handle --yolo flag (overrides --yes)
        auto_approve_all = args.yolo or args.yes
        if args.yolo:
            # Set yolo mode on agent for one-shot mode
            agent.yolo_mode = True
            console.print(
                "[bold red]🔥 YOLO MODE ENABLED - All actions will be auto-approved! 🔥[/bold red]"
            )
        run_one_shot(agent, prompt, auto_approve_all)
    else:
        # Interactive mode - no prompt provided, start REPL
        # Handle --yolo flag (overrides --yes)
        auto_approve = args.yolo or args.yes
        if args.yolo:
            # Set yolo mode on agent for interactive mode
            agent.yolo_mode = True
        run_interactive(agent, auto_approve)


if __name__ == "__main__":
    main()
