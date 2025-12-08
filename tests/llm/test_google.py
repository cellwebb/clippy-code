"""Tests for Google provider."""

from unittest.mock import Mock, patch

import httpx
import pytest

from clippy.llm.errors import APIConnectionError, APITimeoutError
from clippy.llm.google import GoogleProvider


class TestGoogleProvider:
    """Test the GoogleProvider class."""

    def test_init_default(self):
        """Test provider initialization with defaults."""
        provider = GoogleProvider()
        assert provider.api_key is None
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
        assert provider._client is not None
        assert isinstance(provider._client, httpx.Client)

    def test_init_custom(self):
        """Test provider initialization with custom values."""
        provider = GoogleProvider(api_key="test-key", base_url="https://custom.example.com/v1")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://custom.example.com/v1"

    def test_close(self):
        """Test closing the HTTP client."""
        provider = GoogleProvider()
        # Mock the close method since it's a real httpx.Client
        with patch.object(provider._client, "close") as mock_close:
            provider.close()
            mock_close.assert_called_once()

    def test_convert_messages(self):
        """Test message conversion to Gemini format."""
        provider = GoogleProvider()

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        contents, system_instruction = provider._convert_messages(messages)

        # Should convert to Gemini's format
        assert isinstance(contents, list)
        assert len(contents) == 2
        assert system_instruction is None

        # Check first message
        assert contents[0]["role"] == "user"
        assert contents[0]["parts"][0]["text"] == "Hello"

        # Check second message
        assert contents[1]["role"] == "model"
        assert contents[1]["parts"][0]["text"] == "Hi there!"

    def test_convert_messages_with_system(self):
        """Test message conversion with system message."""
        provider = GoogleProvider()

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        contents, system_instruction = provider._convert_messages(messages)

        # System message should be extracted
        assert system_instruction == "You are helpful"
        assert len(contents) == 1
        assert contents[0]["role"] == "user"
        assert contents[0]["parts"][0]["text"] == "Hello"

    def test_convert_messages_with_tool_calls(self):
        """Test message conversion with tool calls."""
        provider = GoogleProvider()

        messages = [
            {"role": "user", "content": "Use tool"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {"name": "test_tool", "arguments": '{"param": "value"}'},
                    }
                ],
            },
        ]

        contents, system_instruction = provider._convert_messages(messages)

        # Should convert tool calls to Gemini's format
        assert len(contents) == 2

        # Check tool call conversion
        model_message = contents[1]
        assert model_message["role"] == "model"
        assert len(model_message["parts"]) == 1
        assert "functionCall" in model_message["parts"][0]
        assert model_message["parts"][0]["functionCall"]["name"] == "test_tool"
        assert model_message["parts"][0]["functionCall"]["args"]["param"] == "value"

    def test_convert_messages_with_tool_results(self):
        """Test message conversion with tool results."""
        provider = GoogleProvider()

        messages = [{"role": "tool", "name": "test_tool", "content": '{"result": "success"}'}]

        contents, system_instruction = provider._convert_messages(messages)

        # Should convert tool results to Gemini's format
        assert len(contents) == 1
        assert contents[0]["role"] == "user"
        assert "functionResponse" in contents[0]["parts"][0]
        assert contents[0]["parts"][0]["functionResponse"]["name"] == "test_tool"
        assert contents[0]["parts"][0]["functionResponse"]["response"]["result"] == "success"

    def test_convert_tools(self):
        """Test tool conversion to Gemini format."""
        provider = GoogleProvider()

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
        assert result[0]["parameters"] == {"type": "object", "properties": {}}

    def test_convert_tools_invalid_type(self):
        """Test tool conversion with invalid tool types."""
        provider = GoogleProvider()

        tools = [{"type": "not_function"}]  # Invalid tool type

        result = provider._convert_tools(tools)

        assert len(result) == 0  # Should filter out invalid tools

    @patch("clippy.llm.google.post_with_retry")
    @patch("clippy.llm.google.raise_for_status")
    def test_create_message_simple(self, mock_raise_for_status, mock_post):
        """Test simple message creation."""
        provider = GoogleProvider(api_key="test-key")

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hello!"}], "role": "model"},
                    "finishReason": "STOP",
                }
            ]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = provider.create_message(messages, model="gemini-1.5-pro")

        mock_post.assert_called_once()
        assert result["content"] == "Hello!"
        assert result["role"] == "assistant"
        assert result["finish_reason"] == "stop"

    @patch("clippy.llm.google.post_with_retry")
    @patch("clippy.llm.google.raise_for_status")
    def test_create_message_with_tools(self, mock_raise_for_status, mock_post):
        """Test message creation with tools."""
        provider = GoogleProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "I'll use a tool"},
                            {"functionCall": {"name": "test_tool", "args": {"param": "value"}}},
                        ],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                }
            ]
        }
        mock_post.return_value = mock_response

        tools = [
            {"type": "function", "function": {"name": "test_tool", "description": "Test tool"}}
        ]  # noqa: E501
        messages = [{"role": "user", "content": "Use tool"}]

        result = provider.create_message(messages, tools=tools, model="gemini-1.5-pro")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "tools" in payload
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1

    @patch("clippy.llm.google.post_with_retry")
    @patch("clippy.llm.google.raise_for_status")
    def test_create_message_with_temperature(self, mock_raise_for_status, mock_post):
        """Test message creation with temperature parameter."""
        provider = GoogleProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Response"}], "role": "model"}}]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        provider.create_message(messages, model="gemini-1.5-pro", temperature=0.5)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        # Check if temperature was included in generation config
        generation_config = payload.get("generationConfig", {})
        assert generation_config.get("temperature") == 0.5

    @patch("clippy.llm.google.post_with_retry")
    def test_create_message_connect_error(self, mock_post):
        """Test create_message with connection error."""
        provider = GoogleProvider(api_key="test-key")
        mock_post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(APIConnectionError):
            provider.create_message([{"role": "user", "content": "Hello"}])

    @patch("clippy.llm.google.post_with_retry")
    def test_create_message_timeout_error(self, mock_post):
        """Test create_message with timeout error."""
        provider = GoogleProvider(api_key="test-key")
        mock_post.side_effect = httpx.ReadTimeout("Request timed out")

        with pytest.raises(APITimeoutError):
            provider.create_message([{"role": "user", "content": "Hello"}])

    def test_normalize_response(self):
        """Test Gemini response normalization."""
        provider = GoogleProvider()

        data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello!"},
                            {"functionCall": {"name": "test_tool", "args": {"param": "value"}}},
                        ],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
        }

        result = provider._normalize_response(data)

        assert result["role"] == "assistant"
        assert result["content"] == "Hello!"
        assert result["finish_reason"] == "stop"
        assert "tool_calls" in result
        assert result["tool_calls"][0]["function"]["name"] == "test_tool"
        assert result["usage"]["prompt_tokens"] == 10

    def test_normalize_response_text_only(self):
        """Test normalization of text-only response."""
        provider = GoogleProvider()

        data = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hello!"}], "role": "model"},
                    "finishReason": "STOP",
                }
            ]
        }

        result = provider._normalize_response(data)

        assert result["role"] == "assistant"
        assert result["content"] == "Hello!"
        assert result["finish_reason"] == "stop"
        assert "tool_calls" not in result

    def test_normalize_response_with_usage(self):
        """Test normalization with usage metadata."""
        provider = GoogleProvider()

        data = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hello!"}], "role": "model"},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 15,
                "candidatesTokenCount": 8,
                "totalTokenCount": 23,
            },
        }

        result = provider._normalize_response(data)

        assert "usage" in result
        assert result["usage"]["prompt_tokens"] == 15
        assert result["usage"]["completion_tokens"] == 8
        assert result["usage"]["total_tokens"] == 23

    def test_normalize_response_error(self):
        """Test normalization of error response."""
        provider = GoogleProvider()

        data = {"error": {"message": "API rate limit exceeded", "code": 429}}

        with pytest.raises(Exception) as exc_info:
            provider._normalize_response(data)

        assert "API rate limit exceeded" in str(exc_info.value)

    def test_map_finish_reason(self):
        """Test mapping Gemini finish reasons to OpenAI format."""
        provider = GoogleProvider()

        # Test standard mappings
        assert provider._map_finish_reason("STOP") == "stop"
        assert provider._map_finish_reason("MAX_TOKENS") == "length"
        assert provider._map_finish_reason("SAFETY") == "content_filter"
        assert provider._map_finish_reason("RECITATION") == "content_filter"
        assert provider._map_finish_reason("OTHER") == "stop"

        # Test unknown reason (should be lowercased)
        assert provider._map_finish_reason("UNKNOWN") == "unknown"

        # Test None
        assert provider._map_finish_reason(None) is None

    @patch("clippy.llm.google.post_with_retry")
    @patch("clippy.llm.google.raise_for_status")
    def test_create_message_with_generation_config(self, mock_raise_for_status, mock_post):
        """Test message creation with various generation config parameters."""
        provider = GoogleProvider(api_key="test-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Response"}], "role": "model"}}]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        provider.create_message(
            messages, model="gemini-1.5-pro", temperature=0.7, max_tokens=150, top_k=40, top_p=0.8
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        generation_config = payload.get("generationConfig", {})

        assert generation_config.get("temperature") == 0.7
        assert generation_config.get("maxOutputTokens") == 150
        assert generation_config.get("topK") == 40
        assert generation_config.get("topP") == 0.8

    def test_convert_messages_mixed_content(self):
        """Test message conversion with mixed text and tool calls."""
        provider = GoogleProvider()

        messages = [
            {
                "role": "assistant",
                "content": "I'll help you",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {"name": "search", "arguments": '{"query": "test"}'},
                    }
                ],
            }
        ]

        contents, system_instruction = provider._convert_messages(messages)

        assert len(contents) == 1
        model_message = contents[0]
        assert model_message["role"] == "model"
        assert len(model_message["parts"]) == 2  # text + function call
        assert model_message["parts"][0]["text"] == "I'll help you"
        assert model_message["parts"][1]["functionCall"]["name"] == "search"

    def test_create_url_with_api_key(self):
        """Test URL construction with API key."""
        provider = GoogleProvider(api_key="test-key")

        messages = [{"role": "user", "content": "Hello"}]

        with (
            patch("clippy.llm.google.post_with_retry") as mock_post,
            patch("clippy.llm.google.raise_for_status"),
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Hi"}]}}]
            }
            mock_post.return_value = mock_response

            provider._create_message_internal(messages, None, "gemini-1.5-pro")

            # Check that URL contains API key
            call_args = mock_post.call_args
            url = call_args[0][1]  # URL is second argument after client
            assert "key=test-key" in url

    def test_create_url_no_api_key(self):
        """Test URL construction without API key."""
        provider = GoogleProvider()

        messages = [{"role": "user", "content": "Hello"}]

        with (
            patch("clippy.llm.google.post_with_retry") as mock_post,
            patch("clippy.llm.google.raise_for_status"),
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Hi"}]}}]
            }
            mock_post.return_value = mock_response

            provider._create_message_internal(messages, None, "gemini-1.5-pro")

            # Check that URL does not contain API key
            call_args = mock_post.call_args
            url = call_args[0][1]  # URL is second argument after client
            assert "key=" not in url

    def test_convert_messages_with_system_instruction(self):
        """Test that system instruction is included in payload when present."""
        provider = GoogleProvider()

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ]

        with (
            patch("clippy.llm.google.post_with_retry") as mock_post,
            patch("clippy.llm.google.raise_for_status"),
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Hi there!"}]}}]
            }
            mock_post.return_value = mock_response

            provider._create_message_internal(messages, None, "gemini-1.5-pro")

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert "systemInstruction" in payload
            assert payload["systemInstruction"]["parts"][0]["text"] == "You are a helpful assistant"

    def test_convert_empty_messages(self):
        """Test conversion of empty message list."""
        provider = GoogleProvider()

        contents, system_instruction = provider._convert_messages([])

        assert contents == []
        assert system_instruction is None
