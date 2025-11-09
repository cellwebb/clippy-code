"""Command handlers for interactive CLI mode."""

import json
import os
import shlex
import time
from typing import Any, Literal

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from ..agent import ClippyAgent
from ..agent.subagent_config_manager import get_subagent_config_manager
from ..agent.subagent_types import list_subagent_types
from ..models import (
    get_provider,
    get_user_manager,
    list_available_models,
    list_available_providers,
)
from ..permissions import ActionType, PermissionLevel

CommandResult = Literal["continue", "break", "run"]


def _format_time_ago(timestamp: float) -> str:
    """Format a timestamp as 'X time ago' string."""
    now = time.time()
    diff = now - timestamp

    if diff < 60:
        return "just now" if diff < 10 else f"{int(diff)} seconds ago"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < 604800:
        days = int(diff / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = int(diff / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"


def _get_all_conversations_with_timestamps(agent: ClippyAgent) -> list[dict[str, Any]]:
    """Get all conversations with their data including timestamps."""
    conversations = []

    try:
        conversation_files = agent.conversations_dir.glob("*.json")
        for conv_file in conversation_files:
            try:
                with open(conv_file) as f:
                    data = json.load(f)

                conversations.append(
                    {
                        "name": conv_file.stem,
                        "timestamp": data.get("timestamp", 0),
                        "model": data.get("model", "unknown"),
                        "message_count": len(data.get("conversation_history", [])),
                    }
                )
            except (json.JSONDecodeError, FileNotFoundError):
                # Handle empty or corrupted files - use file modification time
                try:
                    conversations.append(
                        {
                            "name": conv_file.stem,
                            "timestamp": conv_file.stat().st_mtime,  # Use file modification time
                            "model": "unknown",
                            "message_count": 0,
                        }
                    )
                except Exception:
                    # If we can't even get file stats, skip this file
                    continue

        # Sort by timestamp (most recent first)
        conversations.sort(key=lambda x: x["timestamp"], reverse=True)

    except Exception:
        # If we can't read the directory, return empty list
        pass

    return conversations


def _display_conversation_history(agent: ClippyAgent, console: Console) -> None:
    """Display the conversation history for scrolling back."""
    history = agent.conversation_history

    if not history:
        console.print("[dim]No messages in this conversation yet.[/dim]")
        return

    # Skip system message for display (too verbose)
    display_history = [msg for msg in history if msg.get("role") != "system"]

    if not display_history:
        console.print("[dim]No user messages in this conversation yet.[/dim]")
        return

    # Show recent messages (last 20 to avoid overwhelming output)
    recent_messages = display_history[-20:] if len(display_history) > 20 else display_history

    console.print(
        f"\n[bold cyan]Conversation History ({len(display_history)} messages):[/bold cyan]"
    )
    console.print("[dim]Scroll up to see earlier messages[/dim]\n")

    for i, msg in enumerate(recent_messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "").strip()

        if not content:
            continue

        # Format based on role
        if role == "user":
            console.print(f"[bold green]You:[/bold green] {escape(content)}")
        elif role == "assistant":
            # Truncate very long assistant responses for display
            if len(content) > 500:
                display_content = escape(content[:500]) + "\n[dim]... (truncated)[/dim]"
            else:
                display_content = escape(content)
            console.print(f"[bold blue]Clippy:[/bold blue] {display_content}")
        elif role == "tool":
            console.print(
                f"[bold yellow]Tool Result:[/bold yellow] "
                f"[dim]{escape(content[:200])}{'...' if len(content) > 200 else ''}[/dim]"
            )
        else:
            console.print(
                f"[dim]{role}: {escape(content[:100])}{'...' if len(content) > 100 else ''}[/dim]"
            )

        console.print("")  # Add spacing between messages

    # Show if there are more messages not displayed
    if len(display_history) > 20:
        console.print(
            f"[dim]... and {len(display_history) - 20} earlier messages not shown[/dim]\n"
        )

    console.print("[dim]You can now continue the conversation below:[/dim]")


def handle_exit_command(console: Console) -> CommandResult:
    """Handle /exit or /quit commands."""
    console.print("[yellow]Goodbye![/yellow]")
    return "break"


def handle_reset_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /reset, /clear, or /new commands."""
    agent.reset_conversation()
    console.print("[green]Conversation history reset[/green]")
    return "continue"


def handle_resume_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /resume command."""
    # Parse command arguments
    args = shlex.split(command_args) if command_args else []

    # If no name specified, show interactive selection of conversations
    if not args:
        conversations = _get_all_conversations_with_timestamps(agent)
        if not conversations:
            console.print("[yellow]No saved conversations found.[/yellow]")
            return "continue"

        # Remove the debug print - conversation discovery is working

        # Import questionary for interactive selection
        try:
            import questionary
        except ImportError:
            # Fallback to showing available conversations with timestamps
            console.print(
                "[yellow]Interactive selection not available. Available conversations:[/yellow]"
            )
            for conv in conversations:
                time_ago = _format_time_ago(conv["timestamp"])
                msg_count = conv["message_count"]
                console.print(
                    f"  [cyan]{conv['name']}[/cyan] - {time_ago} "
                    f"([dim]{msg_count} message{'s' if msg_count != 1 else ''}[/dim])"
                )
            console.print("[dim]Usage: /resume <name>[/dim]")
            return "continue"

        # Create choices with detailed information for questionary
        choices = []
        for conv in conversations:
            time_ago = _format_time_ago(conv["timestamp"])
            msg_count = conv["message_count"]
            display_name = f"{conv['name']} ({time_ago}, {msg_count} messages)"
            choices.append(questionary.Choice(title=display_name, value=conv["name"]))

        # Show interactive selection
        conversation_name = questionary.select(
            "Select a conversation to resume:",
            choices=choices,
            instruction="Use arrow keys to navigate, Enter to select",
        ).ask()

        # If user cancelled the selection
        if conversation_name is None:
            console.print("[yellow]Resume cancelled.[/yellow]")
            return "continue"
    else:
        conversation_name = args[0]

    # Load the conversation
    success, message = agent.load_conversation(conversation_name)

    if success:
        console.print(f"[green]✓ {escape(message)}[/green]")

        # Show the conversation history so user can scroll back
        _display_conversation_history(agent, console)

        # Show info about the loaded conversation
        conversations = _get_all_conversations_with_timestamps(agent)
        if conversations:
            names = [conv["name"] for conv in conversations[:5]]  # Show first 5
            if len(conversations) > 5:
                names.append(f"...and {len(conversations) - 5} more")
            console.print(f"[dim]Available conversations: {', '.join(names)}[/dim]")
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")
        # Show available conversations if loading failed
        conversations = _get_all_conversations_with_timestamps(agent)
        if conversations:
            names = [conv["name"] for conv in conversations[:5]]  # Show first 5
            if len(conversations) > 5:
                names.append(f"...and {len(conversations) - 5} more")
            console.print(f"[dim]Available conversations: {', '.join(names)}[/dim]")
        else:
            console.print("[dim]No saved conversations found.[/dim]")

    return "continue"


def handle_help_command(console: Console) -> CommandResult:
    """Handle /help command."""
    console.print(
        Panel.fit(
            "[bold]Session Control:[/bold]\n"
            "  /help - Show this help message\n"
            "  /init - Create or refine AGENTS.md documentation\n"
            "    /init --refine - Enhance existing AGENTS.md with project analysis\n"
            "    /init --force - Overwrite existing AGENTS.md with fresh template\n"
            "  /exit, /quit - Exit clippy-code\n"
            "  /reset, /clear, /new - Reset conversation history\n"
            "  /resume [name] - Resume a saved conversation\n"
            "    (interactive selection if no name provided)\n"
            "  /truncate <count> [option] - Truncate conversation history\n"
            "    Options: --keep-recent (default), --keep-older\n"
            "    Examples: /truncate 5, /truncate 3 --keep-older\n"
            "[bold]Session Info:[/bold]\n"
            "  /status - Show token usage and session info\n"
            "  /compact - Summarize conversation to reduce context usage\n\n"
            "[bold]Model Management:[/bold]\n"
            "  /model - List available subcommands and models\n"
            "  /model list - Show your saved models\n"
            "  /model <name> - Switch to a saved model\n"
            "  /model load <name> - Load model (same as direct switch)\n"
            "  /model add <provider> <model_id> [options] - Add a new model\n"
            "    Options: --name <name>, --default, --threshold <tokens>\n"
            "  /model remove <name> - Remove a saved model\n"
            "  /model default <name> - Set model as default\n"
            "  /model threshold <name> <tokens> - Set compaction threshold\n"
            "  /model use <provider> <model_id> - Try a model without saving\n\n"
            "[bold]Subagent Configuration:[/bold]\n"
            "  /subagent list - Show subagent type configurations\n"
            "  /subagent set <type> <model> - Set model for a subagent type\n"
            "  /subagent clear <type> - Clear model override for a subagent type\n"
            "  /subagent reset - Clear all model overrides\n\n"
            "[bold]Providers:[/bold]\n"
            "  /providers - List available providers\n"
            "  /provider <name> - Show provider details\n\n"
            "[bold]Permissions:[/bold]\n"
            "  /auto list - List auto-approved actions\n"
            "  /auto revoke <action> - Revoke auto-approval for an action\n"
            "  /auto clear - Clear all auto-approvals\n"
            "  /yolo - Toggle YOLO mode (auto-approve ALL actions)\n\n"
            "[bold]MCP Servers:[/bold]\n"
            "  /mcp list - List configured MCP servers\n"
            "  /mcp tools [server] - List tools available from MCP servers\n"
            "  /mcp refresh - Refresh tool catalogs from MCP servers\n"
            "  /mcp allow <server> - Mark an MCP server as trusted for this session\n"
            "  /mcp revoke <server> - Revoke trust for an MCP server\n"
            "  /mcp enable <server> - Enable a disabled MCP server\n"
            "  /mcp disable <server> - Disable an enabled MCP server\n\n"
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

        # Build dynamic note for context limit source
        note: str
        if status.get("context_source") == "threshold":
            note = (
                f"[dim]Note: Usage % based on compaction threshold of "
                f"{status.get('context_limit'):,} tokens[/dim]"
            )
        else:
            note = "[dim]Note: Usage % is estimated for ~128k context window[/dim]"

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
                f"{note}",
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
                f"[bold yellow]⚠ Cannot Compact[/bold yellow]\n\n{escape(message)}",
                title="Compact",
                border_style="yellow",
            )
        )
    return "continue"


def handle_providers_command(console: Console) -> CommandResult:
    """Handle /providers command."""
    providers = list_available_providers()

    if not providers:
        console.print("[yellow]No providers available[/yellow]")
        return "continue"

    provider_list = "\n".join(f"  [cyan]{name:12}[/cyan] - {desc}" for name, desc in providers)

    console.print(
        Panel.fit(
            f"[bold]Available Providers:[/bold]\n\n{provider_list}\n\n"
            f"[dim]Usage: /model add <provider> <model_id>[/dim]",
            title="Providers",
            border_style="cyan",
        )
    )
    return "continue"


def handle_provider_command(console: Console, provider_name: str) -> CommandResult:
    """Handle /provider <name> command."""
    provider = get_provider(provider_name)

    if not provider:
        console.print(f"[red]✗ Unknown provider: {provider_name}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    api_key = os.getenv(provider.api_key_env, "")
    api_key_status = "[green]✓ Set[/green]" if api_key else "[yellow]⚠ Not set[/yellow]"

    console.print(
        Panel.fit(
            f"[bold]Provider:[/bold] [cyan]{provider.name}[/cyan]\n\n"
            f"[bold]Description:[/bold] {provider.description}\n"
            f"[bold]Base URL:[/bold] {provider.base_url or 'Default'}\n"
            f"[bold]API Key Env:[/bold] {provider.api_key_env} {api_key_status}\n\n"
            f"[dim]Usage: /model add {provider.name} <model_id>[/dim]",
            title="Provider Details",
            border_style="cyan",
        )
    )
    return "continue"


def handle_model_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /model commands."""
    if not command_args or command_args.lower() == "list":
        # Show user's saved models
        models = list_available_models()

        if not models:
            console.print(
                Panel.fit(
                    "[bold]No saved models yet[/bold]\n\n"
                    "[dim]Add a model to get started:\n"
                    '  /model add openai gpt-5 --name "gpt-5" --default\n'
                    '  /model add cerebras qwen-3-coder-480b --name "q3c"[/dim]\n\n'
                    "[bold]Available Commands:[/bold]\n"
                    "  /model list - Show your saved models\n"
                    "  /model <name> - Switch to a saved model\n"
                    "  /model load <name> - Load model (same as direct switch)\n"
                    "  /model add <provider> <model_id> [options] - Add a new model\n"
                    "    Options: --name <name>, --default\n"
                    "  /model remove <name> - Remove a saved model\n"
                    "  /model default <name> - Set model as default\n"
                    "  /model use <provider> <model_id> - Try a model without saving\n\n"
                    "[dim]Examples:\n"
                    '  /model add openai gpt-5 --name "gpt-5" --default\n'
                    '  /model add cerebras qwen-3-coder-480b --name "q3c"\n'
                    "  /model use ollama llama3.2:latest\n"
                    "  /model gpt-5[/dim]",
                    title="Model Management",
                    border_style="yellow",
                )
            )
            return "continue"

        model_lines = []
        for model_config in models:
            name, desc, is_default = model_config[:3]  # Extract first three values
            # Try to get threshold if it exists (newer models might have it)
            threshold = model_config[3] if len(model_config) > 3 else None

            default_indicator = " [green](default)[/green]" if is_default else ""
            threshold_info = f" [dim](threshold: {threshold:,} tokens)[/dim]" if threshold else ""
            model_lines.append(
                f"  [cyan]{name:20}[/cyan] - {desc}{default_indicator}{threshold_info}"
            )

        current_model = agent.model
        current_provider = agent.base_url or "OpenAI"

        console.print(
            Panel.fit(
                "[bold]Your Saved Models:[/bold]\n\n" + "\n".join(model_lines) + f"\n\n"
                f"[bold]Current:[/bold] {current_model} ({current_provider})\n\n"
                "[bold]Available Commands:[/bold]\n"
                "  /model list - Show your saved models\n"
                "  /model <name> - Switch to a saved model\n"
                "  /model load <name> - Load model (same as direct switch)\n"
                "  /model add <provider> <model_id> [options] - Add a new model\n"
                "    Options: --name <name>, --default, --threshold <tokens>\n"
                "  /model remove <name> - Remove a saved model\n"
                "  /model default <name> - Set model as default\n"
                "  /model threshold <name> <tokens> - Set compaction threshold\n"
                "  /model use <provider> <model_id> - Try a model without saving\n\n"
                "[dim]Examples:\n"
                '  /model add openai gpt-5 --name "gpt-5" --default --threshold 80000\n'
                '  /model add cerebras qwen-3-coder-480b --name "q3c" --threshold 100000\n'
                "  /model use ollama llama3.2:latest\n"
                "  /model gpt-5[/dim]",
                title="Model Management",
                border_style="cyan",
            )
        )
        return "continue"

    # Parse command arguments
    try:
        args = shlex.split(command_args)
    except ValueError as e:
        console.print(f"[red]✗ Error parsing arguments: {e}[/red]")
        return "continue"

    if not args:
        console.print("[red]Usage: /model <command> [args][/red]")
        console.print("[dim]Commands: list, add, remove, default, use, <name>[/dim]")
        return "continue"

    subcommand = args[0].lower()

    if subcommand == "add":
        return _handle_model_add(console, args[1:])
    elif subcommand == "remove":
        return _handle_model_remove(console, args[1:])
    elif subcommand == "default":
        return _handle_model_default(console, args[1:])
    elif subcommand == "use":
        return _handle_model_use(agent, console, args[1:])
    elif subcommand == "load":
        # Handle /model load <name> - same as direct switch
        if len(args) >= 2:
            return _handle_model_switch(agent, console, args[1])
        else:
            console.print("[red]Usage: /model load <name>[/red]")
            console.print("[dim]Same as: /model <name>[/dim]")
            return "continue"
    elif subcommand == "threshold":
        return _handle_model_threshold(agent, console, args[1:])
    else:
        # Treat as model name to switch to
        # This handles cases where the user tries to switch to a specific model
        # by passing the model name directly as an argument
        return _handle_model_switch(agent, console, subcommand)


def _handle_model_add(console: Console, args: list[str]) -> CommandResult:
    """Handle /model add command."""
    if len(args) < 2:
        console.print(
            "[red]Usage: /model add <provider> <model_id> [options][/red]\n"
            "[dim]Options: --name <name>, --default, --threshold <tokens>[/dim]"
        )
        console.print(
            '[dim]Example: /model add cerebras qwen-3-coder-480b --name "q3c" \n'
            "          --default --threshold 80000[/dim]"
        )
        return "continue"

    provider = args[0]
    model_id = args[1]

    # Parse optional arguments
    name = None
    is_default = False
    compaction_threshold = None

    i = 2
    while i < len(args):
        if args[i] == "--name" and i + 1 < len(args):
            name = args[i + 1]
            i += 2
        elif args[i] == "--default":
            is_default = True
            i += 1
        elif args[i] == "--threshold" and i + 1 < len(args):
            try:
                compaction_threshold = int(args[i + 1])
                i += 2
            except ValueError:
                console.print(f"[red]✗ Invalid threshold value: {args[i + 1]}[/red]")
                return "continue"
        else:
            console.print(f"[red]✗ Unknown argument: {args[i]}[/red]")
            return "continue"

    # Use model_id as name if not specified
    if not name:
        name = model_id.replace(":", "-").replace("/", "-")

    # Add the model
    user_manager = get_user_manager()
    success, message = user_manager.add_model(
        name, provider, model_id, is_default, compaction_threshold
    )

    if success:
        console.print(f"[green]✓ {escape(message)}[/green]")
        if is_default:
            console.print("[dim]Set as default model[/dim]")
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")

    return "continue"


def _handle_model_remove(console: Console, args: list[str]) -> CommandResult:
    """Handle /model remove command."""
    if not args:
        console.print("[red]Usage: /model remove <name>[/red]")
        return "continue"

    name = args[0]
    user_manager = get_user_manager()
    success, message = user_manager.remove_model(name)

    if success:
        console.print(f"[green]✓ {escape(message)}[/green]")
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")

    return "continue"


def _handle_model_default(console: Console, args: list[str]) -> CommandResult:
    """Handle /model default command."""
    if not args:
        console.print("[red]Usage: /model default <name>[/red]")
        return "continue"

    name = args[0]
    user_manager = get_user_manager()
    success, message = user_manager.set_default(name)

    if success:
        console.print(f"[green]✓ {escape(message)}[/green]")
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")
        # Show available models if the model doesn't exist
        available_models = user_manager.list_models()
        if available_models:
            model_names = [m.name for m in available_models]
            console.print(f"[dim]Available models: {', '.join(model_names)}[/dim]")
        else:
            console.print("[dim]No models available. Use /model add to add a model.[/dim]")

    return "continue"


def _handle_model_use(agent: ClippyAgent, console: Console, args: list[str]) -> CommandResult:
    """Handle /model use command (try without saving)."""
    if len(args) < 2:
        console.print("[red]Usage: /model use <provider> <model_id>[/red]")
        console.print("[dim]Example: /model use ollama llama3.2:latest[/dim]")
        return "continue"

    provider_name = args[0]
    model_id = args[1]

    # Get provider
    provider = get_provider(provider_name)
    if not provider:
        console.print(f"[red]✗ Unknown provider: {provider_name}[/red]")
        console.print("[dim]Use /providers to see available providers[/dim]")
        return "continue"

    # Get API key
    api_key = os.getenv(provider.api_key_env)
    if not api_key and provider.name != "ollama":
        console.print(
            f"[yellow]⚠ Warning: {provider.api_key_env} not set in environment[/yellow]\n"
            f"[dim]The model may fail if it requires authentication.[/dim]"
        )
        api_key = "not-set"

    # Switch to model
    success, message = agent.switch_model(
        model=model_id, base_url=provider.base_url, api_key=api_key
    )

    if success:
        if provider.base_url and provider.base_url != "https://api.openai.com/v1":
            provider_info = f" ({provider.base_url})"
        else:
            provider_info = " (OpenAI)"
        console.print(
            Panel.fit(
                f"[bold green]✓ Using Temporary Model[/bold green]\n\n"
                f"[bold]Model ID:[/bold] [cyan]{model_id}[/cyan]\n"
                f"[bold]Provider:[/bold] [cyan]{provider_name}[/cyan]{provider_info}\n\n"
                f"[dim]This is temporary for the current session.\n"
                f"Use '/model add {provider_name} {model_id} --name <name>' to save.[/dim]",
                title="Temporary Model",
                border_style="blue",
            )
        )
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")

    return "continue"


def _handle_model_threshold(agent: ClippyAgent, console: Console, args: list[str]) -> CommandResult:
    """Handle /model threshold command."""
    if len(args) < 2:
        console.print("[red]Usage: /model threshold <name> <tokens>[/red]")
        console.print("[dim]Example: /model threshold gpt-4o 80000[/dim]")
        return "continue"

    name = args[0]
    try:
        threshold = int(args[1])
    except ValueError:
        console.print(f"[red]✗ Invalid threshold value: {args[1]}[/red]")
        return "continue"

    user_manager = get_user_manager()
    success, message = user_manager.set_compaction_threshold(name, threshold)

    if success:
        console.print(f"[green]✓ {escape(message)}[/green]")
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")

    return "continue"


def _handle_model_switch(agent: ClippyAgent, console: Console, model_name: str) -> CommandResult:
    """Handle switching to a saved model."""
    # Explicit validation for empty or whitespace-only model names
    if not model_name or not model_name.strip():
        console.print("[red]✗ Model name cannot be empty[/red]")
        return "continue"

    model_name = model_name.strip()

    # Check if model exists in user's saved models
    user_manager = get_user_manager()
    model = user_manager.get_model(model_name)

    if not model:
        console.print(f"[red]✗ Model '{model_name}' not found in your saved models[/red]")
        available_models = user_manager.list_models()
        if available_models:
            model_names = [m.name for m in available_models]
            console.print(f"[dim]Available models: {', '.join(model_names)}[/dim]")
        else:
            console.print("[dim]No models available. Use /model add to add a model.[/dim]")
        console.print("[yellow]⚠ Model switch aborted - no changes made[/yellow]")
        return "continue"

    # Get the provider for this model
    provider = get_provider(model.provider)

    if not provider:
        console.print(f"[red]✗ Provider '{model.provider}' not found[/red]")
        return "continue"

    # Get API key
    api_key = os.getenv(provider.api_key_env)
    if not api_key and provider.name != "ollama":
        console.print(
            f"[yellow]⚠ Warning: {provider.api_key_env} not set in environment[/yellow]\n"
            f"[dim]The model may fail if it requires authentication.[/dim]"
        )
        api_key = "not-set"

    # Switch to model
    success, message = agent.switch_model(
        model=model.model_id, base_url=provider.base_url, api_key=api_key
    )

    if success:
        if provider.base_url and provider.base_url != "https://api.openai.com/v1":
            provider_info = f" ({provider.base_url})"
        else:
            provider_info = " (OpenAI)"
        console.print(
            Panel.fit(
                f"[bold green]✓ Model Switched Successfully[/bold green]\n\n"
                f"[bold]New Model:[/bold] [cyan]{model.name}[/cyan]\n"
                f"[bold]Provider:[/bold] [cyan]{provider.name}[/cyan]\n"
                f"[bold]Model ID:[/bold] [cyan]{model.model_id}[/cyan]{provider_info}",
                title="Model Changed",
                border_style="green",
            )
        )
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")

    return "continue"


def handle_auto_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /auto command."""
    if not command_args or command_args.lower() == "list":
        # Show currently auto-approved actions
        auto_approved = agent.permission_manager.config.auto_approve
        if auto_approved:
            action_list = "\n".join(
                f"  [cyan]{action.value}[/cyan]" for action in sorted(auto_approved)
            )
            console.print(
                Panel.fit(
                    f"[bold]Auto-approved Actions:[/bold]\n\n{action_list}\n\n"
                    f"[dim]These actions will execute without prompting in the "
                    f"current session.[/dim]",
                    title="Auto-Approved Actions",
                    border_style="cyan",
                )
            )
        else:
            console.print(
                Panel.fit(
                    "[bold]No Auto-approved Actions[/bold]\n\n"
                    "Use 'a' or 'allow' when prompted to approve an action "
                    "to auto-approve it.\n\n"
                    "[dim]Example: When prompted, type 'a' instead of 'y' to "
                    "auto-approve that action type.[/dim]",
                    title="Auto-Approved Actions",
                    border_style="cyan",
                )
            )
    elif command_args.lower().startswith("revoke "):
        # Revoke auto-approval for a specific action
        parts = command_args.split(maxsplit=1)
        if len(parts) < 2:
            console.print("[red]Usage: /auto revoke <action_type>[/red]")
            return "continue"

        action_name = parts[1].strip()
        try:
            action_type = ActionType(action_name)
            # Check if it's currently auto-approved
            if action_type in agent.permission_manager.config.auto_approve:
                # Move it back to require_approval
                agent.permission_manager.update_permission(
                    action_type, PermissionLevel.REQUIRE_APPROVAL
                )
                console.print(f"[green]✓ Revoked auto-approval for {action_name}[/green]")
            else:
                console.print(f"[yellow]⚠ {action_name} is not currently auto-approved[/yellow]")
        except ValueError:
            console.print(f"[red]✗ Unknown action type: {action_name}[/red]")
            console.print("[dim]Use /auto list to see available action types[/dim]")
    elif command_args.lower() == "clear":
        # Revoke all auto-approvals (move them back to require_approval)
        auto_approved = agent.permission_manager.config.auto_approve.copy()
        for action_type in auto_approved:
            agent.permission_manager.update_permission(
                action_type, PermissionLevel.REQUIRE_APPROVAL
            )
        if auto_approved:
            revoked_list = ", ".join(action.value for action in auto_approved)
            console.print(f"[green]✓ Cleared auto-approvals for: {revoked_list}[/green]")
        else:
            console.print("[yellow]No auto-approvals to clear[/yellow]")
    else:
        console.print("[red]Unknown /auto command[/red]")
        console.print("[dim]Available commands: list, revoke <action>, clear[/dim]")

    return "continue"


def handle_mcp_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /mcp commands."""
    if not command_args:
        console.print("[red]Usage: /mcp <command>[/red]")
        console.print(
            "[dim]Available commands: list, tools, refresh, allow, revoke, enable, disable[/dim]"
        )
        return "continue"

    parts = command_args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()
    subcommand_args = parts[1] if len(parts) > 1 else ""

    # Get MCP manager from agent
    mcp_manager = getattr(agent, "mcp_manager", None)
    if mcp_manager is None:
        console.print("[yellow]⚠ MCP functionality not available[/yellow]")
        console.print("[dim]Make sure the agent was initialized with MCP support.[/dim]")
        return "continue"

    if subcommand == "list":
        _handle_mcp_list(mcp_manager, console)
    elif subcommand == "tools":
        _handle_mcp_tools(mcp_manager, console, subcommand_args)
    elif subcommand == "refresh":
        _handle_mcp_refresh(mcp_manager, console)
    elif subcommand == "allow":
        _handle_mcp_allow(mcp_manager, console, subcommand_args)
    elif subcommand == "revoke":
        _handle_mcp_revoke(mcp_manager, console, subcommand_args)
    elif subcommand == "enable":
        _handle_mcp_enable(mcp_manager, console, subcommand_args)
    elif subcommand == "disable":
        _handle_mcp_disable(mcp_manager, console, subcommand_args)
    else:
        console.print(f"[red]Unknown MCP command: {subcommand}[/red]")
        console.print(
            "[dim]Available commands: list, tools, refresh, allow, revoke, enable, disable[/dim]"
        )

    return "continue"


def _handle_mcp_list(mcp_manager: Any, console: Console) -> None:
    """Handle /mcp list command."""
    servers = mcp_manager.list_servers()

    if not servers:
        console.print("[yellow]No MCP servers configured[/yellow]")
        console.print("[dim]Add servers to mcp.json to use MCP functionality.[/dim]")
        return

    server_lines = []
    for server in servers:
        status = "[green]connected[/green]" if server["connected"] else "[red]disconnected[/red]"
        enabled_status = (
            "[green]enabled[/green]" if server["enabled"] else "[yellow]disabled[/yellow]"
        )
        server_lines.append(
            f"  [cyan]{server['server_id']:20}[/cyan] - {enabled_status} - "
            f"{status} ({server['tools_count']} tools)"
        )

    console.print(
        Panel.fit(
            "[bold]Configured MCP Servers:[/bold]\n\n" + "\n".join(server_lines),
            title="MCP Servers",
            border_style="cyan",
        )
    )


def _handle_mcp_tools(mcp_manager: Any, console: Console, server_arg: str) -> None:
    """Handle /mcp tools command."""
    if server_arg:
        # List tools for specific server
        tools = mcp_manager.list_tools(server_arg)
        if not tools:
            console.print(f"[yellow]No tools found for server '{server_arg}'[/yellow]")
            return
    else:
        # List tools for all servers
        tools = mcp_manager.list_tools()
        if not tools:
            console.print("[yellow]No MCP tools available[/yellow]")
            return

    tool_lines = []
    current_server = None
    for tool in tools:
        if tool["server_id"] != current_server:
            current_server = tool["server_id"]
            tool_lines.append(f"\n[bold]Server: {current_server}[/bold]")
        tool_lines.append(f"  [cyan]{tool['name']}[/cyan] - {tool['description']}")

    console.print(
        Panel.fit(
            "[bold]Available MCP Tools:[/bold]\n" + "\n".join(tool_lines),
            title="MCP Tools",
            border_style="cyan",
        )
    )


def _handle_mcp_refresh(mcp_manager: Any, console: Console) -> None:
    """Handle /mcp refresh command."""
    console.print("[cyan]Refreshing MCP server connections...[/cyan]")
    try:
        mcp_manager.stop()
        mcp_manager.start()
        console.print("[green]✓ MCP servers refreshed[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error refreshing MCP servers: {escape(str(e))}[/red]")


def _handle_mcp_allow(mcp_manager: Any, console: Console, server_arg: str) -> None:
    """Handle /mcp allow command."""
    if not server_arg:
        console.print("[red]Usage: /mcp allow <server_id>[/red]")
        return

    server_id = server_arg.strip()
    mcp_manager.set_trusted(server_id, True)
    console.print(f"[green]✓ Marked MCP server '{server_id}' as trusted for this session[/green]")


def _handle_mcp_revoke(mcp_manager: Any, console: Console, server_arg: str) -> None:
    """Handle /mcp revoke command."""
    if not server_arg:
        console.print("[red]Usage: /mcp revoke <server_id>[/red]")
        return

    server_id = server_arg.strip()
    mcp_manager.set_trusted(server_id, False)
    console.print(f"[green]✓ Revoked trust for MCP server '{server_id}'[/green]")


def _handle_mcp_enable(mcp_manager: Any, console: Console, server_arg: str) -> None:
    """Handle /mcp enable command."""
    if not server_arg:
        console.print("[red]Usage: /mcp enable <server_id>[/red]")
        return

    server_id = server_arg.strip()
    success = mcp_manager.set_enabled(server_id, True)

    if success:
        console.print(f"[green]✓ Enabled MCP server '{server_id}'[/green]")
        console.print("[dim]Server will be available on next refresh or restart[/dim]")
    else:
        console.print(f"[red]✗ MCP server '{server_id}' not found in configuration[/red]")


def _handle_mcp_disable(mcp_manager: Any, console: Console, server_arg: str) -> None:
    """Handle /mcp disable command."""
    if not server_arg:
        console.print("[red]Usage: /mcp disable <server_id>[/red]")
        return

    server_id = server_arg.strip()
    success = mcp_manager.set_enabled(server_id, False)

    if success:
        console.print(f"[green]✓ Disabled MCP server '{server_id}'[/green]")
        console.print("[dim]Server has been disconnected and won't be started automatically[/dim]")
    else:
        console.print(f"[red]✗ MCP server '{server_id}' not found in configuration[/red]")


def handle_subagent_command(
    agent: ClippyAgent, console: Console, command_args: str
) -> CommandResult:
    """Handle /subagent commands."""
    config_manager = get_subagent_config_manager()

    if not command_args or command_args.lower() == "list":
        # Show all subagent types and their model configurations
        configs = config_manager.get_all_configurations()

        if not configs:
            console.print("[red]✗ No subagent types available[/red]")
            return "continue"

        config_lines = []
        for subagent_type in sorted(configs.keys()):
            type_config = configs[subagent_type]
            override = type_config["model_override"]
            max_iterations = type_config["max_iterations"]

            if override:
                model_info = f"[green]{override}[/green]"
            else:
                model_info = "[dim](inherits from parent)[/dim]"

            config_lines.append(
                f"  [cyan]{subagent_type:20}[/cyan] {model_info}  "
                f"[dim]({max_iterations} iterations)[/dim]"
            )

        current_model = agent.model
        console.print(
            Panel.fit(
                "[bold]Subagent Type Configurations:[/bold]\n\n"
                + "\n".join(config_lines)
                + f"\n\n[bold]Parent Model:[/bold] [cyan]{current_model}[/cyan]\n\n"
                + "[dim]Usage: /subagent set <type> <model>[/dim]\n"
                + "[dim]       /subagent clear <type>[/dim]",
                title="Subagent Configuration",
                border_style="cyan",
            )
        )
        return "continue"

    # Parse command arguments
    try:
        args = shlex.split(command_args)
    except ValueError as e:
        console.print(f"[red]✗ Error parsing arguments: {e}[/red]")
        return "continue"

    if not args:
        console.print("[red]Usage: /subagent <command> [args][/red]")
        console.print("[dim]Commands: list, set, clear, reset[/dim]")
        return "continue"

    subcommand = args[0].lower()

    if subcommand == "set":
        return _handle_subagent_set(console, args[1:])
    elif subcommand == "clear":
        return _handle_subagent_clear(console, args[1:])
    elif subcommand == "reset":
        return _handle_subagent_reset(console)
    else:
        console.print(f"[red]✗ Unknown subcommand: {subcommand}[/red]")
        console.print("[dim]Commands: list, set, clear, reset[/dim]")
        return "continue"


def _handle_subagent_set(console: Console, args: list[str]) -> CommandResult:
    """Handle /subagent set command."""
    if len(args) < 2:
        console.print("[red]Usage: /subagent set <type> <model>[/red]")
        console.print(f"[dim]Available types: {', '.join(list_subagent_types())}[/dim]")
        console.print("[dim]Example: /subagent set fast_general gpt-3.5-turbo[/dim]")
        return "continue"

    subagent_type = args[0]
    model = args[1]

    config_manager = get_subagent_config_manager()

    try:
        config_manager.set_model_override(subagent_type, model)
        console.print(f"[green]✓ Set {subagent_type} to use model: {model}[/green]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")

    return "continue"


def _handle_subagent_clear(console: Console, args: list[str]) -> CommandResult:
    """Handle /subagent clear command."""
    if not args:
        console.print("[red]Usage: /subagent clear <type>[/red]")
        console.print(f"[dim]Available types: {', '.join(list_subagent_types())}[/dim]")
        return "continue"

    subagent_type = args[0]
    config_manager = get_subagent_config_manager()

    if config_manager.clear_model_override(subagent_type):
        console.print(f"[green]✓ Cleared model override for {subagent_type}[/green]")
        console.print("[dim]Will now inherit from parent agent[/dim]")
    else:
        console.print(f"[yellow]⚠ No model override set for {subagent_type}[/yellow]")

    return "continue"


def _handle_subagent_reset(console: Console) -> CommandResult:
    """Handle /subagent reset command."""
    config_manager = get_subagent_config_manager()
    count = config_manager.clear_all_overrides()

    if count > 0:
        console.print(f"[green]✓ Cleared {count} model override(s)[/green]")
        console.print("[dim]All subagents will now inherit from parent agent[/dim]")
    else:
        console.print("[yellow]⚠ No model overrides to clear[/yellow]")

    return "continue"


def handle_init_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /init command to create or refine AGENTS.md file."""
    # Parse command arguments
    args = shlex.split(command_args) if command_args else []

    # Default to create, allow --refine flag
    is_refine = False
    force = False

    for arg in args:
        if arg == "--refine":
            is_refine = True
        elif arg == "--force":
            force = True

    agents_file = "AGENTS.md"

    # Check if file already exists
    file_exists = os.path.exists(agents_file)

    if file_exists and not is_refine and not force:
        console.print(
            Panel.fit(
                f"[yellow]⚠ {agents_file} already exists[/yellow]\n\n"
                f"[bold]Options:[/bold]\n"
                f"  [cyan]/init --refine[/cyan] - Enhance with project analysis\n"
                f"  [cyan]/init --force[/cyan] - Overwrite with fresh template\n"
                f"  [cyan]/init --refine --force[/cyan] - Force refine update\n\n"
                f"[dim]Use /init --refine to improve existing documentation with "
                f"project-specific insights, or --force to start fresh.[/dim]",
                title="AGENTS.md Exists",
                border_style="yellow",
            )
        )
        return "continue"

    if is_refine and file_exists:
        console.print("[cyan]Analyzing project to refine AGENTS.md...[/cyan]")
        return _refine_agents_file(agent, console)
    else:
        console.print("[cyan]Creating new AGENTS.md file...[/cyan]")
        return _create_agents_file(agent, console, force)


def _create_agents_file(agent: ClippyAgent, console: Console, force: bool = False) -> CommandResult:
    """Create a comprehensive AGENTS.md file based on project analysis."""
    from pathlib import Path

    # Analyze the project structure
    project_root = Path.cwd()

    try:
        # Read existing files to understand the project
        pyproject_content = ""
        if Path("pyproject.toml").exists():
            pyproject_content = Path("pyproject.toml").read_text()

        readme_content = ""
        if Path("README.md").exists():
            readme_content = Path("README.md").read_text()

        # Extract project name and basic info
        project_name = project_root.name
        if pyproject_content:
            # Try to extract project name from pyproject.toml
            import re

            pattern = r'^name\s*=\s*["\']([^"\']+)["\']'
            name_match = re.search(pattern, pyproject_content, re.MULTILINE)
            if name_match:
                project_name = name_match.group(1)

        # Generate comprehensive AGENTS.md content
        agents_content = _generate_agents_template(project_name, pyproject_content, readme_content)

        # Write the file
        Path("AGENTS.md").write_text(agents_content, encoding="utf-8")

        line_count = agents_content.count(chr(10)) + 1
        console.print(
            Panel.fit(
                f"[bold green]✓ Created {line_count} line AGENTS.md[/bold green]\n\n"
                f"[bold]Project:[/bold] {project_name}\n"
                f"[bold]File:[/bold] [cyan]AGENTS.md[/cyan]\n\n"
                f"[dim]The AGENTS.md file provides comprehensive guidance for AI coding agents "
                f"working with this codebase. You can refine it later with '/init --refine'.[/dim]",
                title="AGENTS.md Created",
                border_style="green",
            )
        )
        return "continue"

    except Exception as e:
        console.print(f"[red]✗ Error creating AGENTS.md: {str(e)}[/red]")
        return "continue"


def _refine_agents_file(agent: ClippyAgent, console: Console) -> CommandResult:
    """Refine existing AGENTS.md with additional project analysis."""
    import shutil
    from pathlib import Path

    try:
        # Backup existing file
        backup_file = Path("AGENTS.md.backup")
        if Path("AGENTS.md").exists():
            shutil.copy2("AGENTS.md", backup_file)
            console.print("[dim]✓ Backed up existing AGENTS.md to AGENTS.md.backup[/dim]")

        # Read existing content
        existing_content = Path("AGENTS.md").read_text()

        # Analyze project for additional insights
        project_analysis = _analyze_project_structure()

        # Refine the content
        refined_content = _enhance_agents_content(existing_content, project_analysis)

        # Write the refined file
        Path("AGENTS.md").write_text(refined_content, encoding="utf-8")

        # Show what was added/modified
        new_lines = refined_content.count(chr(10)) + 1
        old_lines = existing_content.count(chr(10)) + 1

        console.print(
            Panel.fit(
                f"[bold green]✓ Refined AGENTS.md[/bold green]\n\n"
                f"[bold]Changes:[/bold]\n"
                f"  Lines: {old_lines} → {new_lines} ({new_lines - old_lines:+d})\n"
                f"  [cyan]Enhanced project analysis[/cyan]\n"
                f"  [cyan]Updated file structure documentation[/cyan]\n"
                f"  [cyan]Added current tool catalog[/cyan]\n\n"
                f"[dim]Backup saved as AGENTS.md.backup if you need to revert.[/dim]",
                title="AGENTS.md Refined",
                border_style="green",
            )
        )
        return "continue"

    except Exception as e:
        console.print(f"[red]✗ Error refining AGENTS.md: {str(e)}[/red]")
        return "continue"


def _analyze_project_structure() -> dict[str, Any]:
    """Analyze project structure to generate insights for AGENTS.md."""
    from pathlib import Path

    analysis: dict[str, Any] = {
        "project_type": "python",
        "has_tests": False,
        "has_docs": False,
        "has_ci": False,
        "main_src_dirs": [],
        "key_files": [],
        "dependencies": [],
        "dev_commands": [],
        "tools_used": [],
    }

    # Check for common directories and files
    if Path("tests").exists() or Path("test").exists():
        analysis["has_tests"] = True
        analysis["main_src_dirs"].append("tests")

    if Path("docs").exists() or Path("documentation").exists():
        analysis["has_docs"] = True
        analysis["main_src_dirs"].append("docs")

    if Path(".github").exists() or Path(".gitlab-ci.yml").exists():
        analysis["has_ci"] = True

    # Find source directories
    for item in Path("src").iterdir() if Path("src").exists() else []:
        if item.is_dir():
            analysis["main_src_dirs"].append(f"src/{item.name}")

    if Path("clippy").exists():
        analysis["main_src_dirs"].append("clippy")

    # Look for key files
    key_file_patterns = [
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
    ]
    for pattern in key_file_patterns:
        if Path(pattern).exists():
            analysis["key_files"].append(pattern)

    # Extract dependencies and commands from pyproject.toml
    if Path("pyproject.toml").exists():
        try:
            import toml  # type: ignore

            pyproject = toml.loads(Path("pyproject.toml").read_text())

            # Get dependencies
            deps = pyproject.get("project", {}).get("dependencies", [])
            if deps:
                analysis["dependencies"] = deps[:10]  # Limit to first 10

            # Get dev commands from tool.uv.scripts or similar
            scripts = pyproject.get("tool", {}).get("uv", {}).get("scripts", {})
            if not scripts:
                # Try other common locations
                scripts = pyproject.get("project", {}).get("scripts", {})

            if scripts:
                analysis["dev_commands"] = list(scripts.keys())[:10]  # Limit to first 10

        except Exception:
            # Fallback: just add common commands
            analysis["dev_commands"] = ["install", "test", "lint", "format", "build"]

    return analysis


def _generate_agents_template(
    project_name: str, pyproject_content: str, readme_content: str
) -> str:
    """Generate a comprehensive AGENTS.md template."""

    # Extract project-specific information
    project_type = "Python"
    description = ""

    if pyproject_content:
        import re

        # Try to extract description
        desc_pattern = r'^description\s*=\s*["\']([^"\']+)["\']'
        desc_match = re.search(desc_pattern, pyproject_content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1)

    if not description and readme_content:
        # Try to get first paragraph from readme
        lines = readme_content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("*"):
                description = line[:100] + ("..." if len(line) > 100 else "")
                break

    template = f"""# AGENTS.md

This file provides guidance for AI coding agents working with the {project_name} codebase.

## Project Overview

- **Name**: {project_name}
- **Type**: {project_type} project
"""

    if description:
        template += f"""- **Description**: {description}
"""

    template += """
## Essential Commands

```bash
# Development commands (extracted from project configuration)
make dev              # Install with dev dependencies
make test             # Run pytest
make check            # Run format, lint, and type-check
make run              # Launch interactive mode through the Makefile
make format           # Autofix and format code with ruff
make lint             # Static analysis with ruff
make type-check       # Run mypy against src/clippy
python -m clippy       # Run in interactive mode
```

## Development Workflow Tips

- Prefer the `make` targets above for consistent formatting, linting, and type checks.
- Run `make check` and `make test` before finishing a task to catch regressions early.
- Use `make format` if a change requires ruff autofixes prior to committing or submitting.
- Reference README.md for installation and CONTRIBUTING.md for workflow details.

## Project Structure

```
src/clippy/
├── agent/                   # Core agent and subagent implementations
├── cli/                     # Command-line interface and REPL
├── tools/                   # Built-in tool implementations
├── mcp/                     # Model Context Protocol integration
├── models.py               # Model configuration
├── providers.py            # LLM provider handling
├── permissions.py          # Permission system
├── prompts.py              # System prompts
└── executor.py             # Tool execution engine
```

## Core Architecture

### Agent Flow
1. User input → `ClippyAgent`
2. Loop (max 100 iterations): Call LLM → Process response → Execute tools → Add results → Repeat
3. Tool execution: Check permissions → Get approval → Execute → Return results
4. Subagent delegation (optional): Spawn specialized subagents for complex tasks

### Tool System
- **Built-in tools**: File operations, code execution, search, etc.
- **MCP integration**: Dynamic external tool discovery
- **Permission system**: AUTO_APPROVE, REQUIRE_APPROVAL, DENY levels

### Model Provider System
- OpenAI-compatible API support
- Multiple providers: OpenAI, Cerebras, Groq, Mistral, Ollama, etc.
- Real-time streaming responses
- Automatic retry with exponential backoff

## Code Standards

- **Type hints**: Required (`str | None` not `Optional[str]`)
- **Line length**: 100 characters maximum
- **Formatting**: `ruff format .`
- **Type checking**: `mypy src/clippy`
- **Style**: Google-style docstrings

## Key Commands Documentation

### Session Control
- `/help` - Show all available commands
- `/exit, /quit` - Exit the application
- `/reset, /clear, /new` - Reset conversation history
- `/resume [name]` - Resume a saved conversation

### Model Management
- `/model list` - Show saved models
- `/model <name>` - Switch to a saved model
- `/model add <provider> <model_id> [options]` - Add new model
- `/model use <provider> <model_id>` - Try model temporarily

### Subagent Configuration
- `/subagent list` - Show subagent type configurations
- `/subagent set <type> <model>` - Set model for subagent type
- `/subagent clear <type>` - Clear model override

### MCP Integration
- `/mcp list` - List configured MCP servers
- `/mcp tools [server]` - List available tools
- `/mcp refresh` - Refresh server connections

### Development Workflow
- `/status` - Show token usage and session info
- `/compact` - Summarize conversation to reduce context usage
- `/auto list` - Show auto-approved actions

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - OpenAI API key
- `CEREBRAS_API_KEY` - Cerebras API key
- `OPENAI_BASE_URL` - Custom provider base URL

### Model Configuration
User models saved in `~/.clippy/models.json`
Provider presets in `src/clippy/providers.yaml`

### MCP Configuration
Server configuration in `~/.clippy/mcp.json` or `.clippy/mcp.json`

## Performance Guidelines

- **Iteration limit**: Maximum 100 iterations per request to prevent infinite loops
- **Context management**: Automatic compaction when approaching token limits
- **Streaming**: Real-time response streaming for immediate feedback
- **Caching**: Subagent result caching to avoid duplicate work

## Troubleshooting

### Common Issues
- **API key errors**: Ensure required environment variables are set
- **Model switching**: Use `/model list` to verify saved configurations
- **Memory usage**: Use `/compact` to summarize long conversations
- **Permission errors**: Check `/auto list` for auto-approved actions

### File Operations
- Auto-creates parent directories when writing files
- Uses UTF-8 encoding by default
- Respects .gitignore patterns for directory operations

## Development Tips

1. **Before making changes**: Use `/status` to check current session state
2. **After code changes**: Run `make format` and `make type-check`
3. **Before completing tasks**: Run `make test` and `make check`
4. **For complex tasks**: Consider using subagents via delegate_to_subagent tool
5. **Debug mode**: Use `/help` to see all available commands and options

---
*This file is automatically generated by `/init` and can be refined with `/init --refine`*
"""

    return template


def _enhance_agents_content(existing_content: str, analysis: dict[str, Any]) -> str:
    """Enhance existing AGENTS.md with project-specific analysis."""

    # Split content into sections
    lines = existing_content.split("\n")
    enhanced_lines: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        enhanced_lines.append(line)

        # Add project-specific enhancements after key sections
        if line.startswith("## Essential Commands"):
            # Add project-specific commands
            if analysis["dev_commands"]:
                enhanced_lines.append("\n# Project-Specific Commands (Auto-discovered)")
                for cmd in analysis["dev_commands"][:8]:
                    enhanced_lines.append(f"#   make {cmd}")
                enhanced_lines.append("")

        elif line.startswith("## Project Structure"):
            # Add analyzed structure
            if analysis["main_src_dirs"]:
                enhanced_lines.append("\n# Discovered Structure:")
                for dir_path in analysis["main_src_dirs"]:
                    enhanced_lines.append(f"#   {dir_path}/ - Project directory")
                enhanced_lines.append("")

        elif line.startswith("## Code Standards") or line.startswith("## Style Guidelines"):
            # Add project-specific insights
            if analysis["dependencies"]:
                enhanced_lines.append("\n# Key Dependencies:")
                for dep in analysis["dependencies"][:5]:
                    enhanced_lines.append(f"#   - {dep}")
                enhanced_lines.append("")

        i += 1

    # Add timestamp and refinement notice
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    analysis_summary = (
        f"*Project analysis: {len(analysis['main_src_dirs'])} dirs, "
        f"{len(analysis['key_files'])} key files*"
    )

    enhanced_lines.extend(
        ["", "---", f"*Last refined: {timestamp} by `/init --refine`*", analysis_summary]
    )

    return "\n".join(enhanced_lines)


def handle_command(user_input: str, agent: ClippyAgent, console: Console) -> CommandResult | None:
    """
    Handle slash commands in interactive mode.

    Returns:
        CommandResult if a command was handled, None if not a command
        If input starts with "/" but is not a valid command, returns "invalid_command"
    """
    command_lower = user_input.lower()

    # Exit commands
    if command_lower in ["/exit", "/quit"]:
        return handle_exit_command(console)

    # Reset commands
    if command_lower in ["/reset", "/clear", "/new"]:
        return handle_reset_command(agent, console)

    # Resume command
    if command_lower.startswith("/resume"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_resume_command(agent, console, command_args)

    # Help command
    if command_lower == "/help":
        return handle_help_command(console)

    # Init command
    if command_lower.startswith("/init"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_init_command(agent, console, command_args)

    # Status command
    if command_lower == "/status":
        return handle_status_command(agent, console)

    # Compact command
    if command_lower == "/compact":
        return handle_compact_command(agent, console)

    # Provider commands
    if command_lower == "/providers":
        return handle_providers_command(console)

    if command_lower.startswith("/provider "):
        parts = user_input.split(maxsplit=1)
        if len(parts) > 1:
            return handle_provider_command(console, parts[1])
        else:
            console.print("[red]Usage: /provider <name>[/red]")
            return "continue"

    # Model commands
    if command_lower == "/model" or command_lower.startswith("/model "):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_model_command(agent, console, command_args)

    # Subagent commands
    if command_lower.startswith("/subagent"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_subagent_command(agent, console, command_args)

    # Auto-approval commands
    if command_lower.startswith("/auto"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_auto_command(agent, console, command_args)

    # MCP commands
    if command_lower.startswith("/mcp"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_mcp_command(agent, console, command_args)

    # Truncate command
    if command_lower.startswith("/truncate"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_truncate_command(agent, console, command_args)

    # YOLO command
    if command_lower == "/yolo":
        return handle_yolo_command(agent, console)

    # Not a recognized command
    return None


def handle_yolo_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /yolo command to toggle YOLO mode."""
    # Toggle yolo mode
    current_yolo = getattr(agent, "yolo_mode", False)
    new_yolo = not current_yolo

    # Set yolo mode on agent
    agent.yolo_mode = new_yolo

    if new_yolo:
        console.print(
            Panel.fit(
                "[bold red]🔥 YOLO MODE ACTIVATED! 🔥[/bold red]\n\n"
                "[bold yellow]⚠ WARNING: All actions will be auto-approved "
                "without prompts![/bold yellow]\n\n"
                "[bold]What this means:[/bold]\n"
                "  • Every tool execution will be approved automatically\n"
                "  • No confirmation prompts for any operations\n"
                "  • File writes, deletes, and executes run without approval\n"
                "  • MCP tools run without trust checks\n\n"
                "[bold dim]Use /yolo again to disable YOLO mode\n"
                "Use with extreme caution - you're in charge! 📎[/bold dim]",
                title="YOLO Mode",
                border_style="red",
            )
        )
    else:
        console.print(
            Panel.fit(
                "[bold green]✓ YOLO Mode Disabled[/bold green]\n\n"
                "[dim]Normal permission checks have been restored.\n"
                "Actions will require approval again.[/dim]",
                title="Safety Restored",
                border_style="green",
            )
        )

    return "continue"


def handle_truncate_command(
    agent: ClippyAgent, console: Console, command_args: str
) -> CommandResult:
    """Handle /truncate command."""
    # Parse command arguments
    args = shlex.split(command_args) if command_args else []

    # If no arguments, show usage
    if not args:
        console.print("[red]Usage: /truncate <count> <option>[/red]")
        console.print(
            "[dim]Truncates conversation history. Options:[/dim]\n"
            "[dim]  /truncate <count> (default) - Keep last <count> messages[/dim]\n"
            "[dim]  /truncate <count> --keep-recent - Keep last <count> messages[/dim]\n"
            "[dim]  /truncate <count> --keep-older - Keep first <count> non-system messages[/dim]\n"
            ""
        )
        return "continue"

    try:
        count = int(args[0])
        if count < 0:
            console.print("[red]Count must be a positive integer[/red]")
            return "continue"
    except ValueError:
        console.print(f"[red]Invalid count: {args[0]}[/red]")
        console.print("[dim]Usage: /truncate <count> <option>[/dim]")
        return "continue"

    # Parse options
    option = "keep-recent"  # default behavior
    if len(args) > 1:
        option = args[1].lower()
        valid_options = {"--keep-recent", "--keep-older"}
        if option not in valid_options:
            console.print(f"[red]Invalid option: {args[1]}[/red]")
            console.print("[dim]Valid options: --keep-recent, --keep-older[/dim]")
            return "continue"

    # Get current conversation history
    history = agent.conversation_history

    # Need at least system message
    if not history:
        console.print("[yellow]No conversation history to truncate[/yellow]")
        return "continue"

    # Find system message (should be first)
    system_msg = None
    non_system_messages = []

    for msg in history:
        if msg.get("role") == "system":
            system_msg = msg
        else:
            non_system_messages.append(msg)

    # If no system message found, that's unexpected but we'll handle it
    if system_msg is None and non_system_messages:
        # Assume first message is system if it has content that looks like a system prompt
        first_msg = history[0]
        if first_msg.get("role") == "system" or len(first_msg.get("content", "")) > 1000:
            system_msg = first_msg
            non_system_messages = history[1:]
        else:
            # No clear system message, just keep the recent messages
            system_msg = None
            non_system_messages = history

    total_messages = len(non_system_messages)

    # Edge case: if there are no non-system messages
    if total_messages == 0:
        console.print("[yellow]No non-system messages to truncate[/yellow]")
        return "continue"

    # Handle different truncation options
    if option in {"keep-recent", "--keep-recent", "default"}:
        # Default behavior - keep last 'count' messages
        if count == 0:
            # Keep only system prompt
            if system_msg is not None:
                agent.conversation_history = [system_msg]
                console.print("[green]Conversation truncated to system prompt only[/green]")
            else:
                agent.conversation_history = []
                console.print("[green]Conversation cleared (no system prompt retained)[/green]")
            return "continue"

        messages_to_keep = (
            non_system_messages[-count:] if count < total_messages else non_system_messages
        )
        removed_count = total_messages - len(messages_to_keep)

        if system_msg is not None:
            agent.conversation_history = [system_msg] + messages_to_keep
        else:
            agent.conversation_history = messages_to_keep

        console.print(
            f"[green]Conversation truncated: {removed_count} messages removed, "
            f"{len(messages_to_keep)} messages kept (recent)[/green]"
        )

    elif option in {"--keep-older", "keep-older"}:
        # Keep first 'count' non-system messages
        if count == 0:
            # Keep only system prompt
            if system_msg is not None:
                agent.conversation_history = [system_msg]
                console.print("[green]Conversation truncated to system prompt only[/green]")
            else:
                agent.conversation_history = []
                console.print("[green]Conversation cleared (no system prompt retained)[/green]")
            return "continue"

        messages_to_keep = (
            non_system_messages[:count] if count < total_messages else non_system_messages
        )
        removed_count = total_messages - len(messages_to_keep)

        if system_msg is not None:
            agent.conversation_history = [system_msg] + messages_to_keep
        else:
            agent.conversation_history = messages_to_keep

        console.print(
            f"[green]Conversation truncated: {removed_count} messages removed, "
            f"{len(messages_to_keep)} messages kept (older)[/green]"
        )

    ""

    if system_msg is not None:
        console.print("[dim]System prompt retained[/dim]")

    return "continue"
