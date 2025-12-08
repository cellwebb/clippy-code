"""Tests for init command handler."""

from unittest.mock import Mock

import pytest
from rich.console import Console

from clippy.agent import ClippyAgent
from clippy.cli.commands.init import handle_init_command


class TestInitCommand:
    """Test the init command handler."""

    def test_handle_init_command_with_args(self):
        """Test handling init command with arguments."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_console = Mock(spec=Console)

        command_args = "Hello, I need help with coding"
        result = handle_init_command(mock_agent, mock_console, command_args)

        assert result == "continue"
        mock_agent.append_user_message.assert_called_once_with(command_args)

        # Check console prints
        mock_console.print.assert_any_call("[green]✓ Conversation initialized with:[/green]")
        mock_console.print.assert_any_call(f"  [dim]{command_args}[/dim]")

    def test_handle_init_command_empty_args(self):
        """Test handling init command with empty arguments."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_console = Mock(spec=Console)

        command_args = ""
        result = handle_init_command(mock_agent, mock_console, command_args)

        assert result == "continue"
        mock_agent.append_user_message.assert_not_called()
        mock_console.print.assert_called_once_with("[red]Usage: /init <init_message>[/red]")

    def test_handle_init_command_whitespace_only(self):
        """Test handling init command with whitespace-only arguments."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_console = Mock(spec=Console)

        command_args = "   "
        result = handle_init_command(mock_agent, mock_console, command_args)

        assert result == "continue"
        mock_agent.append_user_message.assert_called_once_with("")  # After strip

        # Check console prints
        mock_console.print.assert_any_call("[green]✓ Conversation initialized with:[/green]")
        mock_console.print.assert_any_call("  [dim][/dim]")

    def test_handle_init_command_with_special_chars(self):
        """Test handling init command with special characters."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_console = Mock(spec=Console)

        command_args = "Help me with Python 🐍 & JavaScript!"
        result = handle_init_command(mock_agent, mock_console, command_args)

        assert result == "continue"
        mock_agent.append_user_message.assert_called_once_with(command_args)

        # Check console prints
        mock_console.print.assert_any_call("[green]✓ Conversation initialized with:[/green]")
        mock_console.print.assert_any_call(f"  [dim]{command_args}[/dim]")

    def test_handle_init_command_long_message(self):
        """Test handling init command with long message."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_console = Mock(spec=Console)

        command_args = (
            "This is a very long initialization message that might contain "
            + "multiple sentences and could potentially be used to set up a complex "
            + "conversation context with the AI assistant."
        )
        result = handle_init_command(mock_agent, mock_console, command_args)

        assert result == "continue"
        mock_agent.append_user_message.assert_called_once_with(command_args)

        # Check console prints
        mock_console.print.assert_any_call("[green]✓ Conversation initialized with:[/green]")
        mock_console.print.assert_any_call(f"  [dim]{command_args}[/dim]")

    def test_handle_init_command_agent_exception(self):
        """Test handling init command when agent raises exception."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_agent.append_user_message.side_effect = Exception("Agent error")
        mock_console = Mock(spec=Console)

        command_args = "Test message"

        with pytest.raises(Exception, match="Agent error"):
            handle_init_command(mock_agent, mock_console, command_args)

    def test_handle_init_command_console_exception(self):
        """Test handling init command when console raises exception."""
        mock_agent = Mock(spec=ClippyAgent)
        mock_console = Mock(spec=Console)
        mock_console.print.side_effect = Exception("Console error")

        command_args = "Test message"

        with pytest.raises(Exception, match="Console error"):
            handle_init_command(mock_agent, mock_console, command_args)
