"""MCP-specific exceptions."""


class MCPError(Exception):
    """Base exception for MCP-related errors."""

    pass


class MCPConnectionError(MCPError):
    """Error connecting to an MCP server."""

    pass


class MCPToolError(MCPError):
    """Error executing an MCP tool."""

    pass


class MCPToolNotFoundError(MCPError):
    """MCP tool not found."""

    pass


class MCPTimeoutError(MCPError):
    """MCP operation timed out."""

    pass


class MCPPermissionError(MCPError):
    """Permission denied for MCP operation."""

    pass
