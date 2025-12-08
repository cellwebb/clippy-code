"""Tests for Anthropic provider."""

from unittest.mock import Mock, patch

import httpx
import pytest

from clippy.llm.anthropic import AnthropicProvider
from clippy.llm.errors import APIConnectionError, APITimeoutError


class TestAnthropicProvider:
    """Test the AnthropicProvider class."""

    def test_init_default(self):
        """Test provider initialization with defaults."""
        provider = AnthropicProvider()
        assert provider.api_key is None
        assert provider.base_url == "https://api.anthropic.com"
        assert provider._client is not None

    def test_init_custom(self):
        """Test provider initialization with custom values."""
        provider = AnthropicProvider(api_key="test-key", base_url="https://custom.example.com")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://custom.example.com"

    def test_close(self):
        """Test closing the HTTP client."""
        provider = AnthropicProvider()
        with patch.object(provider._client, "close") as mock_close:
            provider.close()
            mock_close.assert_called_once()

    def test_headers(self):
        """Test header generation."""
        provider = AnthropicProvider(api_key="test-key")
        headers = provider._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["x-api-key"] == "test-key"
        assert headers["anthropic-version"] == "2023-06-01"

    def test_headers_no_api_key(self):
        """Test header generation without API key."""
        provider = AnthropicProvider()
        headers = provider._headers()
        assert headers["Content-Type"] == "application/json"
        assert "x-api-key" not in headers
        assert headers["anthropic-version"] == "2023-06-01"

    def test_convert_message_user(self):
        """Test user message conversion."""
        provider = AnthropicProvider()

        msg = {"role": "user", "content": "Hello"}
        result = provider._convert_message(msg)

        assert result == {"role": "user", "content": "Hello"}

    def test_convert_message_assistant(self):
        """Test assistant message conversion."""
        provider = AnthropicProvider()

        msg = {"role": "assistant", "content": "Hi there!"}
        result = provider._convert_message(msg)

        assert result == {"role": "assistant", "content": [{"type": "text", "text": "Hi there!"}]}

    def test_convert_message_assistant_with_tool_calls(self):
        """Test assistant message with tool calls conversion."""
        provider = AnthropicProvider()

        msg = {
            "role": "assistant",
            "content": "I'll use a tool",
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {"name": "test_tool", "arguments": '{"param": "value"}'},
                }
            ],
        }
        result = provider._convert_message(msg)

        assert result["role"] == "assistant"
        assert len(result["content"]) == 2
        assert result["content"][0] == {"type": "text", "text": "I'll use a tool"}
        assert result["content"][1]["type"] == "tool_use"
        assert result["content"][1]["name"] == "test_tool"
        assert result["content"][1]["input"] == {"param": "value"}

    def test_convert_message_tool(self):
        """Test tool message conversion."""
        provider = AnthropicProvider()

        msg = {"role": "tool", "tool_call_id": "call_1", "content": "Tool result"}
        result = provider._convert_message(msg)

        assert result["role"] == "user"
        assert result["content"][0]["type"] == "tool_result"
        assert result["content"][0]["tool_use_id"] == "call_1"
        assert result["content"][0]["content"] == "Tool result"

    def test_convert_message_unknown_role(self):
        """Test unknown role message conversion."""
        provider = AnthropicProvider()

        msg = {"role": "unknown", "content": "Hello"}
        result = provider._convert_message(msg)

        assert result is None

    def test_convert_tools(self):
        """Test tool conversion to Anthropic format."""
        provider = AnthropicProvider()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        result = provider._convert_tools(tools)

        assert len(result) == 1
        assert result[0]["name"] == "test_tool"
        assert result[0]["description"] == "A test tool"
        assert result[0]["input_schema"] == {"type": "object", "properties": {}}

    def test_convert_tools_invalid_type(self):
        """Test tool conversion with invalid type."""
        provider = AnthropicProvider()

        tools = [{"type": "not_function"}]

        result = provider._convert_tools(tools)

        assert len(result) == 0

    def test_merge_consecutive_messages(self):
        """Test merging consecutive messages with same role."""
        provider = AnthropicProvider()

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "Hi!"},
        ]

        result = provider._merge_consecutive_messages(messages)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        # Content should be merged
        if isinstance(result[0]["content"], list):
            assert len(result[0]["content"]) == 2
        else:
            # String content case
            assert "Hello" in result[0]["content"]
            assert "How are you?" in result[0]["content"]

    def test_merge_consecutive_messages_empty(self):
        """Test merging empty message list."""
        provider = AnthropicProvider()

        result = provider._merge_consecutive_messages([])

        assert result == []

    def test_normalize_response_text_only(self):
        """Test Anthropic response normalization with text only."""
        provider = AnthropicProvider()

        data = {"content": [{"type": "text", "text": "Hello!"}], "stop_reason": "end_turn"}

        result = provider._normalize_response(data)

        assert result["role"] == "assistant"
        assert result["content"] == "Hello!"
        assert result["finish_reason"] == "stop"

    def test_normalize_response_with_tools(self):
        """Test Anthropic response normalization with tool calls."""
        provider = AnthropicProvider()

        data = {
            "content": [
                {"type": "text", "text": "I'll use a tool"},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "test_tool",
                    "input": {"param": "value"},
                },  # noqa: E501
            ],
            "stop_reason": "tool_use",
        }

        result = provider._normalize_response(data)

        assert result["role"] == "assistant"
        assert result["content"] == "I'll use a tool"
        assert result["finish_reason"] == "tool_calls"
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "toolu_1"
        assert result["tool_calls"][0]["function"]["name"] == "test_tool"

    def test_normalize_response_with_usage(self):
        """Test Anthropic response normalization with usage info."""
        provider = AnthropicProvider()

        data = {
            "content": [{"type": "text", "text": "Hello!"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        result = provider._normalize_response(data)

        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 5
        assert result["usage"]["total_tokens"] == 15

    def test_map_stop_reason(self):
        """Test mapping Anthropic stop reasons to OpenAI format."""
        provider = AnthropicProvider()

        assert provider._map_stop_reason("end_turn") == "stop"
        assert provider._map_stop_reason("stop_sequence") == "stop"
        assert provider._map_stop_reason("tool_use") == "tool_calls"
        assert provider._map_stop_reason("max_tokens") == "length"
        assert provider._map_stop_reason("unknown") == "unknown"
        assert provider._map_stop_reason(None) is None

    @patch("clippy.llm.anthropic.post_with_retry")
    @patch("clippy.llm.anthropic.raise_for_status")
    def test_create_message_simple(self, mock_raise_for_status, mock_post):
        """Test simple message creation."""
        provider = AnthropicProvider(api_key="test-key")

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Hello!"}],
            "stop_reason": "end_turn",
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = provider.create_message(messages)

        mock_post.assert_called_once()
        assert result["content"] == "Hello!"
        assert result["role"] == "assistant"

    @patch("clippy.llm.anthropic.post_with_retry")
    @patch("clippy.llm.anthropic.raise_for_status")
    def test_create_message_with_system(self, mock_raise_for_status, mock_post):
        """Test message creation with system message."""
        provider = AnthropicProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Response"}],
            "stop_reason": "end_turn",
        }
        mock_post.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        provider.create_message(messages)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "system" in payload
        assert payload["system"] == "You are helpful"

    @patch("clippy.llm.anthropic.post_with_retry")
    @patch("clippy.llm.anthropic.raise_for_status")
    def test_create_message_with_tools(self, mock_raise_for_status, mock_post):
        """Test message creation with tools."""
        provider = AnthropicProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [
                {"type": "text", "text": "I'll use a tool"},
                {"type": "tool_use", "id": "toolu_1", "name": "test_tool", "input": {}},
            ],
            "stop_reason": "tool_use",
        }
        mock_post.return_value = mock_response

        tools = [
            {"type": "function", "function": {"name": "test_tool", "description": "Test tool"}}
        ]  # noqa: E501
        messages = [{"role": "user", "content": "Use tool"}]

        result = provider.create_message(messages, tools=tools)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "tools" in payload
        assert "tool_calls" in result

    @patch(
        "clippy.llm.anthropic.post_with_retry", side_effect=httpx.ConnectError("Connection failed")
    )
    def test_create_message_connect_error(self, mock_post):
        """Test create_message with connection error."""
        provider = AnthropicProvider(api_key="test-key")

        with pytest.raises(APIConnectionError):
            provider.create_message([{"role": "user", "content": "Hello"}])

    @patch(
        "clippy.llm.anthropic.post_with_retry", side_effect=httpx.ReadTimeout("Request timed out")
    )
    def test_create_message_timeout_error(self, mock_post):
        """Test create_message with timeout error."""
        provider = AnthropicProvider(api_key="test-key")

        with pytest.raises(APITimeoutError):
            provider.create_message([{"role": "user", "content": "Hello"}])


class TestClaudeCodeOAuthProvider:
    """Test the ClaudeCodeOAuthProvider class."""

    @patch("clippy.llm.anthropic.create_client")
    def test_init(self, mock_create_client):
        """Test OAuth provider initialization."""
        from clippy.llm.anthropic import ClaudeCodeOAuthProvider

        provider = ClaudeCodeOAuthProvider(api_key="oauth-token")

        assert provider.api_key == "oauth-token"
        assert provider.base_url == "https://api.anthropic.com"
        assert provider._reauth_in_progress is False
        assert "oauth-2025-04-20" in provider._extra_headers["anthropic-beta"]

    def test_is_auth_error(self):
        """Test authentication error detection."""
        from clippy.llm.anthropic import ClaudeCodeOAuthProvider

        provider = ClaudeCodeOAuthProvider()

        # Test various auth error messages
        assert provider._is_auth_error(Exception("401 Unauthorized"))
        assert provider._is_auth_error(Exception("403 Forbidden"))
        assert provider._is_auth_error(Exception("Token expired"))
        assert provider._is_auth_error(Exception("Authentication failed"))
        assert not provider._is_auth_error(Exception("Other error"))
        assert not provider._is_auth_error(Exception("Rate limit exceeded"))
