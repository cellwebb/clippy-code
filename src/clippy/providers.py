"""LLM provider that uses Pydantic AI for model access."""

from __future__ import annotations

import json
import logging
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

# HuggingFace support removed - no one uses it! 📎
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

if TYPE_CHECKING:
    from .models import ProviderConfig

# Provider constants
logger = logging.getLogger(__name__)
SPINNER_SLEEP_INTERVAL = 0.1  # seconds
RETRY_DELAY = 1.0  # seconds
MAX_RETRY_ATTEMPTS = 3

# Module-level storage for reasoning_content to support reasoner models
_reasoning_storage: dict[int, str] = {}  # message_index -> reasoning_content


def _is_reasoner_model(model: str) -> bool:
    """Check if a model is a DeepSeek reasoner model that needs special handling."""
    model_lower = model.lower()
    return "reasoner" in model_lower or "deepseek-r1" in model_lower


class ClaudeCodeOAuthProvider(AnthropicProvider):
    """Custom Anthropic provider for Claude Code OAuth authentication.

    This provider uses the special OAuth token and headers required for Claude Code subscriptions.
    It automatically handles the exact system message requirement and proper authentication headers.
    It also automatically re-authenticates when the OAuth token expires.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        # Claude Code OAuth always uses the standard Anthropic API
        super().__init__(
            api_key=api_key,
            base_url=base_url or "https://api.anthropic.com",
            **kwargs,
        )
        self._reauth_in_progress = False

    def _make_request(self, *args: Any, **kwargs: Any) -> Any:
        """Override to add Claude Code specific headers and handle auto-reauthentication."""
        # Add the special anthropic-beta header for OAuth
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["anthropic-beta"] = "oauth-2025-04-20"

        # Try the request
        try:
            response = super()._make_request(*args, **kwargs)  # type: ignore
            return response
        except Exception as exc:
            # Check if this is an authentication error
            if self._is_auth_error(exc) and not self._reauth_in_progress:
                return self._handle_auth_error_and_retry(args, kwargs)
            else:
                raise

    def _is_auth_error(self, exc: Exception) -> bool:
        """Check if an exception is an authentication error."""
        exc_str = str(exc).lower()
        # Look for common authentication error indicators
        auth_indicators = [
            "401",
            "403",
            "unauthorized",
            "forbidden",
            "invalid token",
            "expired",
            "authentication failed",
            "token",
        ]
        return any(indicator in exc_str for indicator in auth_indicators)

    def _handle_auth_error_and_retry(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """Handle authentication error by re-authenticating and retrying the request."""
        # Prevent infinite recursion
        self._reauth_in_progress = True

        try:
            # Import here to avoid circular imports
            from .oauth.claude_code import ensure_valid_token

            logger.info("🔐 Claude Code token expired - attempting automatic re-authentication...")

            # Attempt to re-authenticate
            if ensure_valid_token(quiet=False, force_reauth=True):
                # Update the API key with the new token
                from .oauth.claude_code import load_stored_token

                new_token = load_stored_token(check_expiry=False)
                if new_token and hasattr(self._client, "api_key"):
                    self._client.api_key = new_token
                    logger.info("✅ Re-authentication successful - retrying request...")

                    # Update headers with new token
                    if "headers" in kwargs:
                        kwargs["headers"]["Authorization"] = f"Bearer {new_token}"

                    # Retry the request
                    return super()._make_request(*args, **kwargs)  # type: ignore

            logger.error("❌ Automatic re-authentication failed")
            raise Exception("Claude Code OAuth re-authentication failed")

        finally:
            self._reauth_in_progress = False


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
            time.sleep(SPINNER_SLEEP_INTERVAL)
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


def _patch_deepseek_reasoner(target_model: Any) -> Any:
    """Patch a DeepSeek reasoner model to preserve reasoning_content."""
    if not hasattr(target_model, "_deepseek_patched"):
        target_model._deepseek_patched = True
        original_map_messages = target_model._map_messages

        async def patched_map_messages(msgs: Any, mrp: Any) -> Any:
            """Patched version that adds reasoning_content for DeepSeek."""
            openai_messages = await original_map_messages(msgs, mrp)

            # Add reasoning_content to assistant messages with tool_calls
            for i, openai_msg in enumerate(openai_messages):
                if openai_msg.get("role") == "assistant" and "tool_calls" in openai_msg:
                    # Check if we have reasoning_marker in the pydantic messages
                    for j, msg in enumerate(msgs):
                        if (
                            hasattr(msg, "parts")
                            and j < len(msgs)
                            and isinstance(msgs[j].parts, list)
                        ):
                            for part in msgs[j].parts:
                                if (
                                    hasattr(part, "content")
                                    and part.content
                                    and "[REASONING]" in part.content
                                ):
                                    # Extract reasoning content
                                    start = part.content.find("[REASONING]") + len("[REASONING]")
                                    end = part.content.find("[/REASONING]", start)
                                    if end > start:
                                        reasoning = part.content[start:end].strip()
                                        openai_msg["reasoning_content"] = reasoning
                                        break

            return openai_messages

        target_model._map_messages = patched_map_messages

    return target_model


def _apply_reasoner_patch(target_model: Any, model: str, messages: Any = None) -> Any:
    """Apply patch for reasoner models to preserve reasoning_content."""
    if "reasoner" in model.lower() and not hasattr(target_model, "_reasoner_patched"):
        target_model._reasoner_patched = True
        original_map_messages = target_model._map_messages

        async def patched_map_messages(msgs: Any, mrp: Any) -> Any:
            """Patched _map_messages that adds reasoning_content for reasoner models."""
            openai_messages = await original_map_messages(msgs, mrp)

            # Try to find reasoning_content for assistant messages with tool_calls
            for i, openai_msg in enumerate(openai_messages):
                if (
                    openai_msg.get("role") == "assistant"
                    and "tool_calls" in openai_msg
                    and "reasoning_content" not in openai_msg
                ):
                    # Look for reasoning in global storage
                    for conv_hash, reasoning in _reasoning_storage.items():
                        # Check if this reasoning applies to any assistant message
                        if reasoning:
                            openai_msg["reasoning_content"] = reasoning
                            break

            return openai_messages

        target_model._map_messages = patched_map_messages

    return target_model


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

    def _create_message_for_reasoner(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "deepseek-reasoner",
    ) -> dict[str, Any]:
        """Create a chat completion for DeepSeek reasoner models using OpenAI SDK directly.

        DeepSeek reasoner models require special handling for the `reasoning_content` field.
        When tool calls are made, the API requires that subsequent requests include the
        `reasoning_content` from the assistant's response. Pydantic AI doesn't preserve
        this field, so we use the OpenAI SDK directly for these models.

        See: https://api-docs.deepseek.com/guides/reasoning_model
        """
        import openai

        # Build client with appropriate configuration
        client_kwargs: dict[str, Any] = {}
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        elif self.provider_config and self.provider_config.base_url:
            client_kwargs["base_url"] = self.provider_config.base_url

        client = openai.OpenAI(**client_kwargs)

        # Prepare messages - keep reasoning_content for assistant messages with tool_calls
        # but only within the current turn (after the last user message)
        api_messages = []
        last_user_idx = -1

        # Find the last user message index
        for i, msg in enumerate(messages):
            if msg.get("role") == "user":
                last_user_idx = i

        for i, msg in enumerate(messages):
            role = msg.get("role")
            api_msg: dict[str, Any] = {"role": role}

            if role == "system":
                api_msg["content"] = msg.get("content", "")
            elif role == "user":
                api_msg["content"] = msg.get("content", "")
            elif role == "assistant":
                content = msg.get("content")
                if content:
                    api_msg["content"] = content

                # Include tool_calls if present
                if msg.get("tool_calls"):
                    api_msg["tool_calls"] = msg["tool_calls"]

                    # Include reasoning_content ONLY for messages after the last user message
                    # (within the current tool-calling turn)
                    if i > last_user_idx and msg.get("reasoning_content"):
                        api_msg["reasoning_content"] = msg["reasoning_content"]
            elif role == "tool":
                api_msg["role"] = "tool"
                api_msg["tool_call_id"] = msg.get("tool_call_id", "")
                api_msg["content"] = msg.get("content", "")

            api_messages.append(api_msg)

        # Prepare request kwargs
        request_kwargs: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
        }

        # Add tools if provided
        if tools:
            request_kwargs["tools"] = tools

        # Make the API call
        response = client.chat.completions.create(**request_kwargs)

        # Extract the response
        choice = response.choices[0]
        message = choice.message

        result: dict[str, Any] = {
            "role": "assistant",
            "content": message.content,
            "finish_reason": choice.finish_reason,
        }

        # Capture tool_calls if present
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        # Capture reasoning_content - this is the key field for DeepSeek reasoner
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            result["reasoning_content"] = message.reasoning_content

        return result

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
            # Use direct OpenAI SDK for DeepSeek reasoner models
            # These models require special handling for reasoning_content field
            if _is_reasoner_model(model):
                result = self._create_message_for_reasoner(messages, tools, model)
                assistant_content = result.get("content")
                if assistant_content:
                    cleaned_content = assistant_content.lstrip("\n")
                    logger.info(f"[📎] {cleaned_content}")
                return result

            provider_system = self.provider_config.pydantic_system if self.provider_config else None
            model_messages = _convert_openai_messages(messages, provider_system)
            tool_definitions = _convert_tools(tools)

            params = ModelRequestParameters(
                function_tools=tool_definitions,
                allow_text_output=True,
            )

            model_identifier, model_object = self._resolve_model(model)
            target_model = model_object or self._default_provider_identifier(model_identifier)

            # Debug: Print model resolution info
            if (
                self.provider_config is not None
                and hasattr(self.provider_config, "name")
                and self.provider_config.name == "proxy"
            ):
                logger.debug(
                    f"Using proxy provider - model: {model}, "
                    f"resolved to: {target_model}, base_url: {self.base_url}"
                )
            try:
                response = model_request_sync(
                    target_model,
                    model_messages,
                    model_request_parameters=params,
                )
                # Check if response is None (which causes the pydantic validation error)
                if response is None:
                    raise ValueError(
                        "Model returned None response - this may indicate an issue "
                        "with the OpenAI API client or provider"
                    )
            except Exception as e:
                # Check if this is the specific pydantic validation error we're seeing
                if "Input should be 'chat.completion'" in str(e) and "literal_error" in str(e):
                    logger.error(f"Model response validation failed: {e}")
                    logger.error("This typically occurs when:")
                    logger.error("1. The API returns an invalid response format")
                    logger.error("2. The response object is None internally")
                    logger.error("3. There's an issue with the OpenAI API client")
                    logger.info("Trying to refresh the provider connection...")
                    # Try to clear any cached connections and retry once
                    import time

                    time.sleep(RETRY_DELAY)
                    response = model_request_sync(
                        target_model,
                        model_messages,
                        model_request_parameters=params,
                    )
                    if response is None:
                        raise ValueError("Model returned None response even after retry")
                else:
                    raise
        finally:
            spinner.stop()

        # Debug: Check what we actually get from pydantic-ai
        if "deepseek-reasoner" in model.lower():
            logger.debug(f"Raw response type: {type(response)}")
            logger.debug(
                f"Response attributes: "
                f"{dir(response) if hasattr(response, '__dir__') else 'No __dir__'}"
            )
            if hasattr(response, "__dict__"):
                logger.debug(f"Response dict keys: {list(response.__dict__.keys())}")
            if hasattr(response, "provider_details"):
                logger.debug(f"Provider details: {response.provider_details}")
            if hasattr(response, "thinking"):
                logger.debug(f"Thinking: {response.thinking}")

        result = _convert_response_to_openai(response)

        # Store reasoning_content for reasoner models so _map_messages can access it
        if "reasoner" in model.lower() and result.get("reasoning_content"):
            # Get the conversation length to find the index for the next message
            if hasattr(response, "__dict__") and hasattr(
                response.__dict__.get("usage", {}), "total_tokens"
            ):
                # Use a hash of the conversation to store reasoning
                conv_hash = hash(str(messages))
                _reasoning_storage[conv_hash] = result["reasoning_content"]

        assistant_content = result.get("content")
        if assistant_content:
            # Remove leading newlines that cause emoji to appear on separate line
            cleaned_content = assistant_content.lstrip("\n")
            logger.info(f"[📎] {cleaned_content}")

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
        aliases: dict[str, str] = {
            "claude-code": "anthropic",
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

        if system in {"anthropic", "claude-code"}:

            def _builder(model_id: str) -> AnthropicModel:
                provider_kwargs: dict[str, Any] = {}
                if self.api_key:
                    provider_kwargs["api_key"] = self.api_key
                if self.provider_config and self.provider_config.base_url:
                    provider_kwargs["base_url"] = self.provider_config.base_url

                # Special handling for Claude Code OAuth
                if system == "claude-code":
                    # Ensure we have a valid OAuth token before creating provider
                    from .oauth.claude_code import ensure_valid_token, load_stored_token

                    # Try to ensure we have a valid token (quietly at provider creation)
                    if not ensure_valid_token(quiet=True):
                        # If we can't get a token, we'll let the request handle it later
                        # but we should still try to load whatever token we have
                        pass

                    # Get the current token for the provider
                    current_token = load_stored_token(check_expiry=False)
                    if current_token:
                        provider_kwargs["api_key"] = current_token

                    # Use custom provider class for Claude Code OAuth
                    provider: AnthropicProvider = ClaudeCodeOAuthProvider(**provider_kwargs)
                else:
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

        # HuggingFace support removed - no one uses it! 📎
        return None


def _convert_openai_messages(
    messages: list[dict[str, Any]],
    provider_system: str | None = None,
) -> list[ModelMessage]:
    """Convert OpenAI-style messages into Pydantic AI message objects."""

    converted: list[ModelMessage] = []
    current_parts: list[Any] = []
    system_instructions = ""

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if role == "system":
            if content is not None:
                system_instructions = _to_text(content)
                # For Claude Code, we don't add SystemPromptPart here - we'll handle it specially
                if provider_system != "claude-code":
                    current_parts.append(SystemPromptPart(content=system_instructions))
        elif role == "user":
            if content is not None:
                user_content = _to_text(content)
                # For Claude Code, prepend system instructions to first user message
                if provider_system == "claude-code" and system_instructions:
                    user_content = f"{system_instructions}\n\n{user_content}"
                    system_instructions = ""  # Clear after using once
                current_parts.append(UserPromptPart(content=user_content))
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

            # Preserve reasoning_content for reasoner models
            reasoning_content = message.get("reasoning_content")
            if reasoning_content:
                # Store reasoning_content as a special text part that we can extract later
                response_parts.append(
                    TextPart(content=f"[REASONING]{reasoning_content}[/REASONING]")
                )

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

    # Get thinking content for DeepSeek reasoner models
    reasoning_content = None
    if hasattr(response, "thinking") and response.thinking:
        reasoning_content = response.thinking

    result: dict[str, Any] = {
        "role": "assistant",
        "content": content,
        "finish_reason": None,
    }

    if tool_calls:
        result["tool_calls"] = tool_calls

    # Preserve reasoning_content for DeepSeek reasoner models
    if reasoning_content is not None:
        result["reasoning_content"] = reasoning_content

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
