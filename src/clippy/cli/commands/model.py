"""Model management command handlers for interactive CLI mode."""

from typing import Literal

from rich.console import Console
from rich.panel import Panel

from ...agent import ClippyAgent
from ...models import (
    get_model_config,
    get_provider,
    get_user_manager,
    list_available_models_with_provider,
    reload_model_manager,
)

CommandResult = Literal["continue", "break", "run"]


# Model management functions
def handle_model_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /model commands."""
    if not command_args or not command_args.strip():
        return _handle_model_help(console)

    parts = command_args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()

    if subcommand == "help":
        return _handle_model_help(console)
    elif subcommand == "list":
        return _handle_model_list(console)
    elif subcommand == "add":
        if len(parts) < 2:
            console.print(
                "[red]Usage: /model add <provider> <model_id> [--name <display_name>][/red]"
            )
            return "continue"
        return _handle_model_add(agent, console, parts[1])
    elif subcommand == "remove":
        if len(parts) < 2:
            console.print("[red]Usage: /model remove <name>[/red]")
            return "continue"
        return _handle_model_remove(console, parts[1])
    elif subcommand == "set-default":
        if len(parts) < 2:
            console.print("[red]Usage: /model set-default <name>[/red]")
            return "continue"
        return _handle_model_set_default(console, parts[1])
    elif subcommand == "threshold":
        if len(parts) < 3:
            console.print("[red]Usage: /model threshold <name> <threshold>[/red]")
            return "continue"
        return _handle_model_threshold(console, parts[1], parts[2])
    elif subcommand == "switch":
        if len(parts) < 2:
            console.print("[red]Usage: /model switch <name>[/red]")
            return "continue"
        return _handle_model_switch(agent, console, parts[1])
    elif subcommand == "use":
        if len(parts) < 2:
            console.print("[red]Usage: /model use <provider> <model_id>[/red]")
            return "continue"
        return _handle_model_use(agent, console, parts[1])
    elif subcommand == "reload":
        reload_model_manager()
        console.print("[green]✓ Model manager reloaded[/green]")
        return "continue"
    else:
        console.print(f"[red]✗ Unknown model subcommand: {subcommand}[/red]")
        console.print("[dim]Use /model help for available commands[/dim]")
        return "continue"


def _handle_model_help(console: Console) -> CommandResult:
    """Display help for model commands."""
    help_text = """
[bold cyan]/model commands:[/bold cyan]

  [cyan]/model[/cyan]                     - Show this help
  [cyan]/model list[/cyan]                - List available models
  [cyan]/model add <provider> <model_id> [--name <display_name>][/cyan]
                                  - Add a new model
  [cyan]/model remove <name>[/cyan]       - Remove a model
  [cyan]/model set-default <name>[/cyan]  - Set default model
  [cyan]/model threshold <name> <n>[/cyan] - Set model switch threshold
  [cyan]/model switch <name>[/cyan]       - Switch to a model
  [cyan]/model use <provider> <model_id>[/cyan] - Temporarily use a model
  [cyan]/model reload[/cyan]              - Reload model manager

[dim]Use /providers to see available providers[/dim]
"""
    console.print(Panel.fit(help_text.strip(), title="Model Help", border_style="cyan"))
    return "continue"


def _handle_model_list(console: Console) -> CommandResult:
    """List available models."""
    models = list_available_models_with_provider()

    if not models:
        console.print("[yellow]No models available[/yellow]")
        console.print("[dim]Use /model add to add a model[/dim]")
        return "continue"

    # Get current model info
    current_model = None
    try:
        user_manager = get_user_manager()
        current_model = user_manager.get_default_model()
    except Exception:
        pass  # Current model info not available

    # Group models by provider
    models_by_provider: dict[str, list[tuple[str, str, bool, int | None, str]]] = {}
    for model in models:
        # model[4] is the provider name from the tuple
        # (name, description, is_default, compaction_threshold, provider)
        provider = model[4]
        if provider not in models_by_provider:
            models_by_provider[provider] = []
        models_by_provider[provider].append(model)

    # Display models
    for provider, provider_models in sorted(models_by_provider.items()):
        console.print(f"\n[bold cyan]Provider: {provider}[/bold cyan]")

        for model in sorted(provider_models, key=lambda m: m[0]):  # m[0] is the name
            status_indicators = []
            if current_model and model[0] == current_model.name:
                status_indicators.append("[green]✓ CURRENT[/green]")
            if model[2]:  # model[2] is is_default
                status_indicators.append("[blue]★ DEFAULT[/blue]")

            status = " ".join(status_indicators) if status_indicators else ""
            if model[3] is not None and model[3] != -1:  # model[3] is compaction_threshold
                threshold_info = f" [dim]({model[3]})[/dim]"
            else:
                threshold_info = ""

            console.print(f"  [cyan]{model[0]:20}[/cyan]{threshold_info} {status}")

    console.print("\n[dim]Use /model switch <name> to switch models[/dim]")
    return "continue"


def _handle_model_add(agent: ClippyAgent, console: Console, args: str) -> CommandResult:
    """Add a new model."""
    import shlex

    try:
        parts = shlex.split(args)
    except ValueError:
        console.print("[red]✗ Error parsing arguments. Use quotes for model IDs with spaces.[/red]")
        return "continue"

    if len(parts) < 2:
        console.print("[red]Usage: /model add <provider> <model_id> [--name <display_name>][/red]")
        return "continue"

    provider = parts[0]
    model_id = parts[1]

    # Parse optional name flag
    display_name = None
    if len(parts) >= 4 and parts[2] == "--name":
        display_name = parts[3]

    # Verify provider exists
    provider_obj = get_provider(provider)
    if not provider_obj:
        console.print(f"[red]✗ Unknown provider: {provider}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    # Add the model
    user_manager = get_user_manager()
    model_name = display_name or model_id
    success, message = user_manager.add_model(model_name, provider, model_id, False, None)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        # Reload model manager to pick up the new model
        reload_model_manager()
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_model_remove(console: Console, name: str) -> CommandResult:
    """Remove a model."""
    user_manager = get_user_manager()
    success, message = user_manager.remove_model(name)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        # Reload model manager to update the available models list
        reload_model_manager()
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_model_set_default(console: Console, name: str) -> CommandResult:
    """Set the default model."""
    user_manager = get_user_manager()
    success, message = user_manager.set_default(name)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        # Reload model manager to update the default model
        reload_model_manager()
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_model_threshold(console: Console, name: str, threshold_str: str) -> CommandResult:
    """Set model compaction threshold."""
    try:
        threshold = int(threshold_str)
        if threshold < -1:
            raise ValueError("Threshold must be -1 or greater")
    except ValueError as e:
        console.print(f"[red]✗ Invalid threshold: {e}[/red]")
        return "continue"

    user_manager = get_user_manager()
    compaction_threshold = threshold if threshold != -1 else None
    success, message = user_manager.set_compaction_threshold(name, compaction_threshold)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        reload_model_manager()
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_model_switch(agent: ClippyAgent, console: Console, name: str) -> CommandResult:
    """Switch to a model."""
    user_manager = get_user_manager()
    success, message = user_manager.switch_model(name)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        # Get the model configuration and update the agent
        model_config, provider_config = get_model_config(name)
        if model_config and provider_config:
            success, msg = agent.switch_model(
                model=model_config.model_id,
                base_url=provider_config.base_url,
                provider_config=provider_config,
            )
            if not success:
                console.print(
                    f"[yellow]⚠ Model switched in config but failed to update agent: {msg}[/yellow]"
                )
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_model_use(agent: ClippyAgent, console: Console, args: str) -> CommandResult:
    """Temporarily use a model without saving it."""
    parts = args.strip().split(maxsplit=1)
    if len(parts) < 2:
        console.print("[red]Usage: /model use <provider> <model_id>[/red]")
        return "continue"

    provider = parts[0]
    model_id = parts[1]

    # Verify provider exists
    provider_obj = get_provider(provider)
    if not provider_obj:
        console.print(f"[red]✗ Unknown provider: {provider}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    # Switch to the temporary model
    provider_obj = get_provider(provider)
    if provider_obj is None:
        console.print(f"[red]✗ Unknown provider: {provider}[/red]")
        return "continue"

    success, message = agent.switch_model(
        model=model_id,
        base_url=provider_obj.base_url,
        provider_config=provider_obj,
    )

    if success:
        console.print(f"[green]✓ {message}[/green]")
        console.print("[dim](Use /model add to save this model permanently)[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"
