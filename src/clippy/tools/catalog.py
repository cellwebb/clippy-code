"""Tool catalog for merging built-in and MCP tools."""

from typing import Any

from ..mcp.manager import Manager
from ..tools import TOOLS as BUILTIN_TOOLS


def get_builtin_tools() -> list[dict[str, Any]]:
    """
    Get all built-in tools.

    Returns:
        List of built-in tool definitions in OpenAI format
    """
    return BUILTIN_TOOLS


def get_mcp_tools(mgr: Manager | None) -> list[dict[str, Any]]:
    """
    Get all MCP tools from connected servers.

    Args:
        mgr: MCP Manager instance or None

    Returns:
        List of MCP tool definitions in OpenAI format
    """
    if mgr is None:
        return []

    try:
        return mgr.get_all_tools_openai()
    except Exception:
        # Gracefully handle MCP errors
        return []


def get_all_tools(mgr: Manager | None) -> list[dict[str, Any]]:
    """
    Get all available tools (built-in + MCP).

    Args:
        mgr: MCP Manager instance or None

    Returns:
        List of all tool definitions in OpenAI format
    """
    builtin_tools = get_builtin_tools()
    mcp_tools = get_mcp_tools(mgr)

    # Combine tools, MCP tools override built-in tools with same names
    all_tools = builtin_tools.copy()

    # Create a set of built-in tool names for quick lookup
    builtin_names = {tool["function"]["name"] for tool in builtin_tools}

    # Add MCP tools, replacing any built-in tools with the same name
    for mcp_tool in mcp_tools:
        tool_name = mcp_tool["function"]["name"]
        if tool_name in builtin_names:
            # Replace the built-in tool
            for i, tool in enumerate(all_tools):
                if tool["function"]["name"] == tool_name:
                    all_tools[i] = mcp_tool
                    break
        else:
            # Add new MCP tool
            all_tools.append(mcp_tool)

    return all_tools


def is_mcp_tool(name: str) -> bool:
    """
    Check if a tool name is an MCP tool.

    Args:
        name: Tool name to check

    Returns:
        True if the tool name is an MCP tool (starts with "mcp__")
    """
    return name.startswith("mcp__")
