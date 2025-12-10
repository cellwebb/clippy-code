"""End-to-end safety integration tests."""

from unittest.mock import Mock, patch

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


class TestSafetyIntegrationE2E:
    """End-to-end tests for safety checker integration."""

    def test_dangerous_command_blocked_integration(self):
        """Integration test that dangerous commands are actually blocked."""
        permission_manager = PermissionManager(PermissionConfig())

        # Mock LLM provider that blocks rm -rf commands
        mock_provider = Mock()
        mock_provider.create_message.return_value = {
            "content": "BLOCK: Would delete entire filesystem - extremely dangerous"
        }

        executor = ActionExecutor(
            permission_manager, llm_provider=mock_provider, model="test-model"
        )

        # Try to execute rm -rf on project directory (still dangerous but recoverable)
        success, message, result = executor.execute(
            "execute_command", {"command": "rm -rf .", "working_dir": "."}
        )

        # Should be blocked by safety checker
        assert success is False
        assert "blocked by safety agent" in message.lower()
        assert "delete entire filesystem" in message.lower()
        assert result is None

    def test_benign_command_allowed_integration(self):
        """Integration test that benign commands are allowed."""
        permission_manager = PermissionManager(PermissionConfig())

        # Mock LLM provider that allows ls commands
        mock_provider = Mock()
        mock_provider.create_message.return_value = {
            "content": "ALLOW: Simple directory listing command"
        }

        with patch("clippy.executor.execute_command") as mock_execute:
            mock_execute.return_value = (
                True,
                "Command executed successfully",
                "file1.txt\nfile2.txt",
            )

            executor = ActionExecutor(
                permission_manager, llm_provider=mock_provider, model="test-model"
            )

            # Try to execute ls command
            success, message, result = executor.execute(
                "execute_command", {"command": "ls -la", "working_dir": "/home/user"}
            )

            # Should be allowed and execute normally
            assert success is True
            assert "executed successfully" in message.lower()
            assert result == "file1.txt\nfile2.txt"

            # Verify the actual command was executed
            mock_execute.assert_called_once_with("ls -la", "/home/user", 60, False)

    def test_safety_checker_context_awareness(self):
        """Test that safety checker gets proper context about working directory."""
        permission_manager = PermissionManager(PermissionConfig())

        # Mock LLM provider that allows commands in safe dirs but blocks in system dirs
        mock_provider = Mock()

        def mock_response(messages, model=None, **kwargs):
            # Check working directory from user message
            user_msg = next(m["content"] for m in messages if m["role"] == "user")
            if "/home/user" in user_msg:
                return {"content": "ALLOW: Safe directory"}
            elif "/etc" in user_msg:
                return {"content": "BLOCK: System directory modification"}
            return {"content": "ALLOW: Unknown context"}

        mock_provider.create_message.side_effect = mock_response

        with patch("clippy.executor.execute_command") as mock_execute:
            mock_execute.return_value = (True, "Success", "output")

            executor = ActionExecutor(
                permission_manager, llm_provider=mock_provider, model="test-model"
            )

            # Command in user directory should be allowed
            success, _, _ = executor.execute(
                "execute_command", {"command": "cat config.txt", "working_dir": "/home/user"}
            )
            assert success is True

            # Same command in system directory should be blocked
            success, message, _ = executor.execute(
                "execute_command", {"command": "cat config.txt", "working_dir": "/etc"}
            )
            assert success is False
            assert "system directory" in message.lower()
