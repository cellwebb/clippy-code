"""LLM Providers package.

This package provides a unified interface for multiple LLM providers
using direct HTTP calls via httpx, without depending on provider-specific SDKs.

Supported providers:
- OpenAI (Chat Completions API and Responses API)
- Anthropic (Claude)
- Google (Gemini)
- Any OpenAI-compatible API (Ollama, Together, Groq, etc.)
"""

from __future__ import annotations

from typing import Any

from .anthropic import AnthropicProvider, ClaudeCodeOAuthProvider
from .base import BaseProvider, LLMResponse, ToolCall
from .errors import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    LLMError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from .google import GoogleProvider
from .openai import OpenAIProvider

__all__ = [
    # Base types
    "BaseProvider",
    "LLMResponse",
    "ToolCall",
    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "ClaudeCodeOAuthProvider",
    "GoogleProvider",
    # Errors
    "LLMError",
    "AuthenticationError",
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "BadRequestError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "InternalServerError",
    # Factory
    "create_provider",
]


def create_provider(
    provider_type: str,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> BaseProvider:
    """Factory function to create appropriate provider.

    Args:
        provider_type: Type of provider ("openai", "anthropic", "google", etc.)
        api_key: API key for the provider
        base_url: Optional base URL override
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured provider instance

    Examples:
        >>> provider = create_provider("openai", api_key="sk-...")
        >>> provider = create_provider("anthropic", api_key="sk-ant-...")
        >>> provider = create_provider("google", api_key="...")
        >>> provider = create_provider("ollama", base_url="http://localhost:11434/v1")
    """
    provider_type_lower = provider_type.lower()

    # Map provider types to classes
    if provider_type_lower in ("anthropic",):
        return AnthropicProvider(api_key=api_key, base_url=base_url, **kwargs)

    if provider_type_lower in ("claude-code",):
        # Special handling for Claude Code OAuth
        return ClaudeCodeOAuthProvider(api_key=api_key, base_url=base_url)

    if provider_type_lower in ("google", "google-gla", "gemini"):
        return GoogleProvider(api_key=api_key, base_url=base_url, **kwargs)

    # Default to OpenAI provider (works with any OpenAI-compatible API)
    return OpenAIProvider(api_key=api_key, base_url=base_url, **kwargs)
