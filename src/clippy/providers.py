"""OpenAI-compatible LLM provider."""

import logging
import os
import sys
import threading
import time
from typing import Any, cast

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class Spinner:
    """A simple terminal spinner for indicating loading status."""
    
    def __init__(self, message: str = "Processing", enabled: bool = True):
        self.message = message
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self.thread = None
        self.enabled = enabled

    def _spin(self):
        """Internal method to run the spinner animation."""
        i = 0
        while self.running:
            sys.stdout.write(f"\r[📎] {self.message} {self.spinner_chars[i % len(self.spinner_chars)]}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        """Start the spinner."""
        if not self.enabled or self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        self.running = False
        if self.thread:
            self.thread.join()
        
        # Clear the spinner line if enabled
        if self.enabled:
            sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")
            sys.stdout.flush()


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

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _create_completion_with_retry(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        **kwargs,
    ):
        """
        Internal method to create completion with retry logic.

        Retries up to 3 times with exponential backoff for:
        - Network errors
        - Rate limit errors
        - Server errors (5xx)
        """
        try:
            from openai import (
                APIConnectionError,
                APITimeoutError,
                InternalServerError,
                RateLimitError,
            )

            # Call OpenAI API with streaming enabled
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools if tools else None,
                stream=True,
                **kwargs,
            )
        except (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError) as e:
            logger.warning(f"API error (will retry): {type(e).__name__}: {e}")
            raise
        except Exception as e:
            # For other errors, log and re-raise without retry
            logger.error(f"Unexpected API error: {type(e).__name__}: {e}")
            raise

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-4o",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a chat completion using OpenAI format with streaming.

        Args:
            messages: OpenAI-format messages (includes system message)
            tools: OpenAI-format tool definitions
            model: Model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with keys: role, content, tool_calls, finish_reason

        Raises:
            Various OpenAI exceptions if all retries fail
        """
        # Check if we're in document mode by looking for Textual's console redirection
        # In document mode, stdout is redirected to a StringIO buffer
        in_document_mode = hasattr(sys.stdout, '_original_stdstream_copy') or not sys.stdout.isatty()
        
        # Create and start spinner to indicate processing (disabled in document mode)
        spinner = Spinner("Thinking", enabled=not in_document_mode)
        spinner.start()
        
        try:
            # Call with retry logic
            stream = self._create_completion_with_retry(
                model=model,
                messages=messages,
                tools=tools,
                **kwargs,
            )
        finally:
            # Stop spinner before displaying results
            spinner.stop()

        # Accumulate streaming response
        full_content = ""
        tool_calls_dict: dict[int, dict[str, Any]] = {}  # Track tool calls by index
        role = "assistant"
        finish_reason = None
        content_started = False  # Track if we've started printing content

        for chunk in stream:
            if not chunk.choices:  # type: ignore
                continue

            choice = chunk.choices[0]  # type: ignore
            delta = choice.delta

            # Update role if present
            if delta.role:
                role = delta.role

            # Stream text content to user in real-time
            if delta.content:
                # Print prefix before first content chunk
                if not content_started:
                    print("\n[📎] ", end="", flush=True)
                    content_started = True
                print(delta.content, end="", flush=True)
                full_content += delta.content

            # Accumulate tool calls
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_dict:
                        tool_calls_dict[idx] = {
                            "id": tc_delta.id or "",
                            "type": tc_delta.type or "function",
                            "function": {"name": "", "arguments": ""},
                        }

                    # Update tool call fields as they arrive
                    if tc_delta.id:
                        tool_calls_dict[idx]["id"] = tc_delta.id
                    if tc_delta.type:
                        tool_calls_dict[idx]["type"] = tc_delta.type
                    if tc_delta.function:
                        if tc_delta.function.name:
                            cast(dict[str, str], tool_calls_dict[idx]["function"])["name"] = (
                                tc_delta.function.name
                            )
                        if tc_delta.function.arguments:
                            cast(dict[str, str], tool_calls_dict[idx]["function"])["arguments"] += (
                                tc_delta.function.arguments
                            )

            # Capture finish reason
            if choice.finish_reason:
                finish_reason = choice.finish_reason

        # Print newline after streaming content (if any content was printed)
        if full_content:
            print()

        # Convert to simple dict format
        result = {
            "role": role,
            "content": full_content if full_content else None,
            "finish_reason": finish_reason,
        }

        # Add tool calls if present (sorted by index)
        if tool_calls_dict:
            result["tool_calls"] = [tool_calls_dict[i] for i in sorted(tool_calls_dict.keys())]

        return result

    def get_default_model(self) -> str:
        """Get the default model."""
        # Check for model in environment first
        return os.getenv("CLIPPY_MODEL", "gpt-5")