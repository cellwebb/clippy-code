"""Tests for LLM providers."""

from __future__ import annotations

import time
from typing import Any

import pytest
from pydantic_ai import ModelRequest, ModelResponse
from pydantic_ai.messages import SystemPromptPart, TextPart, ToolCallPart, UserPromptPart
from pydantic_ai.models import ModelRequestParameters

# Optional import for huggingface support
try:
    from pydantic_ai.models.huggingface import HuggingFaceModel
except ImportError:  # pragma: no cover - optional dependency
    HuggingFaceModel = None  # type: ignore

from clippy.models import ProviderConfig
from clippy.providers import LLMProvider, Spinner, _convert_tools


def _openai_chat_model_stub(model: str, provider: Any | None = None) -> str:
    """Return a deterministic identifier for monkeypatched OpenAIChatModel."""

    _ = provider  # intentionally unused, keeps signature compatible
    return f"model:{model}"


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


class TestLLMProvider:
    """Tests for the Pydantic AI backed provider."""

    def test_create_message_converts_messages_and_tools(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        provider = LLMProvider(api_key="key")

        monkeypatch.setattr("clippy.providers.OpenAIChatModel", _openai_chat_model_stub)

        captured: dict[str, Any] = {}

        def fake_model_request_sync(
            model_identifier: Any,
            messages: list[ModelRequest],
            *,
            model_request_parameters: ModelRequestParameters | None = None,
        ) -> ModelResponse:
            captured["model"] = model_identifier
            captured["messages"] = messages
            captured["params"] = model_request_parameters
            return ModelResponse(parts=[TextPart(content="Hello world")])

        monkeypatch.setattr("clippy.providers.model_request_sync", fake_model_request_sync)

        result = provider.create_message(
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Say hi"},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "description": "Write a file",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ],
            model="gpt-4o",
        )

        output = capsys.readouterr().out
        assert "[📎] Hello world" in output

        assert result == {
            "role": "assistant",
            "content": "Hello world",
            "finish_reason": None,
        }

        assert captured["model"] == "model:gpt-4o"
        assert len(captured["messages"]) == 1
        request = captured["messages"][0]
        assert isinstance(request, ModelRequest)
        assert isinstance(request.parts[0], SystemPromptPart)
        assert isinstance(request.parts[1], UserPromptPart)

        params = captured["params"]
        assert isinstance(params, ModelRequestParameters)
        assert params.function_tools is not None
        assert params.function_tools[0].name == "write_file"

    def test_create_message_returns_tool_calls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        provider = LLMProvider()

        monkeypatch.setattr("clippy.providers.OpenAIChatModel", _openai_chat_model_stub)

        def fake_model_request_sync(*_: Any, **__: Any) -> ModelResponse:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="write_file",
                        args={"path": "a.txt"},
                        tool_call_id="call-1",
                    )
                ]
            )

        monkeypatch.setattr("clippy.providers.model_request_sync", fake_model_request_sync)

        result = provider.create_message(
            messages=[{"role": "user", "content": "Create file"}],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ],
            model="gpt-4o",
        )

        assert result["tool_calls"] == [
            {
                "id": "call-1",
                "type": "function",
                "function": {"name": "write_file", "arguments": '{"path": "a.txt"}'},
            }
        ]

    def test_create_message_prefixed_model_uses_openai_provider(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        provider_config = ProviderConfig(
            name="synthetic",
            base_url="https://api.synthetic.new/openai/v1",
            api_key_env="SYN_API_KEY",
            description="Synthetic",
            pydantic_system="openai",
        )
        provider = LLMProvider(api_key="secret", provider_config=provider_config)

        captured: dict[str, Any] = {}

        def fake_model_request_sync(
            model_identifier: Any,
            *args: Any,
            model_request_parameters: ModelRequestParameters | None = None,
            **kwargs: Any,
        ) -> ModelResponse:
            captured["model"] = model_identifier
            assert model_request_parameters is not None
            return ModelResponse(parts=[TextPart(content="ok")])

        monkeypatch.setattr("clippy.providers.model_request_sync", fake_model_request_sync)

        provider.create_message(
            messages=[{"role": "user", "content": "ping"}],
            model="hf:zai-org/GLM",
        )

        # With the fix, prefixed models now use OpenAIChatModel with custom provider
        from pydantic_ai.models.openai import OpenAIChatModel

        assert isinstance(captured["model"], OpenAIChatModel)
        assert captured["model"].model_name == "hf:zai-org/GLM"

    @pytest.mark.skipif(HuggingFaceModel is None, reason="huggingface extras not installed")
    def test_resolve_model_hf_prefix_uses_huggingface_model(self) -> None:
        provider_config = ProviderConfig(
            name="hf",
            base_url=None,
            api_key_env="HF_API_KEY",
            description="HuggingFace",
            pydantic_system="huggingface",
        )
        provider = LLMProvider(api_key="secret", provider_config=provider_config)

        _, model_obj = provider._resolve_model("hf:zai-org/GLM-4.6")

        assert isinstance(model_obj, HuggingFaceModel)

    def test_resolve_model_openai_prefix_with_openai_provider(self) -> None:
        provider_config = ProviderConfig(
            name="synthetic",
            base_url="https://api.synthetic.new/openai/v1",
            api_key_env="SYN_API_KEY",
            description="Synthetic",
            pydantic_system="openai",
        )
        provider = LLMProvider(api_key="secret", provider_config=provider_config)

        resolved, model_obj = provider._resolve_model("hf:zai-org/GLM")

        assert resolved == "hf:zai-org/GLM"
        # With the fix, model_obj should now be an OpenAIChatModel, not None
        from pydantic_ai.models.openai import OpenAIChatModel

        assert isinstance(model_obj, OpenAIChatModel)
        assert model_obj.model_name == "hf:zai-org/GLM"


class TestConvertTools:
    def test_default_strict_false(self) -> None:
        defs = _convert_tools(
            [
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "description": "Write",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ]
        )

        assert defs[0].strict is False

    def test_respects_strict_flag(self) -> None:
        defs = _convert_tools(
            [
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read",
                        "strict": True,
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ]
        )

        assert defs[0].strict is True
