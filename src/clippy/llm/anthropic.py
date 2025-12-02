"""Anthropic Claude provider."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .base import BaseProvider
from .errors import APIConnectionError, APITimeoutError, raise_for_status
from .http_client import create_client, post_with_retry

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude API."""

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key
            base_url: Base URL for the API (defaults to Anthropic)
            extra_headers: Additional headers to include in requests
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._extra_headers = extra_headers or {}
        self._client = create_client()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": self.API_VERSION,
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        # Merge extra headers
        headers.update(self._extra_headers)
        return headers

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create message using Anthropic Messages API.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions in OpenAI format
            model: Model identifier
            **kwargs: Additional arguments (max_tokens, temperature, etc.)

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
        url = f"{self.base_url}/v1/messages"

        # Extract system message and convert others
        system_content = None
        filtered_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            else:
                converted = self._convert_message(msg)
                if converted:
                    filtered_messages.append(converted)

        # Merge consecutive messages with the same role (Anthropic requirement)
        filtered_messages = self._merge_consecutive_messages(filtered_messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        if system_content:
            payload["system"] = system_content

        if tools:
            payload["tools"] = self._convert_tools(tools)

        # Add optional parameters
        for key in ("temperature", "top_p", "top_k", "stop_sequences"):
            if key in kwargs:
                payload[key] = kwargs[key]

        logger.debug(f"Anthropic request to {url} with model {model}")

        response = post_with_retry(
            self._client,
            url,
            json=payload,
            headers=self._headers(),
        )
        raise_for_status(response)

        data = response.json()
        return self._normalize_response(data)

    def _convert_message(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        """Convert OpenAI message format to Anthropic format.

        Args:
            msg: Message in OpenAI format

        Returns:
            Message in Anthropic format, or None if should be skipped
        """
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "tool":
            # Tool result format for Anthropic
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": content if isinstance(content, str) else json.dumps(content),
                    }
                ],
            }

        if role == "assistant":
            # Handle assistant messages with tool calls
            content_blocks: list[dict[str, Any]] = []

            if content:
                content_blocks.append({"type": "text", "text": content})

            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    args = func.get("arguments", "{}")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}

                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": func.get("name", ""),
                            "input": args,
                        }
                    )

            if content_blocks:
                return {"role": "assistant", "content": content_blocks}
            return None

        if role == "user":
            return {"role": "user", "content": content}

        return None

    def _merge_consecutive_messages(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge consecutive messages with the same role.

        Anthropic requires alternating user/assistant messages.

        Args:
            messages: List of messages

        Returns:
            Messages with consecutive same-role messages merged
        """
        if not messages:
            return messages

        merged: list[dict[str, Any]] = []
        for msg in messages:
            if merged and merged[-1].get("role") == msg.get("role"):
                # Merge content
                prev_content = merged[-1].get("content", [])
                curr_content = msg.get("content", [])

                if isinstance(prev_content, str):
                    prev_content = [{"type": "text", "text": prev_content}]
                if isinstance(curr_content, str):
                    curr_content = [{"type": "text", "text": curr_content}]

                merged[-1]["content"] = prev_content + curr_content
            else:
                merged.append(msg)

        return merged

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI tool format to Anthropic format.

        Args:
            tools: Tools in OpenAI format

        Returns:
            Tools in Anthropic format
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
                    "input_schema": func.get("parameters", {}),
                }
            )
        return converted

    def _normalize_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize Anthropic response to OpenAI format.

        Args:
            data: Raw API response

        Returns:
            Normalized response dict in OpenAI format
        """
        content_parts = []
        tool_calls = []

        for block in data.get("content", []):
            block_type = block.get("type")
            if block_type == "text":
                content_parts.append(block.get("text", ""))
            elif block_type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    }
                )

        result: dict[str, Any] = {
            "role": "assistant",
            "content": "".join(content_parts) if content_parts else None,
            "finish_reason": self._map_stop_reason(data.get("stop_reason")),
        }

        if tool_calls:
            result["tool_calls"] = tool_calls

        # Include usage if available
        usage = data.get("usage")
        if usage:
            result["usage"] = {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            }

        return result

    def _map_stop_reason(self, stop_reason: str | None) -> str | None:
        """Map Anthropic stop_reason to OpenAI finish_reason.

        Args:
            stop_reason: Anthropic stop reason

        Returns:
            OpenAI-compatible finish reason
        """
        if stop_reason is None:
            return None
        mapping = {
            "end_turn": "stop",
            "stop_sequence": "stop",
            "tool_use": "tool_calls",
            "max_tokens": "length",
        }
        return mapping.get(stop_reason, stop_reason)


class ClaudeCodeOAuthProvider(AnthropicProvider):
    """Anthropic provider with Claude Code OAuth authentication.

    This provider uses OAuth tokens from Claude Code subscription
    and handles automatic re-authentication when tokens expire.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the Claude Code OAuth provider.

        Args:
            api_key: OAuth token (will be refreshed automatically if expired)
            base_url: Base URL (defaults to Anthropic API)
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url or "https://api.anthropic.com",
            extra_headers={"anthropic-beta": "oauth-2025-04-20"},
        )
        self._reauth_in_progress = False

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create message with automatic re-authentication on token expiry."""
        try:
            return super().create_message(messages, tools, model, **kwargs)
        except Exception as exc:
            # Check if this is an authentication error
            if self._is_auth_error(exc) and not self._reauth_in_progress:
                return self._handle_auth_error_and_retry(messages, tools, model, **kwargs)
            raise

    def _is_auth_error(self, exc: Exception) -> bool:
        """Check if an exception is an authentication error."""
        exc_str = str(exc).lower()
        auth_indicators = [
            "401",
            "403",
            "unauthorized",
            "forbidden",
            "token",  # OAuth token-related errors
            "expired",
            "authentication failed",
        ]
        return any(indicator in exc_str for indicator in auth_indicators)

    def _handle_auth_error_and_retry(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Handle authentication error by re-authenticating and retrying."""
        self._reauth_in_progress = True

        try:
            # Import here to avoid circular imports
            from clippy.oauth.claude_code import ensure_valid_token, load_stored_token

            logger.info("Claude Code token expired - attempting automatic re-authentication...")

            if ensure_valid_token(quiet=False, force_reauth=True):
                new_token = load_stored_token(check_expiry=False)
                if new_token:
                    self.api_key = new_token
                    logger.info("Re-authentication successful - retrying request...")
                    return super().create_message(messages, tools, model, **kwargs)

            logger.error("Automatic re-authentication failed")
            raise Exception("Claude Code OAuth re-authentication failed")

        finally:
            self._reauth_in_progress = False
