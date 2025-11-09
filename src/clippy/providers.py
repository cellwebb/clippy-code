"""LLM provider that uses Pydantic AI for model access."""

from __future__ import annotations

import json
import sys
import threading
import time
from typing import TYPE_CHECKING, Any

from pydantic_ai import ModelMessage, ModelRequest, ModelResponse, ToolDefinition
from pydantic_ai.direct import model_request_sync
from pydantic_ai.messages import (
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel

try:
    from pydantic_ai.models.huggingface import HuggingFaceModel
except ImportError:
    HuggingFaceModel = None  # type: ignore
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

if TYPE_CHECKING:
    from .models import ProviderConfig


class Spinner:
    """A simple terminal spinner for indicating loading status."""

    def __init__(self, message: str = "Processing", enabled: bool = True) -> None:
        self.message = message
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self.thread: threading.Thread | None = None
        self.enabled = enabled

    def _spin(self) -> None:
        """Internal method to run the spinner animation."""
        i = 0
        while self.running:
            sys.stdout.write(
                f"\r[📎] {self.message} {self.spinner_chars[i % len(self.spinner_chars)]}"
            )
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self) -> None:
        """Start the spinner."""
        if not self.enabled or self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self.running = False
        if self.thread:
            self.thread.join()

        if self.enabled:
            sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")
            sys.stdout.flush()


class LLMProvider:
    """Adapter that routes chat completions through Pydantic AI."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        provider_config: ProviderConfig | None = None,
        **_: Any,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.provider_config = provider_config

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-5",
        **_: Any,
    ) -> dict[str, Any]:
        """Create a chat completion using Pydantic AI."""

        spinner = Spinner("Thinking", enabled=sys.stdout.isatty())
        spinner.start()

        try:
            model_messages = _convert_openai_messages(messages)
            tool_definitions = _convert_tools(tools)

            params = ModelRequestParameters(
                function_tools=tool_definitions,
                allow_text_output=True,
            )

            model_identifier, model_object = self._resolve_model(model)
            target_model = model_object or self._default_provider_identifier(model_identifier)
            response = model_request_sync(
                target_model,
                model_messages,
                model_request_parameters=params,
            )
        finally:
            spinner.stop()

        result = _convert_response_to_openai(response)

        assistant_content = result.get("content")
        if assistant_content:
            # Remove leading newlines that cause emoji to appear on separate line
            cleaned_content = assistant_content.lstrip("\n")
            print(f"\n[📎] {cleaned_content}")

        return result

    def _resolve_model(self, model: str) -> tuple[str, OpenAIChatModel | None]:
        """Resolve model identifier or instantiate a configured model."""

        if ":" in model:
            system, _, model_id = model.partition(":")
            if self._should_treat_prefix_as_system():
                system = self._normalize_system(system)
                provider = self._create_provider_for_system(system)
                if provider is not None:
                    return model, provider(model_id)
                return model, None

            # For OpenAI-compatible providers, prefixed models (like hf:...) should
            # still use the custom provider settings
            if system != "openai" and self._is_openai_system():
                if self.api_key is not None or self.base_url is not None:
                    kwargs: dict[str, Any] = {}
                    if self.api_key is not None:
                        kwargs["api_key"] = self.api_key
                    if self.base_url is not None:
                        kwargs["base_url"] = self.base_url
                    provider = OpenAIProvider(**kwargs)
                    return model, OpenAIChatModel(model, provider=provider)

            if system != "openai":
                return model, None

        provider_kwargs: dict[str, Any] = {}
        if self.api_key is not None:
            provider_kwargs["api_key"] = self.api_key
        if self.base_url is not None:
            provider_kwargs["base_url"] = self.base_url

        if provider_kwargs:
            provider = OpenAIProvider(**provider_kwargs)
            return model, OpenAIChatModel(model, provider=provider)

        return f"openai:{model}", None

    def _should_treat_prefix_as_system(self) -> bool:
        if self.provider_config:
            system = self.provider_config.pydantic_system
            return system not in (None, "openai")
        return self.base_url is None

    def _normalize_system(self, system: str) -> str:
        aliases = {
            "hf": "huggingface",
        }
        return aliases.get(system, system)

    def _default_provider_identifier(self, model_identifier: str) -> str:
        """Ensure prefixed models use the correct provider hint when needed."""

        if not self._is_openai_system():
            return model_identifier

        if model_identifier.startswith("openai:"):
            return model_identifier

        if ":" in model_identifier:
            prefix, _, _ = model_identifier.partition(":")
            if prefix != "openai":
                return f"openai:{model_identifier}"

        return model_identifier

    def _is_openai_system(self) -> bool:
        if self.provider_config:
            system = self.provider_config.pydantic_system
            return system in (None, "openai")
        return True

    def _create_provider_for_system(self, system: str) -> Any | None:
        """Return a callable that builds a model for non-OpenAI systems."""

        if system == "anthropic":

            def _builder(model_id: str) -> AnthropicModel:
                provider_kwargs: dict[str, Any] = {}
                if self.api_key:
                    provider_kwargs["api_key"] = self.api_key
                if self.provider_config and self.provider_config.base_url:
                    provider_kwargs["base_url"] = self.provider_config.base_url
                provider = AnthropicProvider(**provider_kwargs)
                return AnthropicModel(model_id, provider=provider)

            return _builder

        if system in {"google", "google-gla", "gemini"}:

            def _builder_google(model_id: str) -> GoogleModel:
                provider_kwargs: dict[str, Any] = {}
                if self.api_key:
                    provider_kwargs["api_key"] = self.api_key
                if self.provider_config and self.provider_config.base_url:
                    provider_kwargs["base_url"] = self.provider_config.base_url
                provider = GoogleProvider(**provider_kwargs)
                return GoogleModel(model_id, provider=provider)

            return _builder_google

        if system == "huggingface":
            if HuggingFaceModel is None:
                raise ImportError(
                    "HuggingFace support requires additional dependencies. "
                    "Install with: pip install 'pydantic-ai-slim[huggingface]'"
                )

            def _builder_huggingface(model_id: str) -> HuggingFaceModel:
                return HuggingFaceModel(model_id)

            return _builder_huggingface

        return None


def _convert_openai_messages(messages: list[dict[str, Any]]) -> list[ModelMessage]:
    """Convert OpenAI-style messages into Pydantic AI message objects."""

    converted: list[ModelMessage] = []
    current_parts: list[Any] = []

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if role == "system":
            if content is not None:
                current_parts.append(SystemPromptPart(content=_to_text(content)))
        elif role == "user":
            if content is not None:
                current_parts.append(UserPromptPart(content=_to_text(content)))
            if current_parts:
                converted.append(ModelRequest(parts=current_parts))
                current_parts = []
        elif role == "assistant":
            if current_parts:
                converted.append(ModelRequest(parts=current_parts))
                current_parts = []

            response_parts: list[Any] = []

            text = _to_text(content)
            if text:
                response_parts.append(TextPart(content=text))

            for tool_call in message.get("tool_calls", []) or []:
                function_data = tool_call.get("function", {})
                args = function_data.get("arguments")
                parsed_args: Any
                if isinstance(args, str):
                    try:
                        parsed_args = json.loads(args)
                    except json.JSONDecodeError:
                        parsed_args = args
                else:
                    parsed_args = args or {}

                response_parts.append(
                    ToolCallPart(
                        tool_name=function_data.get("name", ""),
                        args=parsed_args,
                        tool_call_id=tool_call.get("id"),
                    )
                )

            if response_parts:
                converted.append(ModelResponse(parts=response_parts))
        elif role == "tool":
            if current_parts:
                converted.append(ModelRequest(parts=current_parts))
                current_parts = []

            tool_name = message.get("name", "")
            tool_call_id = message.get("tool_call_id") or ""
            tool_content = _safe_json_loads(content)
            converted.append(
                ModelRequest(
                    parts=[
                        ToolReturnPart(
                            tool_name=tool_name,
                            content=tool_content,
                            tool_call_id=tool_call_id,
                        )
                    ]
                )
            )

    if current_parts:
        converted.append(ModelRequest(parts=current_parts))

    return converted


def _convert_tools(tools: list[dict[str, Any]] | None) -> list[ToolDefinition]:
    """Convert OpenAI tool definitions into Pydantic AI tool definitions."""

    tool_defs: list[ToolDefinition] = []
    if not tools:
        return tool_defs

    for tool in tools:
        if tool.get("type") != "function":
            continue

        function = tool.get("function", {})
        parameters = function.get("parameters")
        strict_value = function.get("strict")
        strict_flag = bool(strict_value) if strict_value is not None else False
        description = tool.get("description") or function.get("description")
        tool_defs.append(
            ToolDefinition(
                name=function.get("name", ""),
                description=description,
                parameters_json_schema=parameters or {},
                strict=strict_flag,
            )
        )

    return tool_defs


def _convert_response_to_openai(response: ModelResponse) -> dict[str, Any]:
    """Convert a Pydantic AI model response back to OpenAI-style message dict."""

    content_chunks: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    for part in response.parts:
        if isinstance(part, TextPart):
            if part.content:
                content_chunks.append(part.content)
        elif isinstance(part, ToolCallPart):
            arguments = part.args if part.args is not None else {}
            arguments_str = arguments if isinstance(arguments, str) else json.dumps(arguments)
            tool_calls.append(
                {
                    "id": part.tool_call_id or "",
                    "type": "function",
                    "function": {
                        "name": part.tool_name,
                        "arguments": arguments_str,
                    },
                }
            )

    content = "".join(content_chunks) if content_chunks else None

    result: dict[str, Any] = {
        "role": "assistant",
        "content": content,
        "finish_reason": None,
    }

    if tool_calls:
        result["tool_calls"] = tool_calls

    return result


def _to_text(content: Any) -> str:
    """Convert message content to a plain string."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(segment.get("text", "") for segment in content if isinstance(segment, dict))
    if content is None:
        return ""
    return str(content)


def _safe_json_loads(content: Any) -> Any:
    """Attempt to JSON-decode tool output content when appropriate."""

    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    return content
