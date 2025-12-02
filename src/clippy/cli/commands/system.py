"""System status and control commands for interactive CLI mode."""

from typing import Literal

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from ...agent import ClippyAgent

CommandResult = Literal["continue", "break", "run"]


def handle_help_command(console: Console) -> CommandResult:
    """Handle /help command."""
    # Get custom commands help
    from ..custom_commands import get_custom_manager

    custom_manager = get_custom_manager()
    custom_help = custom_manager.help_text()

    # Build help content
    help_content = (
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
        "[bold]Authentication:[/bold]\n"
        "  clippy auth - Authenticate with Claude Code OAuth\n"
        "  clippy auth-status - Check Claude Code authentication status\n\n"
        "[bold]Model Management:[/bold]\n"
        "  /model - List available subcommands and models\n"
        "  /model help - Show comprehensive model management help\n"
        "  /model list - Show your saved models\n"
        "  /model <name> - Switch to a saved model\n"
        "  /model load <name> - Load model (same as direct switch)\n"
        "  /model add [options] - Interactive wizard to add a new model\n"
        "    Options: --name <name>, --default, --threshold <tokens>\n"
        "    Examples: /model add (wizard) or /model add claude-code claude-4-5 --name sonnet\n"
        "  /model remove <name> - Remove a saved model\n"
        "  /model set-default <name> - Set model as default (permanent)\n"
        "  /model threshold <name> <tokens> - Set compaction threshold\n"
        "  /model use <provider> <model_id> - Try a model without saving\n\n"
        "[bold]Subagent Configuration:[/bold]\n"
        "  /subagent list - Show subagent type configurations\n"
        "  /subagent set <type> <model> - Set model for a subagent type\n"
        "  /subagent clear <type> - Clear model override for a subagent type\n"
        "  /subagent reset - Clear all model overrides\n\n"
        "[bold]Providers:[/bold]\n"
        "  /provider list - List available providers\n"
        "  /provider <name> - Show provider details\n"
        "  /provider add - Add a new provider (interactive wizard)\n"
        "  /provider remove <name> - Remove a user-defined provider\n\n"
        "[bold]Permissions:[/bold]\n"
        "  /auto list - List auto-approved actions\n"
        "  /auto revoke <action> - Revoke auto-approval for an action\n"
        "  /auto clear - Clear all auto-approvals\n"
        "  /yolo - Toggle YOLO mode (auto-approve ALL actions)\n\n"
        "[bold]MCP Servers:[/bold]\n"
        "  /mcp help - Show comprehensive MCP server management help\n"
        "  /mcp list - List configured MCP servers\n"
        "  /mcp tools [server] - List tools available from MCP servers\n"
        "  /mcp refresh - Refresh tool catalogs from MCP servers\n"
        "  /mcp allow <server> - Mark an MCP server as trusted for this session\n"
        "  /mcp revoke <server> - Revoke trust for an MCP server\n"
        "  /mcp enable <server> - Enable a disabled MCP server\n"
        "  /mcp disable <server> - Disable an enabled MCP server\n\n"
        "[bold]Custom Commands:[/bold]\n"
        "  /custom list - List all custom commands\n"
        "  /custom reload - Reload custom commands from disk\n"
        "  /custom edit [editor] - Edit custom commands configuration\n"
        "  /custom example - Show example configuration\n"
        "  /custom help - Show custom command management help\n\n"
        "[bold]Interrupt:[/bold]\n"
        "  Ctrl+C or double-ESC - Stop current execution"
    )

    # Add custom commands section if any exist
    if custom_help:
        help_content += f"\n\n{custom_help}"

    console.print(
        Panel.fit(
            help_content,
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


def handle_yolo_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /yolo command (toggle auto-approve all actions)."""
    new_state = agent.toggle_yolo_mode()

    if new_state:
        console.print(
            Panel.fit(
                "[bold yellow]⚠ YOLO MODE ENABLED ⚠[/bold yellow]\n\n"
                "[bold]All actions will be auto-approved![/bold]\n"
                "[dim]Be careful! This bypasses all safety checks.[/dim]\n\n"
                "[dim]Use /yolo again to disable.[/dim]",
                title="YOLO Mode",
                border_style="yellow",
            )
        )
    else:
        console.print(
            Panel.fit(
                "[bold green]✓ YOLO MODE DISABLED[/bold green]\n\n"
                "[bold]Normal permission checking restored.[/bold]\n"
                "[dim]Actions will require manual approval again.[/dim]",
                title="YOLO Mode",
                border_style="green",
            )
        )

    return "continue"
