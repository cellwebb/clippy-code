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

    # Model selection based on provider
    console.print("Now let's choose your model...")

    # Predefined models for each provider
    provider_models = {
        "openai": [
            ("gpt-4o", "GPT-4o - OpenAI's latest model"),
            ("gpt-4o-mini", "GPT-4o Mini - Fast and cost-effective"),
            ("gpt-4-turbo", "GPT-4 Turbo - Powerful model"),
        ],
        "anthropic": [
            ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (latest)"),
            ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet (previous)"),
            ("claude-3-opus-20240229", "Claude 3 Opus - Most capable"),
            ("claude-3-sonnet-20240229", "Claude 3 Sonnet - Balanced"),
            ("claude-3-haiku-20240307", "Claude 3 Haiku - Fastest"),
        ],
        "cerebras": [
            ("llama-3.1-70b", "Llama 3.1 70B"),
            ("llama-3.1-8b", "Llama 3.1 8B"),
        ],
        "gemini": [
            ("gemini-1.5-pro", "Gemini 1.5 Pro"),
            ("gemini-1.5-flash", "Gemini 1.5 Flash"),
        ],
        "openrouter": [
            ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet via OpenRouter"),
            ("openai/gpt-4o", "GPT-4o via OpenRouter"),
            ("meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B via OpenRouter"),
        ],
        "ollama": [
            ("llama3.1:8b", "Llama 3.1 8B (local)"),
            ("llama3.1:70b", "Llama 3.1 70B (local)"),
            ("codellama:13b", "Code Llama 13B (local)"),
        ],
        "lmstudio": [
            ("local-model", "Local Model (specify in LM Studio)"),
        ],
        "synthetic": [
            ("gpt-4o", "GPT-4o via Synthetic.new"),
            ("gpt-4-turbo", "GPT-4 Turbo via Synthetic.new"),
        ],
        "zai": [
            ("claude-3-5-sonnet", "Claude 3.5 Sonnet via Z.AI"),
        ],
        "claude-code": [
            ("claude-3-5-sonnet", "Claude 3.5 Sonnet via Claude Code"),
        ],
    }

    # Get models for selected provider or provide generic options
    available_models = provider_models.get(
        selected_provider,
        [
            ("default", "Default model for " + selected_provider),
        ],
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

        # Add the new model as default
        success, message = user_manager.add_model(
            name=f"{selected_provider}-{selected_model}",
            provider=selected_provider,
            model_id=selected_model,
            is_default=True,
        )

        if success:
            console.print("\n[green]✓ Configuration saved successfully![/green]")
            console.print(
                f"Your default model is now: [bold]{selected_provider}/{selected_model}[/bold]"
            )

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
