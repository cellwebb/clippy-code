"""Simple tests for OpenAI provider."""

from unittest.mock import Mock, patch

import httpx
import pytest

from clippy.llm.errors import APIConnectionError, APITimeoutError
from clippy.llm.openai import OpenAIProvider, _is_reasoner_model


class TestOpenAIProviderSimple:
    """Test the OpenAIProvider class."""

    def test_init_default(self):
        """Test provider initialization with defaults."""
        provider = OpenAIProvider()
        assert provider.api_key is None
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider._client is not None

    def test_init_custom(self):
        """Test provider initialization with custom values."""
        provider = OpenAIProvider(api_key="test-key", base_url="https://custom.example.com/v1")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://custom.example.com/v1"

    def test_close(self):
        """Test closing the HTTP client."""
        provider = OpenAIProvider()
        provider.close()  # Should not raise

    def test_headers(self):
        """Test header generation."""
        provider = OpenAIProvider(api_key="test-key")
        headers = provider._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_headers_no_api_key(self):
        """Test header generation without API key."""
        provider = OpenAIProvider()
        headers = provider._headers()
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_is_reasoner_model(self):
        """Test reasoner model detection."""
        # Should return True for reasoner models
        assert _is_reasoner_model("deepseek-r1")
        assert _is_reasoner_model("deepseek-reasoner")

        # Should return False for non-reasoner models
        assert not _is_reasoner_model("gpt-4")
        assert not _is_reasoner_model("deepseek-chat")

    @patch("clippy.llm.openai.post_with_retry")
    @patch("clippy.llm.openai.raise_for_status")
    def test_create_message_basic(self, mock_raise_for_status, mock_post):
        """Test basic message creation."""
        provider = OpenAIProvider(api_key="test-key")

        mock_response = Mock()
        # Set response data with proper line length
        response_data = {
            "choices": [
                {"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}
            ]  # noqa: E501
        }
        mock_response.json.return_value = response_data
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = provider.create_message(messages, model="gpt-4")

        assert result["content"] == "Hello!"
        assert result["role"] == "assistant"

    @patch("clippy.llm.openai.post_with_retry")
    def test_create_message_connect_error(self, mock_post):
        """Test create_message with connection error."""
        provider = OpenAIProvider(api_key="test-key")
        mock_post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(APIConnectionError):
            provider.create_message([{"role": "user", "content": "Hello"}])

    @patch("clippy.llm.openai.post_with_retry")
    def test_create_message_timeout_error(self, mock_post):
        """Test create_message with timeout error."""
        provider = OpenAIProvider(api_key="test-key")
        mock_post.side_effect = httpx.ReadTimeout("Request timed out")

        with pytest.raises(APITimeoutError):
            provider.create_message([{"role": "user", "content": "Hello"}])

    def test_prepare_messages_for_chat_regular_model(self):
        """Test message preparation for regular models."""
        provider = OpenAIProvider()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!", "reasoning_content": "some reasoning"},
        ]

        result = provider._prepare_messages_for_chat(messages, "gpt-4")

        # Should be unchanged for regular models
        assert result == messages

    def test_normalization_functions(self):
        """Test response normalization functions exist and work."""
        provider = OpenAIProvider()

        # Test chat response normalization
        chat_data = {
            "choices": [
                {"message": {"role": "assistant", "content": "Hi"}, "finish_reason": "stop"}
            ]  # noqa: E501
        }
        result = provider._normalize_chat_response(chat_data)
        assert result["role"] == "assistant"
        assert result["content"] == "Hi"

        # Test responses API normalization
        responses_data = {"output_text": "Response", "status": "completed"}
        result = provider._normalize_responses_response(responses_data)
        assert result["role"] == "assistant"
        assert result["content"] == "Response"
