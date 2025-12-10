"""Tests for LLM providers."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from clippy.llm import AnthropicProvider, GoogleProvider, OpenAIProvider, create_provider
from clippy.models import ProviderConfig
from clippy.providers import LLMProvider, Spinner


class TestSpinner:
    """Tests for Spinner class."""

    def test_spinner_initialization(self) -> None:
        spinner = Spinner("Loading", enabled=True)

        assert spinner.message == "Loading"
        assert spinner.enabled is True
        assert spinner.running is False
        assert spinner.thread is None

    def test_spinner_disabled(self) -> None:
        spinner = Spinner("Loading", enabled=False)
        spinner.start()

        assert spinner.running is False
        assert spinner.thread is None

    def test_spinner_start_and_stop(self) -> None:
        spinner = Spinner("Loading", enabled=True)
        spinner.start()

        assert spinner.running is True
        assert spinner.thread is not None
        assert spinner.thread.is_alive()

        time.sleep(0.2)

        spinner.stop()

        assert spinner.running is False

    def test_spinner_does_not_start_twice(self) -> None:
        spinner = Spinner("Loading", enabled=True)
        spinner.start()
        first_thread = spinner.thread

        spinner.start()

        assert spinner.thread is first_thread

        spinner.stop()

    def test_spinner_custom_message(self) -> None:
        spinner = Spinner("Custom Message", enabled=True)
        assert spinner.message == "Custom Message"


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_initialization(self) -> None:
        provider = OpenAIProvider(api_key="test-key", base_url="https://api.example.com")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.example.com"

    def test_default_base_url(self) -> None:
        provider = OpenAIProvider(api_key="test-key")

        assert provider.base_url == "https://api.openai.com/v1"

    def test_should_use_responses_api(self) -> None:
        provider = OpenAIProvider()

        assert provider._should_use_responses_api("gpt-5-mini") is False
        assert provider._should_use_responses_api("gpt-5-codex") is True
        assert provider._should_use_responses_api("o3-codex-mini") is True

    def test_headers(self) -> None:
        provider = OpenAIProvider(api_key="test-key")
        headers = provider._headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_normalize_chat_response(self) -> None:
        provider = OpenAIProvider()

        response_data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello!",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {"name": "test", "arguments": "{}"},
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        result = provider._normalize_chat_response(response_data)

        assert result["role"] == "assistant"
        assert result["content"] == "Hello!"
        assert result["finish_reason"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"

    def test_convert_tools_to_responses_format(self) -> None:
        provider = OpenAIProvider()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write a file",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        converted = provider._convert_tools_to_responses_format(tools)

        assert len(converted) == 1
        assert converted[0]["type"] == "function"
        assert converted[0]["name"] == "write_file"
        assert converted[0]["description"] == "Write a file"
        # Responses API uses flat structure (no nested "function")
        assert "function" not in converted[0]

    @patch("clippy.llm.openai.post_with_retry")
    def test_create_message_chat_completions(self, mock_post: MagicMock) -> None:
        """Test Chat Completions API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}
            ]
        }
        mock_response.is_success = True
        mock_post.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        result = provider.create_message(
            messages=[{"role": "user", "content": "Hi"}], model="gpt-5-mini"
        )

        assert result["content"] == "Hello!"
        assert result["role"] == "assistant"

        # Verify the URL used
        call_args = mock_post.call_args
        assert "/chat/completions" in call_args[0][1]


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_initialization(self) -> None:
        provider = AnthropicProvider(api_key="test-key")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.anthropic.com"

    def test_headers(self) -> None:
        provider = AnthropicProvider(api_key="test-key")
        headers = provider._headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["x-api-key"] == "test-key"
        assert "anthropic-version" in headers

    def test_convert_tools(self) -> None:
        provider = AnthropicProvider()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
                },
            }
        ]

        converted = provider._convert_tools(tools)

        assert len(converted) == 1
        assert converted[0]["name"] == "read_file"
        assert converted[0]["description"] == "Read a file"
        assert "input_schema" in converted[0]

    def test_map_stop_reason(self) -> None:
        provider = AnthropicProvider()

        assert provider._map_stop_reason("end_turn") == "stop"
        assert provider._map_stop_reason("tool_use") == "tool_calls"
        assert provider._map_stop_reason("max_tokens") == "length"
        assert provider._map_stop_reason(None) is None


class TestGoogleProvider:
    """Tests for Google Gemini provider."""

    def test_initialization(self) -> None:
        provider = GoogleProvider(api_key="test-key")

        assert provider.api_key == "test-key"
        assert "generativelanguage.googleapis.com" in provider.base_url

    def test_convert_tools(self) -> None:
        provider = GoogleProvider()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search for something",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        converted = provider._convert_tools(tools)

        assert len(converted) == 1
        assert converted[0]["name"] == "search"

    def test_map_finish_reason(self) -> None:
        provider = GoogleProvider()

        assert provider._map_finish_reason("STOP") == "stop"
        assert provider._map_finish_reason("MAX_TOKENS") == "length"
        assert provider._map_finish_reason("SAFETY") == "content_filter"
        assert provider._map_finish_reason(None) is None


class TestCreateProvider:
    """Tests for provider factory function."""

    def test_create_openai_provider(self) -> None:
        provider = create_provider("openai", api_key="test")
        assert isinstance(provider, OpenAIProvider)

    def test_create_anthropic_provider(self) -> None:
        provider = create_provider("anthropic", api_key="test")
        assert isinstance(provider, AnthropicProvider)

    def test_create_google_provider(self) -> None:
        provider = create_provider("google", api_key="test")
        assert isinstance(provider, GoogleProvider)

    def test_create_gemini_alias(self) -> None:
        provider = create_provider("gemini", api_key="test")
        assert isinstance(provider, GoogleProvider)

    def test_default_to_openai(self) -> None:
        provider = create_provider("unknown", api_key="test")
        assert isinstance(provider, OpenAIProvider)


class TestLLMProviderWrapper:
    """Tests for the LLMProvider wrapper class."""

    def test_initialization_with_provider_config(self) -> None:
        config = ProviderConfig(
            name="test",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            description="Test provider",
            pydantic_system="openai",
        )

        provider = LLMProvider(api_key="key", provider_config=config)

        assert provider.api_key == "key"
        assert provider.provider_config == config

    def test_initialization_with_anthropic_config(self) -> None:
        config = ProviderConfig(
            name="claude",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_KEY",
            description="Anthropic",
            pydantic_system="anthropic",
        )

        provider = LLMProvider(api_key="key", provider_config=config)

        assert isinstance(provider._provider, AnthropicProvider)

    @patch.object(OpenAIProvider, "create_message")
    def test_create_message_delegates(self, mock_create: MagicMock) -> None:
        mock_create.return_value = {
            "role": "assistant",
            "content": "Hello!",
            "finish_reason": "stop",
        }

        provider = LLMProvider(api_key="key")
        result = provider.create_message(
            messages=[{"role": "user", "content": "Hi"}], model="gpt-5-mini"
        )

        assert result["content"] == "Hello!"
        mock_create.assert_called_once()
