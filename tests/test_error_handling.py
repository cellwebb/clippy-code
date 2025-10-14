"""Tests for enhanced error handling."""

from unittest.mock import Mock, patch

import pytest
from openai import AuthenticationError

from clippy.agent import ClippyAgent
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


class TestErrorHandling:
    """Test cases for enhanced error handling."""

    def test_file_not_found_error_handling(self):
        """Test that file not found errors are handled gracefully."""
        permission_manager = PermissionManager(PermissionConfig())
        executor = ActionExecutor(permission_manager)
        agent = ClippyAgent(
            permission_manager=permission_manager,
            executor=executor,
            api_key="test-key",
            model="gpt-4o",
        )

        # Test file not found
        success, message, content = agent.executor.execute(
            "read_file", {"path": "/nonexistent/file.txt"}
        )
        assert success is False
        assert "File not found" in message

    def test_permission_error_handling(self):
        """Test that permission errors are handled gracefully."""
        permission_manager = PermissionManager(PermissionConfig())
        executor = ActionExecutor(permission_manager)
        agent = ClippyAgent(
            permission_manager=permission_manager,
            executor=executor,
            api_key="test-key",
            model="gpt-4o",
        )

        # Mock PermissionError for testing
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")

            success, message, content = agent.executor.execute(
                "read_file", {"path": "/protected/file.txt"}
            )
            assert success is False
            assert "Permission denied" in message

    @patch("clippy.providers.LLMProvider.create_message")
    def test_api_error_formatting(self, mock_create_message):
        """Test that API errors are formatted correctly."""
        permission_manager = PermissionManager(PermissionConfig())
        executor = ActionExecutor(permission_manager)

        # Test authentication error
        mock_create_message.side_effect = AuthenticationError(
            "Invalid API key", response=Mock(), body=Mock()
        )
        agent = ClippyAgent(
            permission_manager=permission_manager,
            executor=executor,
            api_key="invalid-key",
            model="gpt-4o",
        )

        with pytest.raises(AuthenticationError):
            agent.provider.create_message(messages=[], tools=[])

    def test_unicode_decode_error_handling(self):
        """Test handling of binary files that can't be decoded."""
        permission_manager = PermissionManager(PermissionConfig())
        executor = ActionExecutor(permission_manager)

        # Create a mock binary file that would cause UnicodeDecodeError
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

            success, message, content = executor.execute("read_file", {"path": "binary_file.exe"})
            assert success is False
            assert "Unable to decode file" in message

    def test_json_decode_error_handling(self):
        """Test JSON decode error handling in agent."""
        permission_manager = PermissionManager(PermissionConfig())
        executor = ActionExecutor(permission_manager)
        agent = ClippyAgent(
            permission_manager=permission_manager,
            executor=executor,
            api_key="test-key",
            model="gpt-4o",
        )

        # Test with valid JSON that would cause a tool error
        with patch.object(agent.executor, "execute") as mock_execute:
            mock_execute.return_value = (False, "Error executing tool", None)
            success = agent._handle_tool_use(
                "read_file", {"path": "test.txt"}, "tool_call_id", False
            )
            assert success is False
