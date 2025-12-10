"""First-time setup wizard for clippy-code."""

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..models import (
    UserModelManager,
    get_default_model_config,
    list_available_providers,
    reload_model_manager,
)


def should_run_setup() -> bool:
    """Determine if first-time setup should run.

    Returns:
        True if this appears to be first run (no user models configured)
    """
    models_file = Path.home() / ".clippy" / "models.json"

    # If models file doesn't exist, run setup
    if not models_file.exists():
        return True

    # if models file exists, check if it's empty
    if models_file.stat().st_size == 0:
        return True

    # Even if models file exists, check if there's a default model set
    # If no default is set, run setup to help user choose one
    try:
        from ..models import get_default_model_config

        default_model, default_provider = get_default_model_config()
        if not default_model or not default_provider:
            return True
    except Exception:
        # If there's any error checking defaults, run setup
        return True

    return False


def run_first_time_setup() -> None:
    """Run the first-time setup wizard for choosing a default provider."""
    console = Console()

    # Welcome message
    welcome_panel = Panel(
        "📎 Welcome to clippy-code! 👀\n\n"
        "It looks like you're setting up clippy-code for the first time.\n"
        "Let's choose your preferred AI provider to get started!",
        title="🚀 First-Time Setup",
        border_style="blue",
    )
    console.print(welcome_panel)
    console.print()

    # Get available providers
    providers = list_available_providers()

    if not providers:
        console.print("[bold red]Error: No providers available![/bold red]")
        console.print("This should never happen. Please check your installation.")
        raise SystemExit(1)

    # Create provider selection table
    table = Table(title="Available AI Providers")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Provider", style="green")
    table.add_column("Description", style="white")

    for i, (provider_name, description) in enumerate(providers, 1):
        table.add_row(str(i), provider_name, description)

    console.print(table)
    console.print()

    # Provider selection
    while True:
        try:
            choice = Prompt.ask(
                "Which provider would you like to use as your default?",
                choices=[str(i) for i in range(1, len(providers) + 1)],
                default="1",
            )
            provider_index = int(choice) - 1
            selected_provider, selected_description = providers[provider_index]
            break
        except (ValueError, IndexError):
            console.print("[red]Invalid choice. Please try again.[/red]")

    console.print(f"\n[green]✓ Selected provider: {selected_provider}[/green]")
    console.print(f"[dim]Description: {selected_description}[/dim]")
    console.print()

    # Check if API key is available
    provider_config = None
    from ..models import get_provider

    provider_config = get_provider(selected_provider)

    if provider_config and provider_config.api_key_env:
        api_key_env = provider_config.api_key_env
        api_key = os.getenv(api_key_env)

        if api_key:
            console.print(f"[green]✓ API key found in {api_key_env}[/green]")
        else:
            console.print(f"\n[yellow]⚠ API key not found in {api_key_env}[/yellow]")
            console.print("You'll need to set this after setup completes.")

            # Show instructions for setting the API key
            console.print("\n[dim]To set your API key, you can:[/dim]")
            console.print("  1. Create a .env file in your current directory:")
            console.print(f"     [cyan]echo '{api_key_env}=your_api_key_here' >> .env[/cyan]")
            console.print("  2. Create a .clippy.env file in your home directory:")
            console.print(
                f"     [cyan]echo '{api_key_env}=your_api_key_here' >> ~/.clippy/.env[/cyan]"
            )
            console.print("  3. Set the environment variable in your shell:")
            console.print(f"     [cyan]export {api_key_env}=your_api_key_here[/cyan]")
            console.print()

    # Model selection based on provider - using models.yaml data
    console.print("Now let's choose your model...")

    # Get models from the existing models.yaml infrastructure
    from ..models import list_models_by_source

    # Get all available models and filter by selected provider
    models_by_source = list_models_by_source()
    available_models = []

    # First get built-in models for this provider
    for model_name, description, provider in models_by_source["built_in"]:
        if provider == selected_provider:
            # Convert to tuple format: (model_name, description)
            available_models.append((model_name, description))

    # If no built-in models found for this provider, provide a generic option
    if not available_models:
        available_models.append(
            (f"{selected_provider}-default", f"Default model for {selected_provider}")
        )

    # Create model selection table
    model_table = Table(title="Available Models")
    model_table.add_column("No.", style="cyan", width=4)
    model_table.add_column("Model", style="green")
    model_table.add_column("Description", style="white")

    for i, (model_id, description) in enumerate(available_models, 1):
        model_table.add_row(str(i), model_id, description)

    console.print(model_table)
    console.print()

    # Model selection
    while True:
        try:
            model_choice = Prompt.ask(
                "Which model would you like to use?",
                choices=[str(i) for i in range(1, len(available_models) + 1)],
                default="1",
            )
            model_index = int(model_choice) - 1
            selected_model, selected_model_desc = available_models[model_index]
            break
        except (ValueError, IndexError):
            console.print("[red]Invalid choice. Please try again.[/red]")

    console.print(f"\n[green]✓ Selected model: {selected_model}[/green]")
    console.print(f"[dim]Description: {selected_model_desc}[/dim]")
    console.print()

    # Confirm and save configuration
    confirm = Confirm.ask(
        f"Set [bold]{selected_provider}/{selected_model}[/bold] as your default configuration?",
        default=True,
    )

    if confirm:
        user_manager = UserModelManager()

        # The selected_model is now the actual model name from models.yaml
        # We need to determine if it's a built-in model to get the correct model_id
        model_name = selected_model
        model_id = selected_model

        # Check if this is a built-in model and get its actual model_id
        from ..models import is_builtin_model

        if is_builtin_model(model_name):
            # Try to get the model data from the current user manager to get the real model_id
            existing_model = user_manager.get_model(model_name)
            if existing_model:
                model_id = existing_model.model_id
            else:
                # If it's a built-in model but not yet loaded, we'll create it with the same name
                # The YAML loading will handle getting the correct model_id
                pass

        # Add the new model as default
        success, message = user_manager.add_model(
            name=model_name,
            provider=selected_provider,
            model_id=model_id,
            is_default=True,
        )

        if success:
            console.print("\n[green]✓ Configuration saved successfully![/green]")
            console.print(f"Your default model is now: [bold]{model_name}[/bold]")

            # Reload model manager to ensure changes take effect
            reload_model_manager()

            # Verify the configuration
            default_model, default_provider = get_default_model_config()
            if default_model and default_provider:
                console.print("\n[green]✓ Setup complete![/green]")
                console.print("You're ready to start using clippy-code! 📎👀")
            else:
                console.print("\n[red]⚠ Configuration saved but verification failed[/red]")
                console.print("Please try restarting clippy-code.")
        else:
            console.print(f"\n[red]Error saving configuration: {message}[/red]")
    else:
        console.print(
            "\n[yellow]Setup cancelled. You can configure your provider later using:[/yellow]"
        )
        console.print("[cyan]clippy-code /model add[/cyan]")
