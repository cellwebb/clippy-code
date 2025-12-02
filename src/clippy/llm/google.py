"""Google Gemini provider."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .base import BaseProvider
from .errors import APIConnectionError, APITimeoutError, raise_for_status
from .http_client import create_client, post_with_retry

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    """Provider for Google Gemini API."""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the Google Gemini provider.

        Args:
            api_key: Google API key
            base_url: Base URL for the API (defaults to Gemini)
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._client = create_client()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gemini-1.5-pro",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create message using Gemini API.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions in OpenAI format
            model: Model identifier
            **kwargs: Additional arguments

        Returns:
            Response dict in OpenAI format
        """
        try:
            return self._create_message_internal(messages, tools, model, **kwargs)
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to {self.base_url}: {e}") from e
        except httpx.ReadTimeout as e:
            raise APITimeoutError(f"Request timed out: {e}") from e

    def _create_message_internal(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Internal implementation of create_message."""
        # Gemini uses model name in URL
        url = f"{self.base_url}/models/{model}:generateContent"
        if self.api_key:
            url += f"?key={self.api_key}"

        # Convert to Gemini format
        contents, system_instruction = self._convert_messages(messages)

        payload: dict[str, Any] = {
            "contents": contents,
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        if tools:
            payload["tools"] = [{"functionDeclarations": self._convert_tools(tools)}]

        # Add generation config if provided
        generation_config: dict[str, Any] = {}
        if "temperature" in kwargs:
            generation_config["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            generation_config["maxOutputTokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            generation_config["topP"] = kwargs["top_p"]
        if "top_k" in kwargs:
            generation_config["topK"] = kwargs["top_k"]
        if generation_config:
            payload["generationConfig"] = generation_config

        logger.debug(f"Gemini request to {url} with model {model}")

        response = post_with_retry(
            self._client,
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        raise_for_status(response)

        data = response.json()
        return self._normalize_response(data)

    def _convert_messages(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Convert OpenAI messages to Gemini format.

        Args:
            messages: Messages in OpenAI format

        Returns:
            Tuple of (contents, system_instruction)
        """
        system_instruction = None
        contents: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append(
                    {
                        "role": "user",
                        "parts": [{"text": content}],
                    }
                )
            elif role == "assistant":
                parts: list[dict[str, Any]] = []

                if content:
                    parts.append({"text": content})

                # Handle tool calls
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        args = func.get("arguments", "{}")
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except json.JSONDecodeError:
                                args = {}

                        parts.append(
                            {
                                "functionCall": {
                                    "name": func.get("name", ""),
                                    "args": args,
                                }
                            }
                        )

                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                # Tool result in Gemini format
                tool_result = msg.get("content", "")
                if isinstance(tool_result, str):
                    try:
                        tool_result = json.loads(tool_result)
                    except json.JSONDecodeError:
                        tool_result = {"result": tool_result}

                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": msg.get("name", ""),
                                    "response": tool_result,
                                }
                            }
                        ],
                    }
                )

        return contents, system_instruction

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI tools to Gemini functionDeclarations.

        Args:
            tools: Tools in OpenAI format

        Returns:
            Tools in Gemini format
        """
        converted = []
        for tool in tools:
            if tool.get("type") != "function":
                continue
            func = tool.get("function", {})
            converted.append(
                {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                }
            )
        return converted

    def _normalize_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize Gemini response to OpenAI format.

        Args:
            data: Raw API response

        Returns:
            Normalized response dict in OpenAI format
        """
        # Handle error responses
        if "error" in data:
            error = data["error"]
            raise Exception(f"Gemini API error: {error.get('message', str(error))}")

        candidate = data.get("candidates", [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []

        for part in parts:
            if "text" in part:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                # Generate a unique-ish ID for the tool call
                tool_call_id = f"call_{fc.get('name', 'unknown')}_{len(tool_calls)}"
                tool_calls.append(
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": fc.get("name", ""),
                            "arguments": json.dumps(fc.get("args", {})),
                        },
                    }
                )

        result: dict[str, Any] = {
            "role": "assistant",
            "content": "".join(text_parts) if text_parts else None,
            "finish_reason": self._map_finish_reason(candidate.get("finishReason")),
        }

        if tool_calls:
            result["tool_calls"] = tool_calls

        # Include usage if available
        usage_metadata = data.get("usageMetadata")
        if usage_metadata:
            result["usage"] = {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0),
            }

        return result

    def _map_finish_reason(self, finish_reason: str | None) -> str | None:
        """Map Gemini finishReason to OpenAI finish_reason.

        Args:
            finish_reason: Gemini finish reason

        Returns:
            OpenAI-compatible finish reason
        """
        if finish_reason is None:
            return None
        mapping = {
            "STOP": "stop",
            "MAX_TOKENS": "length",
            "SAFETY": "content_filter",
            "RECITATION": "content_filter",
            "OTHER": "stop",
        }
        return mapping.get(finish_reason, finish_reason.lower())
