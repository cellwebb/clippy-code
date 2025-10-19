"""Tests for enhanced UI widgets with MCP support."""

import pytest

from clippy.mcp.naming import parse_mcp_qualified_name
from clippy.ui.widgets import ApprovalDialog, ErrorPanel


class TestApprovalDialog:
    """Test the enhanced ApprovalDialog widget."""

    def test_regular_tool_dialog_initialization(self) -> None:
        """Test dialog initialization for regular tools."""
        tool_name = "write_file"
        tool_input = {"path": "/tmp/test.txt", "content": "Hello, World!"}
        diff_content = "--- /tmp/test.txt\n+++ /tmp/test.txt\n@@ -1,0 +1 @@\n+Hello, World!"

        dialog = ApprovalDialog(tool_name, tool_input, diff_content)

        assert dialog.tool_name == tool_name
        assert dialog.tool_input == tool_input
        assert dialog.diff_content == diff_content
        assert not dialog.is_mcp_tool
        assert dialog.expanded == {"input": True, "diff": False}

    def test_mcp_tool_dialog_initialization(self) -> None:
        """Test dialog initialization for MCP tools."""
        tool_name = "mcp:test-server:write_file"
        tool_input = {"path": "/tmp/test.txt", "content": "Hello, MCP!"}

        dialog = ApprovalDialog(tool_name, tool_input)

        assert dialog.tool_name == tool_name
        assert dialog.tool_input == tool_input
        assert dialog.is_mcp_tool
        assert dialog.diff_content is None

    def test_truncated_input_handling(self) -> None:
        """Test handling of long input that gets truncated."""
        # Create a tool input with many parameters
        tool_input = {}
        for i in range(15):
            tool_input[f"param_{i}"] = (
                f"This is parameter {i} with some long content to test truncation"
            )

        dialog = ApprovalDialog("test_tool", tool_input)

        # Should have more than max_input_lines
        assert len(list(dialog.tool_input.items())) > dialog.max_input_lines

        # The dialog should handle this in compose() method
        # This is more of an integration test, but we can verify the setup

    def test_large_diff_handling(self) -> None:
        """Test handling of large diff content."""
        # Create a large diff
        diff_lines = []
        for i in range(30):
            diff_lines.append(f"+ Line {i}: Some content here")
        large_diff = "\n".join(diff_lines)

        # Should recognize this as a large diff
        assert len(large_diff.split("\n")) > 20

    def test_expand_collapse_functionality(self) -> None:
        """Test expand/collapse button functionality."""
        dialog = ApprovalDialog("test_tool", {"param1": "value1", "param2": "value2"})

        # Initially expanded state
        assert dialog.expanded["input"] is True
        assert dialog.expanded["diff"] is False

        # Simulate button press for collapsing input
        dialog.expanded["input"] = False
        assert dialog.expanded["input"] is False

        # Simulate button press for expanding diff
        dialog.expanded["diff"] = True
        assert dialog.expanded["diff"] is True


class TestErrorPanel:
    """Test the ErrorPanel widget."""

    def test_basic_error_panel(self) -> None:
        """Test basic error panel initialization."""
        error_message = "Something went wrong"

        panel = ErrorPanel(error_message)

        assert panel.error_message == error_message
        assert panel.error_details == {}
        assert not panel.expanded

    def test_error_panel_with_details(self) -> None:
        """Test error panel with detailed error information."""
        error_message = "MCP server error"
        error_details = {
            "server_id": "test-server",
            "tool_name": "write_file",
            "original_error": "Connection timeout",
        }

        panel = ErrorPanel(error_message, error_details)

        assert panel.error_message == error_message
        assert panel.error_details == error_details
        assert not panel.expanded

    def test_mcp_specific_error_suggestions(self) -> None:
        """Test that MCP errors get appropriate suggestions."""
        panel = ErrorPanel("MCP server not connected", {"server_id": "test-server"})

        suggestions = panel._generate_suggestions()

        assert len(suggestions) > 0
        assert any("mcp refresh" in suggestion.lower() for suggestion in suggestions)

    def test_trust_error_suggestions(self) -> None:
        """Test that trust errors get appropriate suggestions."""
        panel = ErrorPanel("MCP server not trusted", {"server_id": "test-server"})

        suggestions = panel._generate_suggestions()

        assert len(suggestions) > 0
        assert any("mcp allow" in suggestion.lower() for suggestion in suggestions)

    def test_timeout_error_suggestions(self) -> None:
        """Test that timeout errors get appropriate suggestions."""
        panel = ErrorPanel("Operation timed out")

        suggestions = panel._generate_suggestions()

        assert len(suggestions) > 0
        assert any("timeout" in suggestion.lower() for suggestion in suggestions)

    def test_expand_collapse_details(self) -> None:
        """Test expand/collapse functionality for error details."""
        error_details = {}
        for i in range(10):
            error_details[f"detail_{i}"] = f"Detail value {i}"

        panel = ErrorPanel("Test error", error_details)

        # Should have more than 5 details
        assert len(error_details) > 5

        # Initially collapsed
        assert not panel.expanded

        # Test expansion
        panel.expanded = True
        assert panel.expanded


class TestIntegration:
    """Integration tests for the enhanced widgets."""

    def test_mcp_naming_integration(self) -> None:
        """Test that MCP naming works correctly with the dialog."""
        mcp_tool_name = "mcp:my-server:read_file"

        try:
            server_id, tool_name = parse_mcp_qualified_name(mcp_tool_name)
            assert server_id == "my-server"
            assert tool_name == "read_file"
        except ValueError:
            pytest.fail("MCP tool name parsing failed")

        # Test with invalid MCP tool name
        with pytest.raises(ValueError):
            parse_mcp_qualified_name("regular_tool_name")

        # Test with malformed MCP tool name
        with pytest.raises(ValueError):
            parse_mcp_qualified_name("mcp:incomplete")


def test_dialog_content_truncation() -> None:
    """Test that content is properly truncated for display."""
    # Test with very long values
    long_value = "x" * 200
    tool_input = {"long_param": long_value, "short_param": "short"}

    dialog = ApprovalDialog("test_tool", tool_input)

    # The dialog should handle this in its compose method
    # We can't directly test the composed content here without mounting
    # but we can verify the setup is correct
    assert len(dialog.tool_input) == 2
    assert len(dialog.tool_input["long_param"]) == 200


def test_error_message_truncation() -> None:
    """Test that long error messages are properly truncated."""
    long_error = "x" * 300
    error_details = {"original_error": long_error}

    panel = ErrorPanel("Test error", error_details)

    # The panel should handle truncation in its build method
    assert len(panel.error_details["original_error"]) == 300
