"""Tests for executor safety checker integration."""

from unittest.mock import Mock, patch

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


class TestExecutorSafetyIntegration:
    """Test cases for executor integration with safety checker."""

    def test_executor_without_safety_checker(self):
        """Test that executor works without safety checker (backward compatibility)."""
        permission_manager = PermissionManager(PermissionConfig())
        executor = ActionExecutor(permission_manager)

        # Should not crash and execute normally
        success, message, data = executor.execute("execute_command", {"command": "echo hello"})

        # Command should execute (even if it fails, safety checker shouldn't block)
        assert "Command failed" in message or "Command executed" in message

    @patch("clippy.executor.execute_command")
    def test_safety_checker_blocks_dangerous_command(self, mock_execute):
        """Test that safety checker blocks dangerous commands."""
        mock_execute.return_value = (True, "Command executed", "output")

        permission_manager = PermissionManager(PermissionConfig())
        mock_provider = Mock()
        mock_provider.create_message.return_value = {"content": "BLOCK: Too dangerous"}

        executor = ActionExecutor(
            permission_manager, llm_provider=mock_provider, model="test-model"
        )

        success, message, data = executor.execute(
            "execute_command", {"command": "rm -rf /", "working_dir": "/"}
        )

        assert success is False
        assert "blocked by safety agent" in message
        assert "Too dangerous" in message
        # The actual execute_command should not be called
        mock_execute.assert_not_called()

    @patch("clippy.executor.execute_command")
    def test_safety_checker_allows_safe_command(self, mock_execute):
        """Test that safety checker allows safe commands."""
        mock_execute.return_value = (True, "Command executed successfully", "hello")

        permission_manager = PermissionManager(PermissionConfig())
        mock_provider = Mock()
        mock_provider.create_message.return_value = {"content": "ALLOW: Simple echo command"}

        executor = ActionExecutor(
            permission_manager, llm_provider=mock_provider, model="test-model"
        )

        success, message, data = executor.execute(
            "execute_command", {"command": "echo hello", "working_dir": "."}
        )

        assert success is True
        assert "executed successfully" in message
        # The actual execute_command should be called
        mock_execute.assert_called_once()

    @patch("clippy.executor.execute_command")
    def test_safety_checker_failure_blocks_command(self, mock_execute):
        """Test that safety checker failures block commands."""
        mock_execute.return_value = (True, "Command executed", "output")

        permission_manager = PermissionManager(PermissionConfig())
        mock_provider = Mock()
        mock_provider.create_message.side_effect = Exception("LLM down")

        executor = ActionExecutor(
            permission_manager, llm_provider=mock_provider, model="test-model"
        )

        success, message, data = executor.execute("execute_command", {"command": "echo hello"})

        assert success is False
        assert "Safety check failed" in message
        # The actual execute_command should not be called
        mock_execute.assert_not_called()

    @patch("clippy.executor.execute_command")
    def test_set_llm_provider_updates_safety_checker(self, mock_execute):
        """Test that set_llm_provider updates the safety checker."""
        mock_execute.return_value = (True, "Command executed", "output")

        permission_manager = PermissionManager(PermissionConfig())

        # Create executor without safety checker
        executor = ActionExecutor(permission_manager)

        # Command should execute without safety check
        success, message, data = executor.execute("execute_command", {"command": "rm -rf /"})

        # Execute should be called (no safety check)
        mock_execute.assert_called_once()
        mock_execute.reset_mock()

        # Now add safety checker
        mock_provider = Mock()
        mock_provider.create_message.return_value = {"content": "BLOCK: Dangerous"}
        executor.set_llm_provider(mock_provider, "test-model")

        # Command should now be blocked
        success, message, data = executor.execute("execute_command", {"command": "rm -rf /"})

        assert success is False
        assert "blocked by safety agent" in message
        # Execute should not be called anymore
        mock_execute.assert_not_called()

    @patch("clippy.executor.execute_command")
    def test_safety_checker_respects_working_directory(self, mock_execute):
        """Test that safety checker gets the working directory."""
        mock_execute.return_value = (True, "Command executed", "output")

        permission_manager = PermissionManager(PermissionConfig())
        mock_provider = Mock()
        mock_provider.create_message.return_value = {"content": "ALLOW: Safe"}

        executor = ActionExecutor(
            permission_manager, llm_provider=mock_provider, model="test-model"
        )

        success, message, data = executor.execute(
            "execute_command", {"command": "ls", "working_dir": "/etc"}
        )

        # Check that the safety checker was called with the working directory
        call_args = mock_provider.create_message.call_args[0][0]
        user_message = None
        for msg in call_args:
            if msg["role"] == "user":
                user_message = msg["content"]
                break

        assert user_message is not None
        assert "Working directory: /etc" in user_message
        assert "Command to evaluate: ls" in user_message
