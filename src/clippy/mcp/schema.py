"""MCP schema mapping utilities."""

from typing import Any

from mcp import types

from .naming import format_mcp_tool_name


def map_mcp_to_openai(mcp_tool: types.Tool, server_id: str) -> dict[str, Any]:
    """
    Map an MCP tool schema to OpenAI tool schema format.

    Args:
        mcp_tool: MCP tool definition
        server_id: Server identifier

    Returns:
        OpenAI-style tool definition
    """
    # Format the tool name with server qualification
    qualified_name = format_mcp_tool_name(server_id, mcp_tool.name)

    # Format description with server information
    description = _format_description(server_id, mcp_tool.description or "")

    # Convert input schema
    parameters = _convert_input_schema(mcp_tool.inputSchema)

    return {
        "type": "function",
        "function": {"name": qualified_name, "description": description, "parameters": parameters},
    }


def _format_description(server_id: str, original_description: str) -> str:
    """
    Format tool description with server information.

    Args:
        server_id: Server identifier
        original_description: Original tool description

    Returns:
        Formatted description
    """
    return f"[MCP {server_id}] {original_description}"


def _convert_input_schema(input_schema: dict[str, Any] | None) -> dict[str, Any]:
    """
    Convert MCP input schema to OpenAI parameters format.

    Args:
        input_schema: MCP tool input schema

    Returns:
        OpenAI-style parameters definition
    """
    if input_schema is None:
        return {}

    # In many cases, we can pass through the schema directly since MCP uses JSON Schema
    # which is compatible with OpenAI's parameter specification
    return input_schema.copy()
