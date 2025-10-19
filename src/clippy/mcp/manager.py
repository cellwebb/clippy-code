"""MCP Manager for handling connections to MCP servers."""

import asyncio
import logging
from typing import Any

from mcp import StdioServerParameters, types
from mcp.client.stdio import stdio_client
from rich.console import Console

from .config import Config
from .schema import map_mcp_to_openai
from .trust import TrustStore

logger = logging.getLogger(__name__)


class Manager:
    """Manages MCP server connections and tool execution."""

    def __init__(self, config: Config | None = None, console: Console | None = None) -> None:
        """
        Initialize the MCP Manager.

        Args:
            config: MCP configuration
            console: Rich console for output
        """
        self.config = config or Config(mcp_servers={})
        self.console = console
        self._sessions: dict[str, Any] = {}  # Server ID -> session
        self._tools: dict[str, list[types.Tool]] = {}  # Server ID -> tools
        self._trust_store = TrustStore()

    async def start(self) -> None:
        """Start the MCP manager and initialize connections."""
        # Initialize all configured servers
        for server_id, server_config in self.config.mcp_servers.items():
            try:
                # Create stdio transport parameters
                params = StdioServerParameters(
                    command=server_config.command,
                    args=server_config.args,
                    env=server_config.env,
                    cwd=server_config.cwd,
                )

                # Create session context manager
                session_context = stdio_client(params)
                self._sessions[server_id] = session_context

                # Connect session
                await self._connect_session(server_id, session_context)

                if self.console:
                    self.console.print(f"[green]✓ Connected to MCP server '{server_id}'[/green]")

            except Exception as e:
                logger.warning(f"Failed to connect to MCP server '{server_id}': {e}")
                if self.console:
                    error_msg = (
                        f"[yellow]⚠ Failed to connect to MCP server '{server_id}': {e}[/yellow]"
                    )
                    self.console.print(error_msg)

    async def _connect_session(self, server_id: str, session_context: Any) -> None:
        """Connect a session and initialize tools."""
        async with session_context as session:
            # Initialize with tools capability
            await session.initialize(types.ClientCapabilities())

            # List available tools
            tools_result = await session.list_tools()
            self._tools[server_id] = tools_result.tools or []

    async def stop(self) -> None:
        """Stop the MCP manager and close connections."""
        # Close all sessions
        for session_context in self._sessions.values():
            try:
                # Sessions are async context managers
                if hasattr(session_context, "__aexit__"):
                    await session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing MCP session: {e}")

        self._sessions.clear()
        self._tools.clear()

    def list_servers(self) -> list[dict[str, Any]]:
        """
        List available MCP servers.

        Returns:
            List of server information
        """
        servers = []
        for server_id in self.config.mcp_servers.keys():
            connected = server_id in self._sessions
            servers.append(
                {
                    "server_id": server_id,
                    "connected": connected,
                    "tools_count": len(self._tools.get(server_id, [])),
                }
            )
        return servers

    def list_tools(self, server_id: str | None = None) -> list[dict[str, Any]]:
        """
        List tools available from MCP servers.

        Args:
            server_id: Optional specific server ID to list tools for

        Returns:
            List of tools
        """
        tools = []

        if server_id:
            # List tools for specific server
            if server_id in self._tools:
                for tool in self._tools[server_id]:
                    tools.append(
                        {"server_id": server_id, "name": tool.name, "description": tool.description}
                    )
        else:
            # List tools for all servers
            for sid, server_tools in self._tools.items():
                for tool in server_tools:
                    tools.append(
                        {"server_id": sid, "name": tool.name, "description": tool.description}
                    )

        return tools

    def get_all_tools_openai(self) -> list[dict[str, Any]]:
        """
        Get all MCP tools mapped to OpenAI format.

        Returns:
            List of OpenAI-style tool definitions
        """
        openai_tools = []

        for server_id, server_tools in self._tools.items():
            for tool in server_tools:
                try:
                    openai_tool = map_mcp_to_openai(tool, server_id)
                    openai_tools.append(openai_tool)
                except Exception as e:
                    logger.warning(
                        f"Failed to map MCP tool '{tool.name}' from server '{server_id}': {e}"
                    )
                    if self.console:
                        error_msg = (
                            f"[yellow]⚠ Failed to map MCP tool '{tool.name}' "
                            f"from server '{server_id}'[/yellow]"
                        )
                        self.console.print(error_msg)

        return openai_tools

    def execute(
        self, server_id: str, tool_name: str, args: dict[str, Any]
    ) -> tuple[bool, str, Any]:
        """
        Execute an MCP tool call.

        Args:
            server_id: Server identifier
            tool_name: Tool name
            args: Tool arguments

        Returns:
            Tuple of (success: bool, message: str, result: Any)
        """
        # Check if server is configured
        if server_id not in self.config.mcp_servers:
            return False, f"MCP server '{server_id}' not configured", None

        # Check if we're connected to the server
        if server_id not in self._sessions:
            return False, f"Not connected to MCP server '{server_id}'", None

        # Check trust
        if not self._trust_store.is_trusted(server_id):
            return False, f"MCP server '{server_id}' not trusted", None

        session_context = self._sessions[server_id]

        try:
            # Execute tool call
            result = asyncio.run(self._execute_tool(session_context, tool_name, args))
            return True, f"Successfully executed MCP tool '{tool_name}'", result
        except Exception as e:
            logger.error(f"Error executing MCP tool '{tool_name}' on server '{server_id}': {e}")
            error_msg = f"Error executing MCP tool '{tool_name}': {str(e)}"
            return False, error_msg, None

    async def _execute_tool(
        self, session_context: Any, tool_name: str, args: dict[str, Any]
    ) -> Any:
        """Execute a tool call asynchronously."""
        async with session_context as session:
            result = await session.call_tool(tool_name, args)
            return result

    def is_trusted(self, server_id: str) -> bool:
        """
        Check if a server is trusted.

        Args:
            server_id: Server identifier

        Returns:
            True if server is trusted
        """
        return self._trust_store.is_trusted(server_id)

    def set_trusted(self, server_id: str, trusted: bool) -> None:
        """
        Set server trust status.

        Args:
            server_id: Server identifier
            trusted: Trust status
        """
        self._trust_store.set_trusted(server_id, trusted)
