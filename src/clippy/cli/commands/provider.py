"""Provider management command handlers for interactive CLI mode."""

import os
from typing import Any, Literal

from rich.console import Console
from rich.panel import Panel

from ...models import (
    get_provider,
    list_providers_by_source,
)

CommandResult = Literal["continue", "break", "run"]


def handle_providers_command(console: Console) -> CommandResult:
    """Handle /providers command."""
    providers_by_source = list_providers_by_source()
    built_in = providers_by_source["built_in"]
    user = providers_by_source["user"]

    if not built_in and not user:
        console.print("[yellow]No providers available[/yellow]")
        return "continue"

    # Build the display
    content_parts = []

    if built_in:
        built_in_list = "\n".join(f"  [cyan]{name:12}[/cyan] - {desc}" for name, desc in built_in)
        content_parts.append(f"[bold]Built-in Providers:[/bold]\n\n{built_in_list}")

    if user:
        user_list = "\n".join(
            f"  [cyan]{name:12}[/cyan] - {desc} [green](User)[/green]" for name, desc in user
        )
        content_parts.append(f"[bold]User-defined Providers:[/bold]\n\n{user_list}")

    usage_text = (
        "\n\n[dim]Usage: /model add <provider> <model_id>[/dim]\n"
        "[dim]       /provider remove <name> (for user providers)[/dim]"
    )
    content = "\n\n".join(content_parts) + usage_text

    console.print(
        Panel.fit(
            content,
            title="Providers",
            border_style="cyan",
        )
    )
    return "continue"


def handle_provider_command(agent: Any, console: Console, command_args: str) -> CommandResult:
    """Handle /provider commands."""
    if not command_args:
        console.print("[red]Usage: /provider <command> [args][/red]")
        console.print("[dim]Commands: list, add, remove, <name>[/dim]")
        return "continue"

    parts = command_args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()

    if subcommand == "add":
        return _handle_provider_add(console)
    elif subcommand == "remove":
        if len(parts) < 2:
            console.print("[red]Usage: /provider remove <name>[/red]")
            return "continue"
        provider_name = parts[1]
        return _handle_provider_remove(console, provider_name)
    elif subcommand == "list":
        return handle_providers_command(console)
    else:
        # Treat as provider name to show details
        provider_name = subcommand
        return _handle_provider_details(console, provider_name)


def _handle_provider_details(console: Console, provider_name: str) -> CommandResult:
    """Handle /provider <name> command."""
    provider = get_provider(provider_name)

    if not provider:
        console.print(f"[red]✗ Unknown provider: {provider_name}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    api_key = os.getenv(provider.api_key_env, "")
    api_key_status = "[green]✓ Set[/green]" if api_key else "[yellow]⚠ Not set[/yellow]"

    # Check if this is a user-defined provider
    from ...models import is_user_provider

    is_user = is_user_provider(provider_name)
    source_label = "[green](User)[/green]" if is_user else "[dim](Built-in)[/dim]"

    console.print(
        Panel.fit(
            f"[bold]Provider:[/bold] [cyan]{provider.name}[/cyan] {source_label}\n\n"
            f"[bold]Description:[/bold] {provider.description}\n"
            f"[bold]Base URL:[/bold] {provider.base_url or 'Default'}\n"
            f"[bold]API Key Env:[/bold] {provider.api_key_env} {api_key_status}\n\n"
            f"[dim]Usage: /model add {provider.name} <model_id>[/dim]",
            title="Provider Details",
            border_style="cyan",
        )
    )
    return "continue"


def _handle_provider_remove(console: Console, provider_name: str) -> CommandResult:
    """Handle /provider remove command."""
    from ...models import get_user_provider_manager, is_user_provider, reload_providers

    # Check if provider exists
    provider = get_provider(provider_name)
    if not provider:
        console.print(f"[red]✗ Unknown provider: {provider_name}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    # Check if it's a user provider
    if not is_user_provider(provider_name):
        console.print(f"[red]✗ Cannot remove built-in provider '{provider_name}'[/red]")
        console.print("[dim]Only user-defined providers can be removed[/dim]")
        return "continue"

    # Remove the provider
    user_provider_manager = get_user_provider_manager()
    success, message = user_provider_manager.remove_provider(provider_name)

    if success:
        # Reload providers cache
        reload_providers()
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_provider_add(console: Console) -> CommandResult:
    """Handle /provider add command with configuration wizard."""
    console.print("[cyan]🔧 Provider Configuration Wizard[/cyan]")
    console.print("[dim]This wizard will help you add a new LLM provider.[/dim]\n")

    try:
        import questionary
    except ImportError:
        console.print("[red]❌ questionary is required for the interactive wizard[/red]")
        console.print("[dim]Install with: pip install questionary[/dim]")
        console.print("[dim]Alternatively, you can manually edit ~/.clippy/providers.json[/dim]")
        return "continue"

    # Step 1: Choose provider type
    provider_type = questionary.select(
        "What type of provider are you adding?",
        choices=[
            questionary.Choice("OpenAI-Compatible API", value="openai"),
            questionary.Choice("Anthropic-Compatible API", value="anthropic"),
            questionary.Choice("Cancel", value="cancel"),
        ],
        default="openai",
    ).ask()

    if provider_type == "cancel":
        console.print("[yellow]Provider configuration cancelled.[/yellow]")
        return "continue"

    # Step 2: Get provider name
    provider_name = questionary.text(
        "Enter a name for this provider (e.g., 'my-openai', 'custom-anthropic')",
        validate=lambda text: len(text.strip()) > 0 or "Provider name cannot be empty",
    ).ask()

    if not provider_name:
        console.print("[yellow]Provider configuration cancelled.[/yellow]")
        return "continue"

    provider_name = provider_name.strip().lower().replace(" ", "-")

    # Check if provider already exists
    existing_provider = get_provider(provider_name)
    if existing_provider:
        overwrite = questionary.confirm(
            f"Provider '{provider_name}' already exists. Do you want to overwrite it?",
            default=False,
        ).ask()
        if not overwrite:
            console.print("[yellow]Provider configuration cancelled.[/yellow]")
            return "continue"

    # Step 3: Get description
    description = questionary.text(
        "Enter a description for this provider",
        default=f"Custom {provider_type.upper()} provider",
    ).ask()

    if not description:
        description = f"Custom {provider_type.upper()} provider"

    # Step 4: Get base URL
    if provider_type == "openai":
        default_url = "https://api.openai.com/v1"
        url_help = "OpenAI-compatible API endpoint"
        example_urls = [
            "https://api.openai.com/v1 (OpenAI)",
            "https://api.cerebras.ai/v1 (Cerebras)",
            "https://api.groq.com/openai/v1 (Groq)",
            "https://api.together.xyz/v1 (Together AI)",
        ]
    else:  # anthropic
        default_url = "https://api.anthropic.com/v1"
        url_help = "Anthropic-compatible API endpoint"
        example_urls = [
            "https://api.anthropic.com/v1 (Anthropic)",
            "https://your-anthropic-proxy.example.com/v1 (Custom proxy)",
        ]

    console.print(f"\n[dim]{url_help}:[/dim]")
    for example in example_urls:
        console.print(f"[dim]  • {example}[/dim]")

    base_url = questionary.text(
        "Enter the base URL for the provider",
        default=default_url,
        validate=lambda text: len(text.strip()) > 0 or "Base URL cannot be empty",
    ).ask()

    if not base_url:
        console.print("[yellow]Provider configuration cancelled.[/yellow]")
        return "continue"

    base_url = base_url.strip()

    # Step 5: Get API key environment variable
    default_env_var = f"{provider_name.upper()}_API_KEY"
    api_key_env = questionary.text(
        "Enter the environment variable name for the API key",
        default=default_env_var,
        validate=lambda text: len(text.strip()) > 0 or "Environment variable name cannot be empty",
    ).ask()

    if not api_key_env:
        console.print("[yellow]Provider configuration cancelled.[/yellow]")
        return "continue"

    api_key_env = api_key_env.strip().upper()

    # Step 6: Confirmation
    console.print("\n[bold]📋 Configuration Summary:[/bold]")
    console.print(f"  Name: [cyan]{provider_name}[/cyan]")
    console.print(f"  Type: [cyan]{provider_type.upper()}[/cyan]")
    console.print(f"  Description: [cyan]{description}[/cyan]")
    console.print(f"  Base URL: [cyan]{base_url}[/cyan]")
    console.print(f"  API Key Env: [cyan]{api_key_env}[/cyan]")

    confirm = questionary.confirm(
        "Do you want to save this provider configuration?",
        default=True,
    ).ask()

    if not confirm:
        console.print("[yellow]Provider configuration cancelled.[/yellow]")
        return "continue"

    # Save the provider configuration
    success, message = _save_provider_config(
        provider_name=provider_name,
        provider_type=provider_type,
        description=description,
        base_url=base_url,
        api_key_env=api_key_env,
        console=console,
    )

    if success:
        console.print(f"[green]✓ {message}[/green]")

        # Show available models usage
        console.print("\n[dim]To use this provider, you can now add models:[/dim]")
        console.print(f"[dim]  /model add {provider_name} <model_id> --name <model_name>[/dim]")

        if provider_type == "openai":
            console.print("[dim]Example models: gpt-4, gpt-3.5-turbo, etc.[/dim]")
        else:
            console.print("[dim]Example models: claude-3-sonnet, claude-3-haiku, etc.[/dim]")

        # Check if API key is set
        api_key = os.getenv(api_key_env, "")
        if not api_key:
            console.print("\n[yellow]⚠ Remember to set the environment variable:[/yellow]")
            console.print(f"[dim]  export {api_key_env}=your_api_key_here[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _save_provider_config(
    provider_name: str,
    provider_type: str,
    description: str,
    base_url: str,
    api_key_env: str,
    console: Console,
) -> tuple[bool, str]:
    """Save provider configuration using the UserProviderManager."""
    from ...models import get_user_provider_manager, reload_providers

    try:
        # Get the user provider manager
        user_provider_manager = get_user_provider_manager()

        # Check if provider already exists (for better error messages)
        existing = user_provider_manager.get_provider(provider_name)
        is_update = existing is not None

        # Add or update the provider
        if is_update:
            success, message = user_provider_manager.update_provider(
                name=provider_name,
                base_url=base_url,
                api_key_env=api_key_env,
                description=description,
            )
        else:
            success, message = user_provider_manager.add_provider(
                name=provider_name,
                base_url=base_url,
                api_key_env=api_key_env,
                description=description,
            )

        if success:
            # Reload providers cache to ensure the changes take effect immediately
            reload_providers()
            action = "updated" if is_update else "added"
            return True, f"Provider '{provider_name}' {action} successfully"
        else:
            return False, message

    except Exception as e:
        return False, f"Failed to save provider configuration: {e}"
