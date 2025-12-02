"""Tests for enhanced error handling."""

from unittest.mock import patch

import pytest

from clippy.agent import ClippyAgent, handle_tool_use
from clippy.agent.errors import format_api_error
from clippy.executor import ActionExecutor
from clippy.llm.errors import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    LLMError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
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
            model="gpt-5",
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
            model="gpt-5",
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

        # Test authentication error using our custom error class
        mock_create_message.side_effect = AuthenticationError("Invalid API key")
        agent = ClippyAgent(
            permission_manager=permission_manager,
            executor=executor,
            api_key="invalid-key",
            model="gpt-5",
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
            model="gpt-5",
        )

        # Test with valid JSON that would cause a tool error
        with patch.object(executor, "execute") as mock_execute:
            mock_execute.return_value = (False, "Error executing tool", None)
            success = handle_tool_use(
                "read_file",
                {"path": "test.txt"},
                "tool_call_id",
                False,
                permission_manager,
                executor,
                agent.console,
                agent.conversation_history,
                None,
            )
            assert success is False


def test_format_api_error_authentication():
    """Ensure known LLM errors are rendered with friendly hints."""
    error = AuthenticationError("bad key")
    message = format_api_error(error)

    assert "Authentication failed" in message
    assert "OPENAI_API_KEY" in message


def test_format_api_error_unknown():
    """Verify fallback messaging for unknown errors."""

    class CustomError(Exception):
        pass

    error = CustomError("boom")
    message = format_api_error(error)

    assert message == "CustomError: boom"


def test_format_api_error_llm_error():
    """Test that LLMError base class is handled."""
    error = LLMError("generic llm error")
    message = format_api_error(error)

    assert "API Error:" in message


@pytest.mark.parametrize(
    ("error_class", "expected"),
    [
        (RateLimitError, "Rate limit exceeded"),
        (APIConnectionError, "Connection error"),
        (APITimeoutError, "Request timeout"),
        (BadRequestError, "Bad request"),
        (InternalServerError, "Server error"),
        (PermissionDeniedError, "Permission denied"),
        (NotFoundError, "Resource not found"),
        (ConflictError, "Conflict error"),
        (UnprocessableEntityError, "Unprocessable entity"),
    ],
)
def test_format_api_error_known_branches(error_class, expected):
    """Exercise the specialised messaging for individual LLM errors."""
    error = error_class("boom")
    message = format_api_error(error)

    assert expected in message
