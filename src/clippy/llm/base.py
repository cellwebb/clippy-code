"""Base provider classes and response types."""

from __future__ import annotations

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
        model: str = "gpt-4o",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a chat completion.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions in OpenAI format
            model: Model identifier
            **kwargs: Additional provider-specific arguments

        Returns:
            Response dict in OpenAI format for compatibility
        """
        raise NotImplementedError

    def close(self) -> None:
        """Close any open connections."""
        pass
