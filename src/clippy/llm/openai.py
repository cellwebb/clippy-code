"""OpenAI provider supporting Chat Completions and Responses APIs."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import httpx

from .base import BaseProvider
from .errors import APIConnectionError, APITimeoutError, raise_for_status
from .http_client import create_client, post_with_retry, stream_with_retry
from .utils import _is_reasoner_model

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI and OpenAI-compatible APIs.

    Supports both Chat Completions API (/v1/chat/completions) and
    Responses API (/v1/responses) for codex models.
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key (or compatible provider key)
            base_url: Base URL for the API (defaults to OpenAI)
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._client = create_client()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _should_use_responses_api(self, model: str) -> bool:
        """Determine if model should use Responses API.

        Models with 'codex' in the name use the Responses API.
        """
        model_lower = model.lower()
        return "codex" in model_lower

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-5-mini",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a chat completion without streaming.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            model: Model identifier
            **kwargs: Additional arguments

        Returns:
            Complete response in OpenAI format
        """
        try:
            if self._should_use_responses_api(model):
                # For codex models, use the Responses API
                return self._create_responses(messages, tools, model, **kwargs)
            else:
                # For chat models, use the Chat Completions API with stream=False
                return self._create_chat_completion(messages, tools, model, **kwargs)
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to {self.base_url}: {e}") from e
        except httpx.ReadTimeout as e:
            raise APITimeoutError(f"Request timed out: {e}") from e

    def stream_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-5-mini",
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream completion using appropriate API.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            model: Model identifier
            **kwargs: Additional arguments

        Yields:
            Streaming response chunks in OpenAI format
        """
        try:
            if self._should_use_responses_api(model):
                # For codex models, non-streaming is the only option
                response = self._create_responses(messages, tools, model, **kwargs)
                yield response
            else:
                yield from self._stream_chat_completion(messages, tools, model, **kwargs)
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to {self.base_url}: {e}") from e
        except httpx.ReadTimeout as e:
            raise APITimeoutError(f"Request timed out: {e}") from e

    def _prepare_messages_for_chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
    ) -> list[dict[str, Any]]:
        """Prepare messages for Chat Completions API.

        Handles reasoning_content for DeepSeek reasoner models.
        """
        if not _is_reasoner_model(model):
            return messages

        # For reasoner models, include reasoning_content in the current turn
        prepared = []
        last_user_idx = -1

        # Find the last user message index
        for i, msg in enumerate(messages):
            if msg.get("role") == "user":
                last_user_idx = i

        for i, msg in enumerate(messages):
            prepared_msg: dict[str, Any] = {
                "role": msg.get("role"),
            }

            if msg.get("content") is not None:
                prepared_msg["content"] = msg["content"]

            # Include tool_calls if present
            if msg.get("tool_calls"):
                prepared_msg["tool_calls"] = msg["tool_calls"]

            # Include reasoning_content only for messages after the last user message
            if (
                i > last_user_idx
                and msg.get("role") == "assistant"
                and msg.get("reasoning_content")
            ):
                prepared_msg["reasoning_content"] = msg["reasoning_content"]

            # Include tool_call_id for tool messages
            if msg.get("role") == "tool":
                prepared_msg["tool_call_id"] = msg.get("tool_call_id", "")

            prepared.append(prepared_msg)

        return prepared

    def _create_responses(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call Responses API for codex models.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            model: Model identifier
            **kwargs: Additional arguments

        Returns:
            Response dict in OpenAI format (normalized)
        """
        url = f"{self.base_url}/responses"

        # Convert messages to Responses API format
        instructions, input_content = self._convert_messages_to_responses_format(messages)

        payload: dict[str, Any] = {
            "model": model,
            "input": input_content,
        }

        if instructions:
            payload["instructions"] = instructions

        if tools:
            # Convert tool schema from Chat Completions to Responses format
            payload["tools"] = self._convert_tools_to_responses_format(tools)

        logger.debug(f"Responses API request to {url} with model {model}")

        response = post_with_retry(
            self._client,
            url,
            json=payload,
            headers=self._headers(),
        )
        raise_for_status(response)

        data = response.json()
        return self._normalize_responses_response(data)

    def _convert_messages_to_responses_format(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[str | None, str | list[dict[str, Any]]]:
        """Convert Chat Completions messages to Responses API format.

        Args:
            messages: Messages in OpenAI Chat Completions format

        Returns:
            Tuple of (instructions, input) for Responses API
        """
        instructions = None
        input_parts: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "system":
                instructions = content
            elif role == "user":
                input_parts.append(
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": content}],
                    }
                )
            elif role == "assistant":
                assistant_content: list[dict[str, Any]] = []
                if content:
                    assistant_content.append({"type": "output_text", "text": content})

                # Handle tool calls
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        assistant_content.append(
                            {
                                "type": "function_call",
                                "call_id": tc.get("id", ""),
                                "name": func.get("name", ""),
                                "arguments": func.get("arguments", "{}"),
                            }
                        )

                if assistant_content:
                    input_parts.append(
                        {
                            "role": "assistant",
                            "content": assistant_content,
                        }
                    )
            elif role == "tool":
                # Tool results in Responses API format
                input_parts.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "function_call_output",
                                "call_id": msg.get("tool_call_id", ""),
                                "output": content,
                            }
                        ],
                    }
                )

        # If only one simple user message, return as string for simplicity
        if (
            len(input_parts) == 1
            and input_parts[0].get("role") == "user"
            and len(input_parts[0].get("content", [])) == 1
            and input_parts[0]["content"][0].get("type") == "input_text"
        ):
            return instructions, input_parts[0]["content"][0]["text"]

        return instructions, input_parts

    def _convert_tools_to_responses_format(
        self,
        tools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert Chat Completions tool schema to Responses API format.

        The Responses API uses a flat structure instead of nested 'function' object.

        Args:
            tools: Tools in Chat Completions format

        Returns:
            Tools in Responses API format
        """
        converted = []
        for tool in tools:
            if tool.get("type") != "function":
                continue

            func = tool.get("function", {})
            # Responses API uses flat structure (no nested "function" key)
            converted.append(
                {
                    "type": "function",
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                }
            )

        return converted

    def _normalize_chat_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize Chat Completions response to standard format.

        Args:
            data: Raw API response

        Returns:
            Normalized response dict
        """
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        result: dict[str, Any] = {
            "role": "assistant",
            "content": message.get("content"),
            "finish_reason": choice.get("finish_reason"),
        }

        if message.get("tool_calls"):
            result["tool_calls"] = message["tool_calls"]

        # DeepSeek reasoner support
        if message.get("reasoning_content"):
            result["reasoning_content"] = message["reasoning_content"]

        # Include usage if available
        if data.get("usage"):
            result["usage"] = data["usage"]

        return result

    def _create_chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create Chat Completions API response without streaming.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            model: Model identifier
            **kwargs: Additional arguments

        Returns:
            Complete response in OpenAI format
        """
        url = f"{self.base_url}/chat/completions"

        # Build payload for non-streaming
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._prepare_messages_for_chat(messages, model),
            "stream": False,  # Disable streaming for create_message
        }

        if tools:
            payload["tools"] = tools

        # Add any extra kwargs (e.g., temperature, max_tokens)
        for key in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
            if key in kwargs:
                payload[key] = kwargs[key]

        logger.debug(f"Chat completions request to {url} with model {model}")

        response = post_with_retry(
            self._client,
            url,
            json=payload,
            headers=self._headers(),
        )
        raise_for_status(response)

        data = response.json()
        return self._normalize_chat_response(data)

    def _stream_chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream Chat Completions API response.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            model: Model identifier
            **kwargs: Additional arguments

        Yields:
            Streaming response chunks in OpenAI format
        """
        url = f"{self.base_url}/chat/completions"

        # Build payload for streaming
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._prepare_messages_for_chat(messages, model),
            "stream": True,  # Enable streaming
        }

        if tools:
            payload["tools"] = tools

        # Add any extra kwargs (e.g., temperature, max_tokens)
        for key in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
            if key in kwargs:
                payload[key] = kwargs[key]

        logger.debug(f"Streaming chat completions request to {url} with model {model}")

        # Track accumulated content and tool calls
        accumulated_content = ""
        accumulated_tool_calls: list[dict[str, Any]] = []
        current_tool_call: dict[str, Any] | None = None

        try:
            for chunk in stream_with_retry(self._client, url, payload, self._headers()):
                # Parse OpenAI streaming format
                choices = chunk.get("choices", [])
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                finish_reason = choices[0].get("finish_reason")

                # Handle content streaming
                if "content" in delta and delta["content"] is not None:
                    accumulated_content += delta["content"]
                    yield {
                        "role": "assistant",
                        "content": delta["content"],
                        "delta": True,
                    }

                # Handle tool call streaming
                if "tool_calls" in delta:
                    for tool_call_delta in delta["tool_calls"]:
                        index = tool_call_delta.get("index")

                        # Ensure we have the right tool call slot
                        while len(accumulated_tool_calls) <= index:
                            accumulated_tool_calls.append(
                                {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            )

                        current_tool_call = accumulated_tool_calls[index]

                        # Update tool call ID
                        if "id" in tool_call_delta:
                            current_tool_call["id"] = tool_call_delta["id"]

                        # Update function name
                        func_name = tool_call_delta.get("function", {}).get("name")
                        if func_name:
                            current_tool_call["function"]["name"] += func_name

                        # Update function arguments
                        func_args = tool_call_delta.get("function", {}).get("arguments")
                        if func_args:
                            current_tool_call["function"]["arguments"] += func_args

                # Handle finish
                if finish_reason:
                    tool_calls_result = accumulated_tool_calls if accumulated_tool_calls else None
                    if accumulated_content:
                        yield {
                            "role": "assistant",
                            "content": accumulated_content,
                            "tool_calls": tool_calls_result,
                            "finish_reason": finish_reason,
                            "delta": False,
                        }
                    else:
                        yield {
                            "role": "assistant",
                            "tool_calls": tool_calls_result,
                            "finish_reason": finish_reason,
                            "delta": False,
                        }
                    return

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            raise

    def _normalize_responses_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize Responses API response to standard format.

        Args:
            data: Raw API response

        Returns:
            Normalized response dict in Chat Completions format
        """
        # Responses API can return output_text directly or output array
        content = data.get("output_text")

        # Handle structured output
        output = data.get("output", [])
        tool_calls = []

        if isinstance(output, list):
            text_parts = []
            for item in output:
                item_type = item.get("type")
                if item_type == "message":
                    # Extract text from message content
                    for content_item in item.get("content", []):
                        if content_item.get("type") == "output_text":
                            text_parts.append(content_item.get("text", ""))
                elif item_type == "function_call":
                    tool_calls.append(
                        {
                            "id": item.get("call_id", ""),
                            "type": "function",
                            "function": {
                                "name": item.get("name", ""),
                                "arguments": item.get("arguments", "{}"),
                            },
                        }
                    )

            if text_parts and not content:
                content = "".join(text_parts)

        result: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "finish_reason": data.get("status"),
        }

        if tool_calls:
            result["tool_calls"] = tool_calls

        # Include usage if available
        if data.get("usage"):
            result["usage"] = data["usage"]

        return result
