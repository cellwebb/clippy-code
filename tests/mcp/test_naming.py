"""Tests for MCP naming utilities."""

from clippy.mcp.naming import format_mcp_tool_name, is_mcp_tool, parse_mcp_qualified_name


def test_is_mcp_tool() -> None:
    """Test MCP tool detection."""
    assert is_mcp_tool("mcp__server__tool") is True
    assert is_mcp_tool("mcp__another__tool") is True
    assert is_mcp_tool("read_file") is False
    assert is_mcp_tool("write_file") is False
    assert is_mcp_tool("") is False
    assert is_mcp_tool("mcp") is False
    assert is_mcp_tool("mcp__") is False


def test_parse_mcp_qualified_name() -> None:
    """Test parsing MCP qualified names."""
    server_id, tool_name = parse_mcp_qualified_name("mcp__server__tool")
    assert server_id == "server"
    assert tool_name == "tool"

    server_id, tool_name = parse_mcp_qualified_name("mcp__another_server__another_tool")
    assert server_id == "another_server"
    assert tool_name == "another_tool"


def test_parse_mcp_qualified_name_invalid() -> None:
    """Test that invalid MCP names raise ValueError."""
    try:
        parse_mcp_qualified_name("read_file")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected

    try:
        parse_mcp_qualified_name("mcp__server")  # Missing tool part
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected

    try:
        parse_mcp_qualified_name("mcp__")  # Missing server and tool parts
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_format_mcp_tool_name() -> None:
    """Test formatting MCP tool names."""
    name = format_mcp_tool_name("server", "tool")
    assert name == "mcp__server__tool"

    name = format_mcp_tool_name("another_server", "another_tool")
    assert name == "mcp__another_server__another_tool"
