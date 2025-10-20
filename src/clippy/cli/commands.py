"""Command handlers for interactive CLI mode."""

import os
import shlex
from typing import Any, Literal

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from ..agent import ClippyAgent
from ..models import (
    get_model_config,
    get_provider,
    get_user_manager,
    list_available_models,
    list_available_providers,
)
from ..permissions import ActionType, PermissionLevel

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
            "  /exit, /quit - Exit clippy-code\n"
            "  /reset, /clear, /new - Reset conversation history\n"
            "  /status - Show token usage and session info\n"
            "  /compact - Summarize conversation to reduce context usage\n"
            "  /providers - List available providers\n"
            "  /provider <name> - Show provider details\n"
            "  /model list - Show your saved models\n"
            "  /model add <provider> <model_id> [options] - Add a new model\n"
            "  /model remove <name> - Remove a saved model\n"
            "  /model default <name> - Set model as default\n"
            "  /model use <provider> <model_id> - Try a model without saving\n"
            "  /model <name> - Switch to saved model\n"
            "  /auto list - List auto-approved actions\n"
            "  /auto revoke <action> - Revoke auto-approval for an action\n"
            "  /auto clear - Clear all auto-approvals\n"
            "  /mcp list - List configured MCP servers\n"
            "  /mcp tools [server] - List tools available from MCP servers\n"
            "  /mcp refresh - Refresh tool catalogs from MCP servers\n"
            "  /mcp allow <server> - Mark an MCP server as trusted for this session\n"
            "  /mcp revoke <server> - Revoke trust for an MCP server\n"
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
                    '  /model add cerebras qwen-3-coder-480b --name "q3c"[/dim]',
                    title="Models",
                    border_style="yellow",
                )
            )
            return "continue"

        model_lines = []
        for name, desc, is_default in models:
            default_indicator = " [green](default)[/green]" if is_default else ""
            model_lines.append(f"  [cyan]{name:20}[/cyan] - {desc}{default_indicator}")

        current_model = agent.model
        current_provider = agent.base_url or "OpenAI"

        console.print(
            Panel.fit(
                "[bold]Your Saved Models:[/bold]\n\n" + "\n".join(model_lines) + f"\n\n"
                f"[bold]Current:[/bold] {current_model} ({current_provider})\n\n"
                f"[dim]Usage: /model <name> to switch[/dim]",
                title="Models",
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
    else:
        # Treat as model name to switch to
        return _handle_model_switch(agent, console, command_args)


def _handle_model_add(console: Console, args: list[str]) -> CommandResult:
    """Handle /model add command."""
    if len(args) < 2:
        console.print(
            "[red]Usage: /model add <provider> <model_id> [options][/red]\n"
            "[dim]Options: --name <name>, --default[/dim]"
        )
        console.print(
            '[dim]Example: /model add cerebras qwen-3-coder-480b --name "q3c" --default[/dim]'
        )
        return "continue"

    provider = args[0]
    model_id = args[1]

    # Parse optional arguments
    name = None
    is_default = False

    i = 2
    while i < len(args):
        if args[i] == "--name" and i + 1 < len(args):
            name = args[i + 1]
            i += 2
        elif args[i] == "--default":
            is_default = True
            i += 1
        else:
            console.print(f"[red]✗ Unknown argument: {args[i]}[/red]")
            return "continue"

    # Use model_id as name if not specified
    if not name:
        name = model_id.replace(":", "-").replace("/", "-")

    # Add the model
    user_manager = get_user_manager()
    success, message = user_manager.add_model(name, provider, model_id, is_default)

    if success:
        console.print(f"[green]✓ {message}[/green]")
        if is_default:
            console.print("[dim]Set as default model[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")

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
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[red]✗ {message}[/red]")

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
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[red]✗ {message}[/red]")

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
        console.print(f"[green]✓ Using {provider_name}/{model_id} (temporary)[/green]")
        console.print("[dim]Use /model add to save this configuration[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")

    return "continue"


def _handle_model_switch(agent: ClippyAgent, console: Console, model_name: str) -> CommandResult:
    """Handle switching to a saved model."""
    model, provider = get_model_config(model_name)

    if not model or not provider:
        console.print(f"[red]✗ Model '{model_name}' not found[/red]")
        console.print("[dim]Use /model list to see your saved models[/dim]")
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
        console.print(f"[green]✓ Switched to {model.name}[/green]")
        console.print(f"[dim]Using {provider.name}/{model.model_id}[/dim]")
    else:
        console.print(f"[red]✗ {message}[/red]")

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
        console.print("[dim]Available commands: list, tools, refresh, allow, revoke[/dim]")
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
    else:
        console.print(f"[red]Unknown MCP command: {subcommand}[/red]")
        console.print("[dim]Available commands: list, tools, refresh, allow, revoke[/dim]")

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
        server_lines.append(
            f"  [cyan]{server['server_id']:20}[/cyan] - {status} ({server['tools_count']} tools)"
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
        import asyncio

        asyncio.run(mcp_manager.stop())
        asyncio.run(mcp_manager.start())
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
    if command_lower.startswith("/model"):
        parts = user_input.split(maxsplit=1)
        command_args = parts[1] if len(parts) > 1 else ""
        return handle_model_command(agent, console, command_args)

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

    # Not a recognized command
    return None
