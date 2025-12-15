"""Base provider classes and response types."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: str  # JSON string


@dataclass
class LLMResponse:
    """Standardized response from any provider."""

    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    reasoning_content: str | None = None  # For DeepSeek reasoner
    usage: dict[str, int] | None = None


class BaseProvider:
    """Abstract base for all LLM providers."""

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
            tools: Optional list of tool definitions in OpenAI format
            model: Model identifier
            **kwargs: Additional provider-specific arguments

        Returns:
            Complete response in OpenAI format
        """
        # Default implementation: iterate over streaming response and return final result
        response = None
        for chunk in self.stream_message(messages, tools, model, **kwargs):
            response = chunk
        if response is None:
            raise RuntimeError("No response received from streaming")
        return response

    def stream_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-5-mini",
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream a chat completion.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions in OpenAI format
            model: Model identifier
            **kwargs: Additional provider-specific arguments

        Yields:
            Streaming response chunks in OpenAI format
        """
        raise NotImplementedError

    def close(self) -> None:
        """Close any open connections."""
        pass
