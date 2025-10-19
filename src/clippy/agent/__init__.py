"""Agent system for clippy-code - modular AI coding assistant."""

from .conversation import (
    compact_conversation,
    create_system_prompt,
    get_token_count,
)
from .core import ClippyAgent, InterruptedExceptionError
from .errors import format_api_error
from .tool_handler import add_tool_result, ask_approval, display_tool_request, handle_tool_use
from .utils import generate_preview_diff, validate_python_syntax

__all__ = [
    # Main agent class
    "ClippyAgent",
    # Exceptions
    "InterruptedExceptionError",
    # Conversation management
    "create_system_prompt",
    "get_token_count",
    "compact_conversation",
    # Tool handling
    "handle_tool_use",
    "ask_approval",
    "add_tool_result",
    "display_tool_request",
    # Error handling
    "format_api_error",
    # Utilities
    "generate_preview_diff",
    "validate_python_syntax",
]
