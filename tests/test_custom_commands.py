"""Tests for custom slash commands."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from clippy.cli.custom_commands import (
    CustomCommand,
    CustomCommandManager,
    handle_custom_command,
    show_session_stats,
)


def test_custom_command_text_type() -> None:
    """Test text-type custom command."""
    config = {
        "type": "text",
        "description": "Test command",
        "text": "Hello {user} at {cwd}!",
        "formatted": True,
    }

    cmd = CustomCommand("test", config)
    assert cmd.name == "test"
    assert cmd.command_type == "text"
    assert cmd.description == "Test command"

    # Mock agent and console
    agent = Mock()
    console = Mock()

    with patch.dict(os.environ, {"USER": "testuser"}, clear=True):
        with patch("os.getcwd", return_value="/test/dir"):
            result = cmd.execute("", agent, console)

            assert result == "continue"
            console.print.assert_called_once()
            # Check that variables were substituted
            call_args = console.print.call_args[0][0]
            assert "testuser" in call_args
            assert "/test/dir" in call_args


def test_custom_command_shell_type() -> None:
    """Test shell-type custom command."""
    config = {
        "type": "shell",
        "description": "Echo command",
        "command": "echo {args}",
        "dry_run": True,  # Use dry run for testing
    }

    cmd = CustomCommand("echo", config)
    assert cmd.command_type == "shell"

    agent = Mock()
    console = Mock()

    result = cmd.execute("hello world", agent, console)

    assert result == "continue"
    console.print.assert_called_once()
    call_args = console.print.call_args[0][0]
    assert "echo hello world" in call_args


def test_custom_command_template_type() -> None:
    """Test template-type custom command."""
    config = {
        "type": "template",
        "description": "Template command",
        "template": "User: {user}, Args: {args}, Model: {model}",
        "formatted": True,
    }

    cmd = CustomCommand("template", config)

    agent = Mock()
    agent.model = "test-model"
    agent.conversation_history = [{"role": "user"}, {"role": "assistant"}]  # Give it a length
    console = Mock()

    with patch.dict(os.environ, {"USER": "testuser"}, clear=True):
        result = cmd.execute("my args", agent, console)

        assert result == "continue"
        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "testuser" in call_args
        assert "my args" in call_args
        assert "test-model" in call_args


def test_custom_command_function_type() -> None:
    """Test function-type custom command."""
    config = {
        "type": "function",
        "description": "Function command",
        "function": "clippy.cli.custom_commands.show_session_stats",
    }

    cmd = CustomCommand("stats", config)
    assert cmd.command_type == "function"

    agent = Mock()
    agent.conversation_history = [{"role": "user"}, {"role": "assistant"}]
    console = Mock()

    with patch.dict(os.environ, {"USER": "testuser"}, clear=True):
        result = cmd.execute("", agent, console)

        assert result == "continue"
        # show_session_stats should have been called and printed to console


def test_custom_command_manager_initialization() -> None:
    """Test custom command manager creates example config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_commands.json"

        with patch("clippy.cli.custom_commands.get_user_manager") as mock_user_mgr:
            mock_user_dir = Path(tmpdir)
            mock_usermgr_instance = Mock()
            mock_usermgr_instance.config_dir = mock_user_dir
            mock_user_mgr.return_value = mock_usermgr_instance

            CustomCommandManager()

            # Should have created example config
            assert config_path.exists()

            # Load and verify config content
            with open(config_path) as f:
                config_data = json.load(f)

            assert "commands" in config_data
            assert "git" in config_data["commands"]
            assert "whoami" in config_data["commands"]
            assert "todo" in config_data["commands"]
            assert "stats" in config_data["commands"]


def test_custom_command_manager_load_commands() -> None:
    """Test loading commands from config."""
    test_config = {
        "commands": {
            "test1": {
                "type": "text",
                "description": "Test 1",
                "text": "Hello world",
            },
            "test2": {
                "type": "shell",
                "description": "Test 2",
                "command": "echo test",
                "dry_run": True,
            },
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_commands.json"
        with open(config_path, "w") as f:
            json.dump(test_config, f)

        with patch("clippy.cli.custom_commands.get_user_manager") as mock_user_mgr:
            mock_user_dir = Path(tmpdir)
            mock_usermgr_instance = Mock()
            mock_usermgr_instance.config_dir = mock_user_dir
            mock_user_mgr.return_value = mock_usermgr_instance

            manager = CustomCommandManager()

            # Should have loaded commands
            assert len(manager.commands) == 2
            assert "test1" in manager.commands
            assert "test2" in manager.commands

            cmd1 = manager.get_command("test1")
            assert cmd1.command_type == "text"
            assert cmd1.description == "Test 1"


def test_handle_custom_command() -> None:
    """Test custom command handler."""
    test_config = {
        "commands": {
            "hello": {
                "type": "text",
                "text": "Hello world!",
            },
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_commands.json"
        with open(config_path, "w") as f:
            json.dump(test_config, f)

        with patch("clippy.cli.custom_commands.get_user_manager") as mock_user_mgr:
            mock_user_dir = Path(tmpdir)
            mock_usermgr_instance = Mock()
            mock_usermgr_instance.config_dir = mock_user_dir
            mock_user_mgr.return_value = mock_usermgr_instance

            # Clear manager cache
            import clippy.cli.custom_commands

            clippy.cli.custom_commands._custom_manager = None

            agent = Mock()
            console = Mock()

            # Test existing command
            result = handle_custom_command("hello", "", agent, console)
            assert result == "continue"
            console.print.assert_called_with("Hello world!")

            # Test non-existent command
            result = handle_custom_command("nonexistent", "", agent, console)
            assert result is None


def test_show_session_stats_function() -> None:
    """Test the example show_session_stats function."""
    agent = Mock()
    agent.conversation_history = [{"role": "user"}, {"role": "assistant"}, {"role": "user"}]
    console = Mock()

    with patch.dict(os.environ, {"USER": "testuser"}, clear=True):
        result = show_session_stats("", agent, console)
        assert result == "continue"

        # Should have printed stats
        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "3" in call_args  # Message count
        assert "testuser" in call_args


def test_custom_command_dangerous_commands_blocked() -> None:
    """Test that dangerous commands are blocked by default."""
    config = {
        "type": "shell",
        "description": "Dangerous command",
        "command": "rm -rf /",
        "dangerous": False,  # Not explicitly marked as dangerous
    }

    cmd = CustomCommand("dangerous", config)
    agent = Mock()
    console = Mock()

    result = cmd.execute("", agent, console)

    assert result == "continue"
    console.print.assert_called_once()
    call_args = console.print.call_args[0][0]
    assert "Dangerous command detected" in call_args


def test_custom_command_dangerous_commands_allowed() -> None:
    """Test that dangerous commands can be explicitly allowed."""
    config = {
        "type": "shell",
        "description": "Allowed dangerous command",
        "command": "rm -rf test",  # Still dangerous but allowed
        "dangerous": True,  # Explicitly allowed
        "dry_run": True,  # Use dry run for testing
    }

    cmd = CustomCommand("allowed-danger", config)
    agent = Mock()
    console = Mock()

    result = cmd.execute("", agent, console)

    assert result == "continue"
    console.print.assert_called_once()
    call_args = console.print.call_args[0][0]
    assert "rm -rf test" in call_args
