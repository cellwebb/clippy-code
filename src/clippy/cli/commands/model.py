"""Model management command handlers for interactive CLI mode."""

from typing import Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...agent import ClippyAgent
from ...models import (
    get_model_config,
    get_provider,
    get_user_manager,
    list_available_models_with_provider,
    list_available_providers,
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
        # Check if there are arguments
        if len(parts) < 2:
            return _handle_model_add(agent, console, "")  # Launch wizard
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
        if len(parts) < 2:
            console.print("[red]Usage: /model threshold <name> <threshold>[/red]")
            return "continue"
        # parts[1] contains "<name> <threshold>", need to split further
        threshold_parts = parts[1].strip().split(maxsplit=1)
        if len(threshold_parts) < 2:
            console.print("[red]Usage: /model threshold <name> <threshold>[/red]")
            return "continue"
        return _handle_model_threshold(console, threshold_parts[0], threshold_parts[1])
    elif subcommand == "switch":
        if len(parts) < 2:
            console.print("[red]Usage: /model switch <name>[/red]")
            return "continue"
        return _handle_model_switch(agent, console, parts[1])
    elif subcommand == "reload":
        reload_model_manager()
        console.print("[green]✓ Model manager reloaded[/green]")
        return "continue"
    else:
        # Treat unknown subcommand as a model name to switch to
        # This makes "/model <name>" work the same as "/model switch <name>"
        return _handle_model_switch(agent, console, subcommand)


def _handle_model_help(console: Console) -> CommandResult:
    """Display help for model commands."""
    help_text = """
[bold cyan]/model commands:[/bold cyan]

  [cyan]/model[/cyan]                     - Show this help
  [cyan]/model list[/cyan]                - List available models
  [cyan]/model <name>[/cyan]              - Switch to a model (shortcut for /model switch)
  [cyan]/model switch <name>[/cyan]       - Switch to a model (current session only)
  [cyan]/model set-default <name>[/cyan]  - Set default model (permanent)
  [cyan]/model add[/cyan]                 - Add a new model (interactive wizard)
  [cyan]/model add <provider> <model_id> [--name <display_name>][/cyan]
                                  - Add a new model (direct arguments)
  [cyan]/model remove <name>[/cyan]       - Remove a model
  [cyan]/model threshold <name> <n>[/cyan] - Set model compaction threshold
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

    # Create a table with rich formatting
    table = Table(
        title="Available Models",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold green",
    )

    # Add columns
    table.add_column("Model Name", style="cyan", width=25)
    table.add_column("Provider", style="green", width=15)
    table.add_column("Threshold", style="yellow", width=12, justify="right")
    table.add_column("Status", style="magenta", width=25)

    # Sort models by provider, then by name
    sorted_models = sorted(models, key=lambda m: (m[4], m[0]))  # m[4] is provider, m[0] is name

    # Add rows to the table
    for model in sorted_models:
        name, description, is_default, compaction_threshold, provider = model

        # Format threshold
        if compaction_threshold is not None and compaction_threshold != -1:
            threshold_str = f"{compaction_threshold:,}"
        else:
            threshold_str = "—"

        # Determine status
        status_parts = []
        if is_default:
            status_parts.append("[bold blue]★ DEFAULT[/bold blue]")
        if current_model and name == current_model.name:
            status_parts.append("[bold green]✓ CURRENT[/bold green]")

        status = " ".join(status_parts) if status_parts else ""

        # Add row to table
        table.add_row(name, provider, threshold_str, status)

    # Wrap the table in a panel for better visual appeal
    panel = Panel(
        table,
        title="📊 Model Configuration",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(panel)

    # Add helpful information below
    console.print("\n[dim]Legend:[/dim]")
    console.print("  [bold blue]★ DEFAULT[/bold blue] - Default model (permanent)")
    console.print("  [bold green]✓ CURRENT[/bold green] - Currently active model (session only)")
    console.print("  [dim]—[/dim] - No compaction threshold set")
    console.print("\n[dim]Commands:[/dim]")
    console.print("  [cyan]/model switch <name>[/cyan] - Switch to a model (current session only)")
    console.print("  [cyan]/model set-default <name>[/cyan] - Set a model as default (permanent)")
    console.print("  [cyan]/model threshold <name> <n>[/cyan] - Set model compaction threshold")

    return "continue"


def _handle_model_add(agent: ClippyAgent, console: Console, args: str) -> CommandResult:
    """Add a new model with interactive wizard."""
    # Check if using legacy argument-based mode
    if args and args.strip() and not args.strip().startswith("--wizard"):
        return _handle_model_add_legacy(agent, console, args.strip())

    # Interactive wizard mode
    return _handle_model_add_wizard(agent, console)


def _handle_model_add_legacy(agent: ClippyAgent, console: Console, args: str) -> CommandResult:
    """Handle legacy argument-based model addition."""
    import shlex

    try:
        parts = shlex.split(args)
    except ValueError:
        console.print("[red]✗ Error parsing arguments. Use quotes for model IDs with spaces.[/red]")
        console.print("[dim]Use /model add --wizard for interactive mode[/dim]")
        return "continue"

    if len(parts) < 2:
        console.print("[red]Usage: /model add <provider> <model_id> [--name <display_name>][/red]")
        console.print("[dim]Use /model add --wizard for interactive mode[/dim]")
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


def _handle_model_add_wizard(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /model add command with interactive wizard."""
    console.print("[cyan]🛠️ Model Configuration Wizard[/cyan]")
    console.print(
        "[dim]This wizard will help you add a new model from an available provider.[/dim]\n"
    )

    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        console.print(
            "[dim]Alternatively, use: /model add <provider> <model_id> "
            "[--name <display_name>][/dim]"
        )
        return "continue"

    # Step 1: Select provider
    providers = list_available_providers()
    if not providers:
        console.print("[red]❌ No providers available[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    provider_choices = [
        questionary.Choice(f"{name} - {desc}", value=name) for name, desc in providers
    ]
    provider_choices.append(questionary.Choice("Cancel", value="cancel"))

    console.print("[bold]Step 1/5: Select Provider[/bold]")
    console.print("[dim]Choose which provider this model belongs to:[/dim]\n")

    provider_name = questionary.select(
        "Select a provider:",
        choices=provider_choices,
        default=provider_choices[0].value if provider_choices else "cancel",
    ).ask()

    if provider_name == "cancel" or not provider_name:
        console.print("[yellow]Model configuration cancelled.[/yellow]")
        return "continue"

    # Get provider details for examples
    provider = get_provider(provider_name)
    if not provider:
        console.print(f"[red]✗ Provider '{provider_name}' not found[/red]")
        return "continue"

    # Step 2: Get model ID with examples
    console.print("\n[bold]Step 2/5: Model ID[/bold]")
    console.print(f"[dim]Enter the model ID for {provider_name}:[/dim]")

    # Show provider-specific examples
    examples = _get_model_examples(provider_name, provider.base_url)
    if examples:
        console.print("[dim]Common examples:[/dim]")
        for example in examples:
            console.print(f"[dim]  • {example}[/dim]")

    model_id = questionary.text(
        "Enter the model ID (exact identifier used by the provider)",
        validate=lambda text: len(text.strip()) > 0 or "Model ID cannot be empty",
    ).ask()

    if not model_id:
        console.print("[yellow]Model configuration cancelled.[/yellow]")
        return "continue"

    model_id = model_id.strip()

    # Step 3: Display name
    console.print("\n[bold]Step 3/5: Display Name[/bold]")
    console.print("[dim]Choose a display name for this model (for easier identification):[/dim]\n")

    display_name = questionary.text(
        "Enter a display name (optional, press Enter to use model ID)",
        default=model_id,
    ).ask()

    if not display_name:
        display_name = model_id
    display_name = display_name.strip()

    # Check if model name already exists
    user_manager = get_user_manager()
    existing_model = user_manager.get_model(display_name)
    if existing_model:
        overwrite = questionary.confirm(
            f"A model named '{display_name}' already exists. Do you want to use a different name?",
            default=True,
        ).ask()
        if overwrite:
            # Let them enter a new name
            new_name = questionary.text(
                "Enter a different display name",
                validate=lambda text: (len(text.strip()) > 0 and text.strip() != display_name)
                or "Please enter a different name",
            ).ask()
            if not new_name:
                console.print("[yellow]Model configuration cancelled.[/yellow]")
                return "continue"
            display_name = new_name.strip()
        else:
            console.print("[yellow]Model configuration cancelled.[/yellow]")
            return "continue"

    # Step 4: Default model setting
    console.print("\n[bold]Step 4/5: Default Model[/bold]")
    console.print("[dim]Would you like to set this as your default model?[/dim]\n")

    set_as_default = questionary.confirm(
        "Set this model as the default?",
        default=False,
    ).ask()

    # Step 5: Compaction threshold
    console.print("\n[bold]Step 5/5: Compaction Threshold[/bold]")
    console.print("[dim]Set a token limit for automatic conversation compaction (optional):[/dim]")

    threshold_choice = questionary.select(
        "Choose compaction behavior:",
        choices=[
            questionary.Choice("No automatic compaction", value=None),
            questionary.Choice("50,000 tokens", value=50000),
            questionary.Choice("100,000 tokens", value=100000),
            questionary.Choice("200,000 tokens", value=200000),
            questionary.Choice("Custom threshold", value="custom"),
        ],
        default=None,
    ).ask()

    compaction_threshold = None
    if threshold_choice == "custom":
        threshold_input = questionary.text(
            "Enter custom threshold (number of tokens)",
            validate=lambda text: (text.isdigit() and int(text) > 0)
            or "Please enter a positive number",
        ).ask()
        if threshold_input:
            compaction_threshold = int(threshold_input)
    elif threshold_choice:
        compaction_threshold = threshold_choice

    # Step 6: Confirmation
    console.print("\n[bold]📋 Configuration Summary:[/bold]")
    console.print(f"  Provider: [cyan]{provider_name}[/cyan]")
    console.print(f"  Model ID: [cyan]{model_id}[/cyan]")
    console.print(f"  Display Name: [cyan]{display_name}[/cyan]")
    console.print(f"  Default Model: [cyan]{'Yes' if set_as_default else 'No'}[/cyan]")
    if compaction_threshold:
        console.print(f"  Compaction Threshold: [cyan]{compaction_threshold:,} tokens[/cyan]")
    else:
        console.print("  Compaction Threshold: [cyan]Disabled[/cyan]")

    confirm = questionary.confirm(
        "Do you want to save this model configuration?",
        default=True,
    ).ask()

    if not confirm:
        console.print("[yellow]Model configuration cancelled.[/yellow]")
        return "continue"

    # Save the model configuration
    success, message = user_manager.add_model(
        name=display_name,
        provider=provider_name,
        model_id=model_id,
        is_default=set_as_default,
        compaction_threshold=compaction_threshold,
    )

    if success:
        console.print(f"[green]✓ {message}[/green]")
        # Reload model manager to pick up the new model
        reload_model_manager()

        # Offer to switch to the new model
        if not set_as_default:
            switch_now = questionary.confirm(
                f"Would you like to switch to '{display_name}' now?",
                default=True,
            ).ask()
            if switch_now:
                # Update the agent directly without setting as default
                model_config, provider_config = get_model_config(display_name)
                if model_config and provider_config:
                    success, msg = agent.switch_model(
                        model=model_config.model_id,
                        base_url=provider_config.base_url,
                        provider_config=provider_config,
                    )
                    if success:
                        console.print(
                            f"[green]✓ Switched to model '{display_name}' "
                            f"(current session only)[/green]"
                        )
                        console.print(
                            f"[dim]Use '/model set-default {display_name}' "
                            f"to make it your default model[/dim]"
                        )
                    else:
                        console.print(f"[red]✗ Failed to switch model: {msg}[/red]")
                else:
                    console.print(
                        f"[red]✗ Could not load configuration for model '{display_name}'[/red]"
                    )
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _get_model_examples(provider_name: str, base_url: str | None) -> list[str]:
    """Get example model IDs for a provider."""
    examples = []

    # Provider-specific examples based on common models
    if provider_name == "openai":
        examples.extend(
            [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
            ]
        )
    elif provider_name == "anthropic" or "anthropic" in provider_name.lower():
        examples.extend(
            [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
            ]
        )
    elif provider_name == "cerebras":
        examples.extend(
            [
                "llama3.1-70b",
                "llama3.1-8b",
            ]
        )
    elif provider_name == "groq":
        examples.extend(
            [
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
            ]
        )
    elif provider_name == "together":
        examples.extend(
            [
                "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                "mistralai/Mixtral-8x7B-Instruct-v0.1",
            ]
        )
    elif provider_name == "deepseek":
        examples.extend(
            [
                "deepseek-chat",
                "deepseek-coder",
            ]
        )
    elif provider_name == "ollama":
        examples.extend(
            [
                "llama3.1:70b",
                "llama3.1:8b",
                "codellama:13b",
            ]
        )
    else:
        # Generic examples for unknown providers
        examples.extend(
            [
                "gpt-4",  # OpenAI-style
                "claude-3-sonnet",  # Anthropic-style
                "llama-3-70b",  # Open-source style
            ]
        )

    return examples


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
    """Switch to a model for the current session only."""
    user_manager = get_user_manager()
    model = user_manager.get_model(name)

    if not model:
        console.print(f"[red]✗ Model '{name}' not found[/red]")
        return "continue"

    # Get the model configuration and update the agent
    model_config, provider_config = get_model_config(name)
    if model_config and provider_config:
        success, msg = agent.switch_model(
            model=model_config.model_id,
            base_url=provider_config.base_url,
            provider_config=provider_config,
        )
        if success:
            console.print(f"[green]✓ Switched to model '{name}' (current session only)[/green]")
            console.print(
                f"[dim]Use '/model set-default {name}' to make it your default model[/dim]"
            )
        else:
            console.print(f"[red]✗ Failed to switch model: {msg}[/red]")
    else:
        console.print(f"[red]✗ Could not load configuration for model '{name}'[/red]")

    return "continue"
