"""MCP tool naming utilities."""


def is_mcp_tool(name: str) -> bool:
    """
    Check if a tool name is an MCP tool.

    Args:
        name: Tool name to check

    Returns:
        True if the tool name is an MCP tool (starts with "mcp__" and has server and tool parts)
    """
    if not name.startswith("mcp__"):
        return False

    parts = name.split("__", 2)
    # Return True if we have exactly 3 parts and the server/tool parts are not empty
    return len(parts) == 3 and bool(parts[1]) and bool(parts[2])


def parse_mcp_qualified_name(name: str) -> tuple[str, str]:
    """
    Parse an MCP qualified tool name.

    Args:
        name: MCP qualified tool name (format: "mcp__{server_id}__{tool_name}")

    Returns:
        Tuple of (server_id, tool_name)

    Raises:
        ValueError: If name is not a valid MCP qualified name
    """
    if not is_mcp_tool(name):
        raise ValueError(f"Not an MCP tool name: {name}")

    parts = name.split("__", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid MCP tool name format: {name}")

    return parts[1], parts[2]  # server_id, tool_name


def format_mcp_tool_name(server_id: str, tool_name: str) -> str:
    """
    Format an MCP tool name.

    Args:
        server_id: Server identifier
        tool_name: Tool name

    Returns:
        MCP qualified tool name (format: "mcp__{server_id}__{tool_name}")
    """
    return f"mcp__{server_id}__{tool_name}"
