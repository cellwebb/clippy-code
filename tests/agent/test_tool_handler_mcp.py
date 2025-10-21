"""Tests for MCP result formatting in tool_handler."""

from mcp import types

from clippy.agent.tool_handler import add_tool_result, format_mcp_result


class TestFormatMCPResult:
    """Test format_mcp_result function."""

    def test_formats_simple_text_result(self):
        """Test formatting a simple text result."""
        result = types.CallToolResult(
            content=[types.TextContent(type="text", text="Simple text content")]
        )

        formatted = format_mcp_result(result)
        assert formatted == "Simple text content"

    def test_formats_multiple_text_blocks(self):
        """Test formatting multiple text blocks."""
        result = types.CallToolResult(
            content=[
                types.TextContent(type="text", text="First block"),
                types.TextContent(type="text", text="Second block"),
            ]
        )

        formatted = format_mcp_result(result)
        assert formatted == "First block\nSecond block"

    def test_handles_image_content(self):
        """Test handling image content."""
        result = types.CallToolResult(
            content=[
                types.TextContent(type="text", text="Before image"),
                types.ImageContent(type="image", mimeType="image/png", data="base64data"),
                types.TextContent(type="text", text="After image"),
            ]
        )

        formatted = format_mcp_result(result)
        assert "Before image" in formatted
        assert "[Image: image/png]" in formatted
        assert "After image" in formatted

    def test_handles_non_mcp_result(self):
        """Test handling non-MCP result."""
        result = "Plain string result"
        formatted = format_mcp_result(result)
        assert formatted == "Plain string result"

    def test_handles_embedded_resource(self):
        """Embedded resources should include resource text."""
        resource = types.TextResourceContents(uri="https://example.com", text="embedded")
        result = types.CallToolResult(
            content=[types.EmbeddedResource(type="resource", resource=resource)]
        )

        formatted = format_mcp_result(result)
        assert "embedded" in formatted

    def test_avoids_ugly_representation(self):
        """Test that we don't get the ugly CallToolResult repr."""
        result = types.CallToolResult(
            content=[types.TextContent(type="text", text="Clean content")]
        )

        formatted = format_mcp_result(result)

        # Should NOT contain these ugly parts from the repr
        assert "meta=None" not in formatted
        assert "annotations=None" not in formatted
        assert "structuredContent=None" not in formatted
        assert "isError=False" not in formatted

        # Should only contain the actual content
        assert formatted == "Clean content"


class TestAddToolResultWithMCP:
    """Test add_tool_result with MCP results."""

    def test_formats_mcp_result_properly(self):
        """Test that MCP results are formatted cleanly in conversation history."""
        conversation_history = []

        mcp_result = types.CallToolResult(
            content=[types.TextContent(type="text", text="Actual MCP tool output")]
        )

        add_tool_result(
            conversation_history,
            tool_use_id="tool_123",
            success=True,
            message="Successfully executed MCP tool",
            result=mcp_result,
        )

        assert len(conversation_history) == 1
        tool_message = conversation_history[0]

        assert tool_message["role"] == "tool"
        assert tool_message["tool_call_id"] == "tool_123"

        content = tool_message["content"]
        assert "Successfully executed MCP tool" in content
        assert "Actual MCP tool output" in content

        # Should NOT contain ugly repr parts
        assert "meta=None" not in content
        assert "annotations=None" not in content
        assert "CallToolResult" not in content

    def test_handles_regular_non_mcp_result(self):
        """Test that non-MCP results still work normally."""
        conversation_history = []

        add_tool_result(
            conversation_history,
            tool_use_id="tool_456",
            success=True,
            message="Regular tool result",
            result="Some regular data",
        )

        assert len(conversation_history) == 1
        tool_message = conversation_history[0]

        content = tool_message["content"]
        assert "Regular tool result" in content
        assert "Some regular data" in content

    def test_handles_empty_result(self):
        """Test that empty results are handled correctly."""
        conversation_history = []

        add_tool_result(
            conversation_history,
            tool_use_id="tool_789",
            success=True,
            message="No result data",
            result=None,
        )

        assert len(conversation_history) == 1
        tool_message = conversation_history[0]

        content = tool_message["content"]
        assert content == "No result data"

    def test_error_prefix_added_on_failure(self):
        """Test that ERROR prefix is added on failure."""
        conversation_history = []

        mcp_result = types.CallToolResult(
            content=[types.TextContent(type="text", text="Error details")]
        )

        add_tool_result(
            conversation_history,
            tool_use_id="tool_error",
            success=False,
            message="MCP tool failed",
            result=mcp_result,
        )

        assert len(conversation_history) == 1
        tool_message = conversation_history[0]

        content = tool_message["content"]
        assert content.startswith("ERROR: ")
        assert "MCP tool failed" in content
        assert "Error details" in content
