"""Integration tests for custom commands."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from rich.console import Console

from clippy.cli.commands import handle_command


def test_custom_command_integration() -> None:
    """Test that custom commands integrate properly with main command handler."""

    # Create a test custom commands file
    test_config = {
        "commands": {
            "echo": {
                "type": "text",
                "description": "Echo your message",
                "text": "You said: {args}",
                "formatted": False,
            },
            "count": {
                "type": "template",
                "description": "Count messages and show model",
                "template": "Model: {model}, Messages: {message_count}",
                "formatted": True,
            },
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_commands.json"
        with open(config_path, "w") as f:
            json.dump(test_config, f)

        # Mock the user manager to use our test directory
        with patch("clippy.cli.custom_commands.get_user_manager") as mock_user_mgr:
            mock_usermgr_instance = Mock()
            mock_usermgr_instance.config_dir = Path(tmpdir)
            mock_user_mgr.return_value = mock_usermgr_instance

            # Clear the custom manager cache
            import clippy.cli.custom_commands

            clippy.cli.custom_commands._custom_manager = None

            # Create mock agent and console
            agent = Mock()
            agent.model = "test-gpt"
            agent.conversation_history = [{"role": "user"}, {"role": "assistant"}]
            console = Console()
            console.print = Mock()

            # Test 1: Handle custom command through main dispatcher
            result = handle_command("/echo hello world", agent, console)

            assert result == "continue"
            console.print.assert_called_with("You said: hello world")

            # Test 2: Handle template custom command
            console.print.reset_mock()
            result = handle_command("/count", agent, console)

            assert result == "continue"
            call_args = console.print.call_args[0][0]
            assert "test-gpt" in call_args
            assert "2" in call_args  # message count

            # Test 3: Handle custom command management
            console.print.reset_mock()
            result = handle_command("/custom list", agent, console)

            assert result == "continue"
            # Should have printed the custom commands list

            # Test 4: Non-existent command returns None
            result = handle_command("/nonexistent", agent, console)
            assert result is None

            # Test 5: Built-in commands still work
            result = handle_command("/help", agent, console)
            assert result == "continue"


def test_help_command_includes_custom_commands() -> None:
    """Test that the /help command includes custom commands."""

    test_config = {
        "commands": {
            "testcmd": {
                "type": "text",
                "description": "A test custom command",
                "text": "This is a test",
            }
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_commands.json"
        with open(config_path, "w") as f:
            json.dump(test_config, f)

        with patch("clippy.cli.custom_commands.get_user_manager") as mock_user_mgr:
            mock_usermgr_instance = Mock()
            mock_usermgr_instance.config_dir = Path(tmpdir)
            mock_user_mgr.return_value = mock_usermgr_instance

            # Clear the custom manager cache
            import clippy.cli.custom_commands

            clippy.cli.custom_commands._custom_manager = None

            agent = Mock()
            console = Console()
            console.print = Mock()

            # Test that help includes custom commands
            result = handle_command("/help", agent, console)

            assert result == "continue"
            console.print.assert_called_once()

            # Check that custom commands section was included
            help_panel = console.print.call_args[0][0]
            # The Rich Panel doesn't show the content in str(), so extract from renderable
            from rich.panel import Panel

            assert isinstance(help_panel, Panel), f"Expected Panel, got {type(help_panel)}"
            help_content = str(help_panel.renderable)
            assert "testcmd" in help_content


def test_custom_command_management_integration() -> None:
    """Test integration of custom command management."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the user manager
        with patch("clippy.cli.custom_commands.get_user_manager") as mock_user_mgr:
            mock_usermgr_instance = Mock()
            mock_usermgr_instance.config_dir = Path(tmpdir)
            mock_user_mgr.return_value = mock_usermgr_instance

            # Clear the custom manager cache
            import clippy.cli.custom_commands

            clippy.cli.custom_commands._custom_manager = None

            agent = Mock()
            console = Console()
            console.print = Mock()

            # Test custom help command
            result = handle_command("/custom help", agent, console)
            assert result == "continue"

            # Test custom list command (should show empty initially)
            console.print.reset_mock()
            result = handle_command("/custom list", agent, console)
            assert result == "continue"

            # Verify it shows some message (either empty config or example)
            call_args = console.print.call_args[0][0]
            assert call_args is not None
            # The test config should have been loaded and show different content
