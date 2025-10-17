"""Command handlers for interactive CLI mode."""

import os
from typing import Literal

from rich.console import Console
from rich.panel import Panel

from ..agent import ClippyAgent
from ..models import get_model_config, list_available_models

CommandResult = Literal["continue", "break", "run"]


def handle_exit_command(console: Console) -> CommandResult:
    """Handle /exit or /quit commands."""
    console.print("[yellow]Goodbye![/yellow]")
    return "break"


def handle_reset_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /reset, /clear, or /new commands."""
    agent.reset_conversation()
    console.print("[green]Conversation history reset[/green]")
    return "continue"


def handle_help_command(console: Console) -> CommandResult:
    """Handle /help command."""
    console.print(
        Panel.fit(
            "[bold]Commands:[/bold]\n"
            "  /exit, /quit - Exit code-with-clippy\n"
            "  /reset, /clear, /new - Reset conversation history\n"
            "  /status - Show token usage and session info\n"
            "  /compact - Summarize conversation to reduce context usage\n"
            "  /model list - Show available model presets\n"
            "  /model <name> - Switch to a preset model\n"
            "  /help - Show this help message\n\n"
            "[bold]Interrupt:[/bold]\n"
            "  Ctrl+C or double-ESC - Stop current execution",
            border_style="blue",
        )
    )
    return "continue"


def handle_status_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /status command."""
    status = agent.get_token_count()

    if "error" in status:
        console.print(
            Panel.fit(
                f"[bold red]Error counting tokens:[/bold red]\n{status['error']}\n\n"
                f"[bold]Session Info:[/bold]\n"
                f"  Model: {status['model']}\n"
                f"  Provider: {status.get('base_url') or 'OpenAI'}\n"
                f"  Messages: {status['message_count']}",
                title="Status",
                border_style="yellow",
            )
        )
    else:
        provider = status.get("base_url") or "OpenAI"
        usage_bar_length = 20
        usage_filled = int((status["usage_percent"] / 100) * usage_bar_length)
        usage_bar = "█" * usage_filled + "░" * (usage_bar_length - usage_filled)

        usage_pct = f"{status['usage_percent']:.1f}%"

        # Build message breakdown
        message_info = []
        if status["system_messages"] > 0:
            msg = f"System: {status['system_messages']} msgs, {status['system_tokens']:,} tokens"
            message_info.append(msg)
        if status["user_messages"] > 0:
            msg = f"User: {status['user_messages']} msgs, {status['user_tokens']:,} tokens"
            message_info.append(msg)
        if status["assistant_messages"] > 0:
            msg = (
                f"Assistant: {status['assistant_messages']} msgs, "
                f"{status['assistant_tokens']:,} tokens"
            )
            message_info.append(msg)
        if status["tool_messages"] > 0:
            msg = f"Tool: {status['tool_messages']} msgs, {status['tool_tokens']:,} tokens"
            message_info.append(msg)

        message_breakdown = "\n    ".join(message_info) if message_info else "No messages yet"

        console.print(
            Panel.fit(
                f"[bold]Current Session:[/bold]\n"
                f"  Model: [cyan]{status['model']}[/cyan]\n"
                f"  Provider: [cyan]{provider}[/cyan]\n"
                f"  Messages: [cyan]{status['message_count']}[/cyan]\n\n"
                f"[bold]Token Usage:[/bold]\n"
                f"  Context: [cyan]{status['total_tokens']:,}[/cyan] tokens\n"
                f"  Usage: [{usage_bar}] [cyan]{usage_pct}[/cyan]\n\n"
                f"[bold]Message Breakdown:[/bold]\n"
                f"    {message_breakdown}\n\n"
                f"[dim]Note: Usage % is estimated for ~128k context window[/dim]",
                title="Session Status",
                border_style="cyan",
            )
        )
    return "continue"


def handle_compact_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /compact command."""
    console.print("[cyan]Compacting conversation...[/cyan]")

    success, message, stats = agent.compact_conversation()

    if success:
        console.print(
            Panel.fit(
                f"[bold green]✓ Conversation Compacted[/bold green]\n\n"
                f"[bold]Token Reduction:[/bold]\n"
                f"  Before: [cyan]{stats['before_tokens']:,}[/cyan] tokens\n"
                f"  After: [cyan]{stats['after_tokens']:,}[/cyan] tokens\n"
                f"  Saved: [green]{stats['tokens_saved']:,}[/green] tokens "
                f"([green]{stats['reduction_percent']:.1f}%[/green])\n\n"
                f"[bold]Messages:[/bold]\n"
                f"  Before: [cyan]{stats['messages_before']}[/cyan] messages\n"
                f"  After: [cyan]{stats['messages_after']}[/cyan] messages\n"
                f"  Summarized: "
                f"[cyan]{stats['messages_summarized']}[/cyan] messages\n\n"
                f"[dim]The conversation history has been condensed while "
                f"preserving recent context.[/dim]",
                title="Compact Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                f"[bold yellow]⚠ Cannot Compact[/bold yellow]\n\n{message}",
                title="Compact",
                border_style="yellow",
            )
        )
    return "continue"


def handle_model_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /model command."""
    if not command_args or command_args.lower() == "list":
        # Show available models
        models = list_available_models()
        model_list = "\n".join(f"  [cyan]{name:20}[/cyan] - {desc}" for name, desc in models)
        current_model = agent.model
        current_provider = agent.base_url or "OpenAI"
        console.print(
            Panel.fit(
                f"[bold]Available Model Presets:[/bold]\n\n{model_list}\n\n"
                f"[bold]Current:[/bold] {current_model} ({current_provider})\n\n"
                f"[dim]Usage: /model <name>[/dim]",
                title="Models",
                border_style="cyan",
            )
        )
    else:
        # Switch to specified model
        model_name = command_args.strip()
        config = get_model_config(model_name)

        if config:
            # Use preset configuration
            # Load API key from environment variable specified in config
            api_key = os.getenv(config.api_key_env)

            if not api_key:
                console.print(
                    f"[yellow]⚠ Warning: {config.api_key_env} not set in "
                    f"environment[/yellow]\n"
                    f"[dim]The model may fail if it requires authentication.[/dim]"
                )
                # Continue anyway - some providers like Ollama might not need a key
                api_key = "not-set"

            success, message = agent.switch_model(
                model=config.model_id, base_url=config.base_url, api_key=api_key
            )
        else:
            # Treat as custom model ID (keep current base_url and api_key)
            success, message = agent.switch_model(model=model_name)

        if success:
            console.print(f"[green]✓ {message}[/green]")
        else:
            console.print(f"[red]✗ {message}[/red]")

    return "continue"


def handle_command(user_input: str, agent: ClippyAgent, console: Console) -> CommandResult | None:
    """
    Handle slash commands in interactive mode.

    Returns:
        CommandResult if a command was handled, None if not a command
    """
    command_lower = user_input.lower()

    # Exit commands
    if command_lower in ["/exit", "/quit"]:
        return handle_exit_command(console)

    # Reset commands
    if command_lower in ["/reset", "/clear", "/new"]:
        return handle_reset_command(agent, console)

    # Help command
    if command_lower == "/help":
        return handle_help_command(console)

    # Status command
    if command_lower == "/status":
        return handle_status_command(agent, console)

    # Compact command
    if command_lower == "/compact":
        return handle_compact_command(agent, console)

    # Model commands
    if command_lower.startswith("/model"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_model_command(agent, console, command_args)

    # Not a recognized command
    return None
