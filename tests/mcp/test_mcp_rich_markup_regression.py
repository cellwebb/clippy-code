"""Regression tests for Rich markup escaping in MCP manager."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from rich.console import Console

from clippy.mcp.config import Config
from clippy.mcp.manager import Manager


def test_mcp_manager_handles_problematic_markup():
    """
    Test that MCP manager handles problematic Rich markup without crashing.

    This is a regression test for the error:
    MarkupError: closing tag '[/yellow]' at position 112129 doesn't match any open tag
    """
    console = Console()
    config = Config(mcp_servers={})

    # Mock server config that will fail
    server_config = Mock()
    server_config.command = "nonexistent-command"
    server_config.args = []
    server_config.env = {}
    server_config.cwd = None

    config.mcp_servers["test-server"] = server_config

    manager = Manager(config, console)

    # Mock exception with problematic Rich markup
    problematic_exception = Exception("Connection failed: [/yellow] unmatched closing tag")

    with patch("clippy.mcp.manager.stdio_client") as mock_stdio:
        mock_context = AsyncMock()
        mock_context.__aenter__.side_effect = problematic_exception
        mock_stdio.return_value = mock_context

        try:
            # This should not raise a MarkupError
            manager._run_in_loop(manager._async_start())
            # If we get here without MarkupError, the fix worked
            assert True
        except Exception as e:
            # Check if it's a Rich markup error
            if "MarkupError" in str(type(e)) or "closing tag" in str(e):
                pytest.fail(f"Rich markup error was not prevented: {e}")
            else:
                # Other exceptions might be expected
                pass


def test_mcp_manager_tool_mapping_error_with_markup():
    """Test MCP tool mapping error with problematic markup."""
    console = Console()
    config = Config(mcp_servers={})
    manager = Manager(config, console)

    # Mock a tool with problematic description
    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.description = "Tool that [yellow]highlights[/yellow] important data"

    # Mock exception with markup
    problematic_exception = Exception("Mapping failed: [bold red]invalid schema[/bold red]")

    with patch.object(manager, "_tools", {"test-server": [mock_tool]}):
        with patch("clippy.mcp.manager.map_mcp_to_openai", side_effect=problematic_exception):
            try:
                # This should not raise a MarkupError
                manager.get_all_tools_openai()
                # If we get here without MarkupError, the fix worked
                assert True
            except Exception as e:
                # Check if it's a Rich markup error
                if "MarkupError" in str(type(e)) or "closing tag" in str(e):
                    pytest.fail(f"Rich markup error was not prevented in tool mapping: {e}")
                else:
                    # Other exceptions might be expected
                    pass


def test_mcp_manager_various_problematic_patterns():
    """Test various problematic markup patterns in MCP manager."""
    console = Console()
    config = Config(mcp_servers={})
    manager = Manager(config, console)

    # Test various markup patterns that could cause issues
    problematic_exceptions = [
        Exception("Error with unmatched closing tag [/red]"),
        Exception("Error with [yellow]markup but no closing"),
        Exception("Error with [green]multiple[/green] [red]tags[/red]"),
        Exception("Error with nested [bold [red]deep[/red]] markup"),
        Exception("Connection: [dim]timeout[/dim] occurred"),
        Exception("Warning: [cyan]invalid configuration[/cyan]"),
    ]

    for i, test_exception in enumerate(problematic_exceptions):
        server_config = Mock()
        server_config.command = "test-command"
        server_config.args = []
        server_config.env = {}
        server_config.cwd = None

        config.mcp_servers[f"server-{i}"] = server_config

        manager = Manager(config, console)

        with patch("clippy.mcp.manager.stdio_client") as mock_stdio:
            mock_context = AsyncMock()
            mock_context.__aenter__.side_effect = test_exception
            mock_stdio.return_value = mock_context

            try:
                manager._run_in_loop(manager._async_start())
                # If we get here without MarkupError, the fix worked for this case
                assert True
            except Exception as e:
                # Check if it's a Rich markup error
                if "MarkupError" in str(type(e)) or "closing tag" in str(e):
                    pytest.fail(f"Rich markup error was not prevented for exception {i}: {e}")
                else:
                    # Other exceptions might be expected
                    pass
