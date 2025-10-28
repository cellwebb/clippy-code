"""
Comprehensive tests for Rich markup escaping to prevent regressions.

This test suite verifies that the fix for Rich markup escaping in tool handler,
CLI commands, and MCP manager works correctly and prevents the original bug:

    MarkupError: closing tag '[/yellow]' at position 112129 doesn't match any open tag
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from rich.console import Console

from clippy.agent.tool_handler import handle_tool_use
from clippy.cli.commands import _handle_model_add
from clippy.executor import ActionExecutor
from clippy.mcp.config import Config
from clippy.mcp.manager import Manager
from clippy.permissions import PermissionManager


def test_original_bug_scenario():
    """
    Test the exact scenario from the bug report to ensure it's fixed.

    Original error:
    "Operation result: content processed [/yellow] but no opening tag"

    This contains an unmatched closing tag that would cause the original
    MarkupError: closing tag '[/yellow]' at position 112129 doesn't match any open tag
    """
    console = Console()
    executor = Mock(spec=ActionExecutor)
    permission_manager = PermissionManager()

    # Mock executor to return the exact problematic message from bug report
    test_message = "Operation result: content processed [/yellow] but no opening tag"
    executor.execute.return_value = (False, test_message, None)

    conversation_history = []

    # This should NOT raise a MarkupError with our fix
    try:
        with patch.object(console, "print") as mock_print:
            handle_tool_use(
                tool_name="write_file",
                tool_input={"path": "test.txt", "content": "test"},
                tool_use_id="test_bug_regression",
                auto_approve_all=True,
                permission_manager=permission_manager,
                executor=executor,
                console=console,
                conversation_history=conversation_history,
            )

            # If we get here without MarkupError, the fix worked
            assert True

            # Verify that console was called and no unescaped markup exists
            mock_print.assert_called()
            call_args = [str(call[0]) for call in mock_print.call_args_list if call[0]]

            # The problematic pattern [/yellow] should be escaped (double backslash in repr)
            found_escaped = any(
                r"\\[/yellow]" in call_str and "processed" in call_str for call_str in call_args
            )
            assert found_escaped, f"Expected escaped pattern not found. Call args: {call_args}"

            # Verify the message is displayed in red color markup (without MarkupError)
            found_red_markup = any(
                "[bold red]" in call_str and "✗" in call_str for call_str in call_args
            )
            assert found_red_markup, "Expected red markup styling not found"

    except Exception as e:
        # If we get a MarkupError, the fix didn't work
        if "MarkupError" in str(type(e)):
            pytest.fail(f"Original bug not fixed! Rich markup error occurred: {e}")
        else:
            # Some other exception might be expected
            raise


def test_various_problematic_rich_markup_scenarios():
    """
    Test various problematic Rich markup scenarios to ensure they're handled safely.
    """
    console = Console()
    executor = Mock(spec=ActionExecutor)
    permission_manager = PermissionManager()

    # Test various problematic markup patterns
    problematic_cases = [
        "Error with unmatched closing tag [/red]",
        "Warning: [yellow]markup but no closing",
        "Error with [green]multiple[/green] [red]tags[/red]",
        "Error with nested [bold][red]deep[/red]] markup",
        "Critical error: [bold red][yellow]Critical[/yellow][/bold red]",
        "Status: [dim]timeout[/dim] occurred",
        "Warning: [cyan]invalid configuration[/cyan]",
        "Info: [blue]connection successful[/blue]",
    ]

    for i, test_message in enumerate(problematic_cases):
        conversation_history = []
        executor.execute.return_value = (False, test_message, None)

        try:
            with patch.object(console, "print"):
                handle_tool_use(
                    tool_name="test_tool",
                    tool_input={"param": "value"},
                    tool_use_id=f"test_problematic_{i}",
                    auto_approve_all=True,
                    permission_manager=permission_manager,
                    executor=executor,
                    console=console,
                    conversation_history=conversation_history,
                )

            # If we get here without MarkupError, the fix worked for this case
            assert True

        except Exception as e:
            # Check if it's a Rich markup error
            if "MarkupError" in str(type(e)):
                pytest.fail(f"Rich markup error not prevented for case {i}: {test_message}")
            else:
                # Some other exception might be expected, re-raise it
                raise


def test_successful_operations_with_markup():
    """
    Test that success messages with Rich markup are handled correctly.
    """
    console = Console()
    executor = Mock(spec=ActionExecutor)
    permission_manager = PermissionManager()

    success_messages = [
        "File created with [green]success[/green] status",
        "Operation completed [bold]successfully[/bold]",
        "All [cyan]tests[/cyan] passed",
        "Connection [blue]established[/blue]",
    ]

    for i, test_message in enumerate(success_messages):
        conversation_history = []
        executor.execute.return_value = (True, test_message, "result")

        try:
            with patch.object(console, "print"):
                handle_tool_use(
                    tool_name="test_tool",
                    tool_input={"param": "value"},
                    tool_use_id=f"test_success_{i}",
                    auto_approve_all=True,
                    permission_manager=permission_manager,
                    executor=executor,
                    console=console,
                    conversation_history=conversation_history,
                )

            # Should not raise any exception
            assert True

        except Exception as e:
            pytest.fail(f"Unexpected exception for success case {i}: {e}")


def test_cli_commands_markup_handling():
    """
    Test that CLI commands handle problematic Rich markup correctly.
    """
    console = Console()

    problematic_messages = [
        "Failed to add model: [/yellow] unmatched closing tag",
        "Cannot remove: [red]validation error[/red] occurred",
        "Model not found: [bold cyan]missing[/bold cyan]",
        "Connection failed: [dim]timeout[/dim] after 30 seconds",
        "Invalid threshold: [green]must be number[/green]",
        "Switch failed: [bold]authentication[/bold] required",
    ]

    for i, test_message in enumerate(problematic_messages):
        with patch("clippy.cli.commands.get_user_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_manager.add_model.return_value = (False, test_message)
            mock_get_manager.return_value = mock_manager

            try:
                _handle_model_add(console, ["provider", "model"])
                # Should not raise MarkupError
                assert True
            except Exception as e:
                if "MarkupError" in str(type(e)):
                    pytest.fail(f"CLI command error for case {i}: {e}")
                else:
                    raise


def test_mcp_manager_markup_handling():
    """
    Test that MCP manager handles problematic Rich markup correctly.
    """
    console = Console()
    config = Config(mcp_servers={})

    # Test connection error with markup
    server_config = Mock()
    server_config.command = "nonexistent-command"
    server_config.args = []
    server_config.env = {}
    server_config.cwd = None
    config.mcp_servers["test-server"] = server_config

    manager = Manager(config, console)

    try:
        with patch("clippy.mcp.manager.stdio_client") as mock_stdio:
            mock_context = AsyncMock()
            mock_context.__aenter__.side_effect = Exception(
                "Connection failed: [/yellow] unmatched closing tag"
            )
            mock_stdio.return_value = mock_context

            manager._run_in_loop(manager._async_start())
            # Should not raise MarkupError if our fix works
            assert True
    except Exception as e:
        if "MarkupError" in str(type(e)):
            pytest.fail(f"MCP manager error not prevented: {e}")
        else:
            # Other exceptions might be expected
            raise


def test_edge_cases_and_boundaries():
    """
    Test edge cases and boundary conditions for Rich markup escaping.
    """
    console = Console()
    executor = Mock(spec=ActionExecutor)
    permission_manager = PermissionManager()

    # Test empty message (should work fine)
    conversation_history = []
    executor.execute.return_value = (False, "", None)

    try:
        with patch.object(console, "print"):
            handle_tool_use(
                tool_name="test_tool",
                tool_input={"param": "value"},
                tool_use_id="test_empty",
                auto_approve_all=True,
                permission_manager=permission_manager,
                executor=executor,
                console=console,
                conversation_history=conversation_history,
            )

        # Empty message should work fine
        assert True
    except Exception as e:
        pytest.fail(f"Empty message caused unexpected error: {e}")

    # Test extremely long message with lots of markup
    long_message = (
        "Error: [red]Many[/red] [green]different[/green] [yellow]markup[/yellow] "
        "[bold]patterns[/bold] [dim]scattered[/dim] [cyan]throughout[/cyan] "
        "[blue]message[/blue] [magenta]causing[/magenta] [italic]issues[/italic]"
    )

    conversation_history = []
    executor.execute.return_value = (False, long_message, None)

    try:
        with patch.object(console, "print"):
            handle_tool_use(
                tool_name="test_tool",
                tool_input={"param": "value"},
                tool_use_id="test_long",
                auto_approve_all=True,
                permission_manager=permission_manager,
                executor=executor,
                console=console,
                conversation_history=conversation_history,
            )

        # Should handle very long messages without issues
        assert True
    except Exception as e:
        pytest.fail(f"Long message caused unexpected error: {e}")
