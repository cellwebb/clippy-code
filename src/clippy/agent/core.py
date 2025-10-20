"""AI agent with OpenAI-compatible LLM support."""

import logging
from typing import Any

from rich.console import Console

from ..executor import ActionExecutor
from ..permissions import PermissionManager
from ..providers import LLMProvider
from .conversation import (
    compact_conversation,
    create_system_prompt,
    get_token_count,
)
from .loop import run_agent_loop
from .subagent_manager import SubAgentManager

logger = logging.getLogger(__name__)


class InterruptedExceptionError(Exception):
    """Exception raised when user interrupts execution."""

    pass


class ClippyAgent:
    """AI coding assistant powered by OpenAI-compatible LLMs - here to help you with
    that paperclip!"""

    def __init__(
        self,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        approval_callback: Any = None,
        mcp_manager: Any = None,
        max_concurrent_subagents: int = 3,
    ) -> None:
        """
        Initialize the ClippyAgent.

        Args:
            permission_manager: Permission manager instance
            executor: Action executor instance
            api_key: API key for OpenAI-compatible provider
            model: Model identifier to use (required)
            base_url: Base URL for OpenAI-compatible API (for alternate providers)
            approval_callback: Optional callback function for approval requests
                             (used in document mode). Should accept (tool_name, tool_input)
                             and return bool (True for approve, False for deny).
                             Can raise InterruptedExceptionError to stop execution.
            mcp_manager: Optional MCP manager instance for tool discovery
            max_concurrent_subagents: Maximum number of concurrent subagents
        """
        self.permission_manager = permission_manager
        self.executor = executor

        # Store credentials for provider recreation
        self.api_key = api_key
        self.base_url = base_url

        # Create provider (OpenAI-compatible)
        self.provider = LLMProvider(api_key=api_key, base_url=base_url)

        # Model is now required - callers must resolve the default model
        if not model:
            raise ValueError(
                "Model must be specified. Use get_default_model_config() to get the default."
            )
        self.model = model

        self.console = Console()
        self.conversation_history: list[dict[str, Any]] = []
        self.interrupted = False
        self.approval_callback = approval_callback
        self.mcp_manager = mcp_manager

        # Initialize subagent manager
        self.subagent_manager = SubAgentManager(
            parent_agent=self,
            permission_manager=permission_manager,
            executor=executor,
            max_concurrent=max_concurrent_subagents,
        )

    def run(self, user_message: str, auto_approve_all: bool = False) -> str:
        """
        Run the agent with a user message.

        Args:
            user_message: The user's request
            auto_approve_all: If True, auto-approve all actions (dangerous!)

        Returns:
            The final response from the agent
        """
        self.interrupted = False

        # Initialize with system message if first run
        if not self.conversation_history:
            self.conversation_history.append({"role": "system", "content": create_system_prompt()})

        # Add user message
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = self._run_agent_loop(auto_approve_all)
            return response
        except InterruptedExceptionError:
            return "Execution interrupted by user."

    def _run_agent_loop(self, auto_approve_all: bool = False) -> str:
        """Run the main agent loop."""
        return run_agent_loop(
            conversation_history=self.conversation_history,
            provider=self.provider,
            model=self.model,
            permission_manager=self.permission_manager,
            executor=self.executor,
            console=self.console,
            auto_approve_all=auto_approve_all,
            approval_callback=self.approval_callback,
            check_interrupted=lambda: self.interrupted,
            mcp_manager=self.mcp_manager,
            parent_agent=self,  # Pass self for subagent delegation
        )

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
        self.interrupted = False

    def switch_model(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> tuple[bool, str]:
        """
        Switch to a different model or provider.

        Args:
            model: New model identifier (if None, keeps current)
            base_url: New base URL (if None, keeps current)
            api_key: New API key (if None, keeps current)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Update base_url if provided
            new_base_url = base_url if base_url is not None else self.base_url

            # Update model if provided
            new_model = model if model is not None else self.model

            # Update API key if provided
            new_api_key = api_key if api_key is not None else self.api_key

            # Create new provider with updated settings
            self.provider = LLMProvider(api_key=new_api_key, base_url=new_base_url)

            # Update instance variables
            self.base_url = new_base_url
            self.model = new_model
            self.api_key = new_api_key

            # Build success message
            provider_info = f" ({new_base_url})" if new_base_url else " (OpenAI)"
            message = f"Switched to model: {new_model}{provider_info}"

            return True, message

        except Exception as e:
            return False, f"Failed to switch model: {e}"

    def get_token_count(self) -> dict[str, Any]:
        """
        Get token usage statistics for the current conversation.

        Returns:
            Dictionary with token usage information including:
            - total_tokens: Total tokens in conversation history
            - usage_percent: Percentage of typical context window used (estimate)
            - message_count: Number of messages in history
            - system_tokens: Tokens from system messages
            - system_messages: Number of system messages
            - user_tokens: Tokens from user messages
            - user_messages: Number of user messages
            - assistant_tokens: Tokens from assistant messages
            - assistant_messages: Number of assistant messages
            - tool_tokens: Tokens from tool messages
            - tool_messages: Number of tool messages
        """
        return get_token_count(self.conversation_history, self.model, self.base_url)

    def compact_conversation(self, keep_recent: int = 4) -> tuple[bool, str, dict[str, Any]]:
        """
        Compact the conversation history by summarizing older messages.

        This helps manage context window limits by condensing older conversation
        history into a summary while keeping recent messages intact.

        Args:
            keep_recent: Number of recent messages to keep intact (default: 4)

        Returns:
            Tuple of (success: bool, message: str, stats: dict)
            Stats include before/after token counts and reduction percentage
        """
        success, message, stats, new_history = compact_conversation(
            self.conversation_history, self.provider, self.model, keep_recent
        )

        # Update conversation history if successful
        if success and new_history:
            self.conversation_history = new_history

        return success, message, stats
