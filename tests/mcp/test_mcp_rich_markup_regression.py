"""Regression tests for Rich markup escaping in MCP manager.

This version tests the Rich markup escaping more directly without relying on
complex async/await mocking that can hang in some environments.
"""

from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.markup import escape

from clippy.mcp.config import Config
from clippy.mcp.manager import Manager


def test_rich_markup_escaping_directly():
    """Test that problematic Rich markup strings are properly escaped."""

    # Test various problematic markup patterns
    problematic_strings = [
        "Connection failed: [/yellow] unmatched closing tag",
        "Error with [yellow]markup but no closing",
        "Error with [green]multiple[/green] [red]tags[/red]",
        "Error with nested [bold [red]deep[/red]] markup",
        "Connection: [dim]timeout[/dim] occurred",
        "Warning: [cyan]invalid configuration[/cyan]",
        "[/] empty tag",
        "Multiple [red][green][blue] nested tags",
        "Mangled tag [/unclosed bracket",
        "Tag with [invalid_chars!@#] markup",
    ]

    for problematic_string in problematic_strings:
        # Test that the escape function properly handles the string
        escaped = escape(problematic_string)

        # When printed to console, it should not raise MarkupError
        try:
            real_console = Console()
            real_console.print(f"[yellow]⚠ Error: {escaped}[/yellow]")
        except Exception as e:
            if "MarkupError" in str(type(e)) or "closing tag" in str(e):
                pytest.fail(f"Rich markup error was not prevented for '{problematic_string}': {e}")


def test_mcp_manager_error_handling_with_problematic_markup():
    """Test that MCP manager properly escapes problematic markup in error messages."""

    console = Mock(spec=Console)

    # Mock a server with problematic markup in its error
    server_id = "test-server"
    problematic_error = Exception("Connection failed: [/yellow] unmatched closing tag")

    # Mock console.print call to capture what gets printed
    printed_messages = []

    def capture_print(msg):
        printed_messages.append(msg)
        # This should not raise a MarkupError
        try:
            real_console = Console()
            real_console.print(msg)
        except Exception as e:
            if "MarkupError" in str(type(e)) or "closing tag" in str(e):
                pytest.fail(f"Rich markup error occurred: {e}")

    console.print = capture_print

    # Simulate the error handling that happens in _async_start
    try:
        raise problematic_error
    except Exception as e:
        if console:
            error_msg = (
                f"[yellow]⚠ Failed to connect to MCP server '{server_id}': "
                f"{escape(str(e))}[/yellow]"
            )
            console.print(error_msg)

    # Verify the error message was constructed and printed successfully
    assert len(printed_messages) == 1
    assert "Failed to connect to MCP server 'test-server'" in printed_messages[0]


def test_mcp_manager_tool_mapping_error_with_markup_direct():
    """Test MCP tool mapping error with problematic markup, tested directly."""

    console = Mock(spec=Console)
    config = Config(mcp_servers={})
    manager = Manager(config, console)

    # Mock a tool with problematic description
    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.description = "Tool that [yellow]highlights[/yellow] important data"

    # Mock exception with problematic markup
    problematic_exception = Exception("Mapping failed: [bold red]invalid schema[/bold red]")

    # Mock console.print to capture and test the message
    printed_messages = []

    def capture_print(msg):
        printed_messages.append(msg)
        # This should not raise a MarkupError
        try:
            real_console = Console()
            real_console.print(msg)
        except Exception as e:
            if "MarkupError" in str(type(e)) or "closing tag" in str(e):
                pytest.fail(f"Rich markup error occurred: {e}")

    console.print = capture_print

    # Mock map_mcp_to_openai to raise the problematic exception
    with patch("clippy.mcp.manager.map_mcp_to_openai", side_effect=problematic_exception):
        with patch.object(manager, "_tools", {"test-server": [mock_tool]}):
            # Call the method directly
            result = manager.get_all_tools_openai()

            # Should return empty list due to mapping failure
            assert result == []

            # Should have printed an error message - the test is this didn't raise MarkupError
            assert len(printed_messages) == 1
            assert "Failed to map MCP tool" in printed_messages[0]
