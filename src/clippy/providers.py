"""LLM provider wrapper - delegates to providers package.

This module provides backwards compatibility while using the new
httpx-based provider implementations under the hood.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from .llm import (
    ClaudeCodeOAuthProvider,
    create_provider,
)
from .llm.base import BaseProvider
from .llm.errors import LLMError

if TYPE_CHECKING:
    from .models import ProviderConfig

logger = logging.getLogger(__name__)

# Provider constants
SPINNER_SLEEP_INTERVAL = 0.1  # seconds


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


class LLMProvider:
    """Adapter that routes to appropriate provider implementation.

    This class maintains backwards compatibility with existing code
    while using the new httpx-based providers under the hood.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        provider_config: ProviderConfig | None = None,
        **_: Any,
    ) -> None:
        """Initialize the LLM provider.

        Args:
            api_key: API key for the provider
            base_url: Base URL for the API
            provider_config: Optional provider configuration
        """
        self.api_key = api_key
        self.base_url = base_url
        self.provider_config = provider_config

        # Determine provider type from config
        provider_type = "openai"
        effective_base_url = base_url

        if provider_config:
            if provider_config.pydantic_system:
                provider_type = provider_config.pydantic_system
            if provider_config.base_url and not base_url:
                effective_base_url = provider_config.base_url

        # Handle Claude Code OAuth provider
        self._provider: BaseProvider
        if provider_type == "claude-code":
            self._provider = self._create_claude_code_provider(effective_base_url)
        else:
            self._provider = create_provider(
                provider_type=provider_type,
                api_key=api_key,
                base_url=effective_base_url,
            )

    def _create_claude_code_provider(self, base_url: str | None) -> ClaudeCodeOAuthProvider:
        """Create Claude Code OAuth provider with token loading.

        Args:
            base_url: Optional base URL override

        Returns:
            Configured ClaudeCodeOAuthProvider
        """
        # Try to load OAuth token
        try:
            from .oauth.claude_code import ensure_valid_token, load_stored_token

            # Ensure we have a valid token
            if ensure_valid_token(quiet=True):
                token = load_stored_token(check_expiry=False)
                if token:
                    return ClaudeCodeOAuthProvider(api_key=token, base_url=base_url)
        except ImportError:
            logger.warning("Claude Code OAuth module not available")
        except (OSError, ValueError, RuntimeError) as e:
            # Handle token loading errors: file I/O, invalid token format, or runtime issues
            logger.warning(f"Failed to load Claude Code OAuth token ({type(e).__name__}): {e}")

        # Fall back to provider without token (will fail on first request)
        return ClaudeCodeOAuthProvider(api_key=self.api_key, base_url=base_url)

    def stream_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-5.1",
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream a chat completion using appropriate provider.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            model: Model identifier
            **kwargs: Additional arguments

        Yields:
            Streaming response chunks in OpenAI format
        """
        spinner = Spinner("Thinking", enabled=sys.stdout.isatty())
        spinner.start()

        try:
            yield from self._provider.stream_message(messages, tools, model, **kwargs)
        except LLMError:
            # Re-raise LLM errors directly
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.exception(f"Unexpected error in stream_message: {e}")
            raise
        finally:
            spinner.stop()
