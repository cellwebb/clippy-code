"""OpenAI-compatible LLM provider."""

import os
from typing import Any


class LLMProvider:
    """OpenAI-compatible LLM provider.

    Supports OpenAI and any OpenAI-compatible API (Cerebras, Together AI,
    Azure OpenAI, Ollama, llama.cpp, vLLM, Groq, etc.)
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None, **kwargs):
        """
        Initialize OpenAI-compatible provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for API (e.g., https://api.cerebras.ai/v1 for Cerebras)
            **kwargs: Additional arguments passed to OpenAI client
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install it with: pip install openai")

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        # Add any additional kwargs
        client_kwargs.update(kwargs)

        self.client = OpenAI(**client_kwargs)

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
        model: str = "gpt-4o",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a chat completion using OpenAI format.

        Args:
            messages: OpenAI-format messages (includes system message)
            tools: OpenAI-format tool definitions
            max_tokens: Maximum tokens for response
            model: Model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with keys: role, content, tool_calls, finish_reason
        """
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            tools=tools if tools else None,
            **kwargs,
        )

        # Extract message from response
        message = response.choices[0].message

        # Convert to simple dict format
        result = {
            "role": message.role,
            "content": message.content,
            "finish_reason": response.choices[0].finish_reason,
        }

        # Add tool calls if present
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,  # Already JSON string
                    },
                }
                for tc in message.tool_calls
            ]

        return result

    def get_default_model(self) -> str:
        """Get the default model."""
        # Check for model in environment first
        return os.getenv("CLIPPY_MODEL", "gpt-4o")
