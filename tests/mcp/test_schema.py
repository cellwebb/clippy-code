"""Tests for MCP schema mapping."""

from clippy.mcp.schema import _convert_input_schema, map_mcp_to_openai


def test_map_mcp_to_openai() -> None:
    """Test mapping MCP tool to OpenAI format."""
    # Create a mock MCP tool
    mcp_tool = type(
        "Tool",
        (),
        {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "A string parameter"},
                    "param2": {"type": "integer", "description": "An integer parameter"},
                },
                "required": ["param1"],
            },
        },
    )()

    result = map_mcp_to_openai(mcp_tool, "test-server")

    assert result["type"] == "function"
    assert result["function"]["name"] == "mcp__test-server__test_tool"
    assert result["function"]["description"] == "[MCP test-server] A test tool"
    assert "parameters" in result["function"]
    assert result["function"]["parameters"]["type"] == "object"


def test_convert_input_schema_with_none() -> None:
    """Test converting input schema when None."""
    result = _convert_input_schema(None)
    assert result == {}


def test_convert_input_schema_with_schema() -> None:
    """Test converting input schema with actual schema."""
    schema = {"type": "object", "properties": {"param1": {"type": "string"}}}

    result = _convert_input_schema(schema)
    assert result == schema
    # Verify it's a copy, not the same object
    assert result is not schema
