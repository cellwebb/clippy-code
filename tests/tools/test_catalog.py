"""Tests for the tools catalog module."""

import copy

from clippy.tools.catalog import get_all_tools, get_builtin_tools, get_mcp_tools, is_mcp_tool


def test_get_builtin_tools() -> None:
    """Test that we can get builtin tools."""
    tools = get_builtin_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0

    # Check that all tools have the expected structure
    for tool in tools:
        assert "type" in tool
        assert "function" in tool
        assert isinstance(tool["function"], dict)
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]


def test_get_mcp_tools_with_none_manager() -> None:
    """Test that get_mcp_tools returns empty list when manager is None."""
    tools = get_mcp_tools(None)
    assert isinstance(tools, list)
    assert len(tools) == 0


def test_get_all_tools_with_none_manager() -> None:
    """Test that get_all_tools works when manager is None."""
    tools = get_all_tools(None)
    builtin_tools = get_builtin_tools()

    # Should be the same as builtin tools when no MCP manager
    assert isinstance(tools, list)
    assert len(tools) == len(builtin_tools)

    # Check that all builtin tools are present
    builtin_names = {tool["function"]["name"] for tool in builtin_tools}
    all_names = {tool["function"]["name"] for tool in tools}
    assert builtin_names == all_names


def test_is_mcp_tool() -> None:
    """Test MCP tool name detection."""
    # MCP tools start with "mcp__"
    assert is_mcp_tool("mcp__server__tool") is True
    assert is_mcp_tool("mcp__another_server__another_tool") is True

    # Regular tools don't start with "mcp__"
    assert is_mcp_tool("read_file") is False
    assert is_mcp_tool("write_file") is False
    assert is_mcp_tool("list_directory") is False


def test_get_mcp_tools_handles_errors() -> None:
    """Manager errors should be swallowed and return empty tool lists."""

    class FailingManager:
        def get_all_tools_openai(self) -> list[dict[str, str]]:
            raise RuntimeError("boom")

    assert get_mcp_tools(FailingManager()) == []


def test_get_all_tools_prioritizes_mcp_overrides() -> None:
    """MCP definitions with matching names should override built-ins."""
    builtin = copy.deepcopy(get_builtin_tools()[0])
    builtin_name = builtin["function"]["name"]

    overridden_tool = copy.deepcopy(builtin)
    overridden_tool["function"]["description"] = "MCP version"

    new_tool = {
        "type": "function",
        "function": {
            "name": "mcp__custom__tool",
            "description": "New MCP tool",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }

    class DummyManager:
        def get_all_tools_openai(self) -> list[dict[str, dict[str, str]]]:
            return [overridden_tool, new_tool]

    tools = get_all_tools(DummyManager())

    override = next(tool for tool in tools if tool["function"]["name"] == builtin_name)
    assert override["function"]["description"] == "MCP version"

    assert any(tool["function"]["name"] == "mcp__custom__tool" for tool in tools)
