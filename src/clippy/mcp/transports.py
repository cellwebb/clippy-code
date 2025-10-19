"""MCP transport implementations."""

from typing import Any


class BaseTransport:
    """Base class for MCP transports."""

    def __init__(self) -> None:
        pass

    async def connect(self) -> None:
        """Connect to the MCP server."""
        pass

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Send a request to the MCP server.

        Args:
            request: Request data

        Returns:
            Response data
        """
        return {}


class StdioTransport(BaseTransport):
    """Stdio transport for MCP servers."""

    def __init__(
        self,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> None:
        """
        Initialize stdio transport.

        Args:
            command: Command to execute
            args: Arguments for command
            env: Environment variables
            cwd: Working directory
        """
        super().__init__()
        self.command = command
        self.args = args
        self.env = env
        self.cwd = cwd
