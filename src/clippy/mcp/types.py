"""MCP type definitions."""

from typing import Any


class ServerInfo:
    """Information about an MCP server."""

    def __init__(self, server_id: str, name: str, description: str, connection_status: str) -> None:
        """
        Initialize server info.

        Args:
            server_id: Server identifier
            name: Server name
            description: Server description
            connection_status: Connection status ("connected", "disconnected", "error")
        """
        self.server_id = server_id
        self.name = name
        self.description = description
        self.connection_status = connection_status


class TargetTool:
    """Information about an MCP tool."""

    def __init__(
        self, server_id: str, tool_name: str, description: str, input_schema: dict[str, Any]
    ) -> None:
        """
        Initialize tool info.

        Args:
            server_id: Server identifier
            tool_name: Tool name
            description: Tool description
            input_schema: Tool input schema
        """
        self.server_id = server_id
        self.tool_name = tool_name
        self.description = description
        self.input_schema = input_schema
