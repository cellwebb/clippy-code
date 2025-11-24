"""MCP (Model Context Protocol) commands for interactive CLI mode."""

from typing import Literal

from rich.console import Console
from rich.panel import Panel

from ...agent import ClippyAgent

CommandResult = Literal["continue", "break", "run"]


def handle_mcp_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /mcp commands for managing MCP server configurations."""
    if not command_args:
        console.print("Usage: /mcp [list|tools|refresh|allow|revoke]")
        return "continue"

    parts = command_args.strip().split(maxsplit=1)
    subcommand = parts[0].lower()

    if subcommand == "list":
        return _handle_mcp_list(agent, console)
    elif subcommand == "tools":
        server_name = parts[1] if len(parts) > 1 else None
        return _handle_mcp_tools(agent, console, server_name)
    elif subcommand == "refresh":
        return _handle_mcp_refresh(agent, console)
    elif subcommand == "allow":
        if len(parts) < 2:
            console.print("Usage: /mcp allow <server_name>")
            return "continue"
        return _handle_mcp_allow(agent, console, parts[1])
    elif subcommand == "revoke":
        if len(parts) < 2:
            console.print("Usage: /mcp revoke <server_name>")
            return "continue"
        return _handle_mcp_revoke(agent, console, parts[1])
    else:
        console.print(f"Unknown MCP command: {subcommand}")
        return "continue"


def _handle_mcp_help(console: Console) -> CommandResult:
    """Display help for MCP commands."""
    help_text = """
[bold cyan]/mcp commands:[/bold cyan]

  [cyan]/mcp[/cyan]                        - Show this help
  [cyan]/mcp list[/cyan]                   - List MCP servers
  [cyan]/mcp add <name> <command> [args][/cyan]
                                   - Add an MCP server
  [cyan]/mcp remove <name>[/cyan]          - Remove an MCP server
  [cyan]/mcp restart <name>[/cyan]         - Restart an MCP server
  [cyan]/mcp restart-all[/cyan]            - Restart all MCP servers

[dim]MCP servers provide additional tools and capabilities to the AI assistant[/dim]
"""
    console.print(Panel.fit(help_text.strip(), title="MCP Help", border_style="cyan"))
    return "continue"


def _handle_mcp_list(agent: ClippyAgent, console: Console) -> CommandResult:
    """List configured MCP servers."""
    if agent.mcp_manager is None:
        console.print("MCP functionality not available")
        return "continue"

    servers = agent.mcp_manager.list_servers()
    if not servers:
        console.print("No MCP servers configured")
        return "continue"

    for server in servers:
        console.print(
            f"Server: {server['server_id']}, Connected: {server['connected']}, "
            f"Tools: {server['tools_count']}"
        )

    return "continue"


def _handle_mcp_tools(agent: ClippyAgent, console: Console, server: str | None) -> CommandResult:
    """List tools from MCP servers."""
    if agent.mcp_manager is None:
        console.print("MCP functionality not available")
        return "continue"

    tools = agent.mcp_manager.list_tools(server)
    if not tools:
        console.print("No tools available" if not server else f"No tools for server: {server}")
        return "continue"

    for tool in tools:
        console.print(f"  {tool['name']}: {tool['description']}")

    return "continue"


def _handle_mcp_refresh(agent: ClippyAgent, console: Console) -> CommandResult:
    """Refresh MCP server connections."""
    if agent.mcp_manager is None:
        console.print("MCP functionality not available")
        return "continue"

    console.print("Refreshing MCP connections...")
    agent.mcp_manager.start()
    agent.mcp_manager.stop()
    console.print("MCP connections refreshed")
    return "continue"


def _handle_mcp_allow(agent: ClippyAgent, console: Console, server_id: str) -> CommandResult:
    """Allow (trust) an MCP server."""
    if agent.mcp_manager is None:
        console.print("MCP functionality not available")
        return "continue"

    agent.mcp_manager.set_trusted(server_id, True)
    console.print(f"Allowed server: {server_id}")
    return "continue"


def _handle_mcp_revoke(agent: ClippyAgent, console: Console, server_id: str) -> CommandResult:
    """Revoke trust from an MCP server."""
    if agent.mcp_manager is None:
        console.print("MCP functionality not available")
        return "continue"

    agent.mcp_manager.set_trusted(server_id, False)
    console.print(f"Revoked server: {server_id}")
    return "continue"


__all__ = [
    "handle_mcp_command",
    "CommandResult",
]
