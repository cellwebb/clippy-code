"""AI agent with OpenAI-compatible LLM support."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console

from ..executor import ActionExecutor
from ..models import ProviderConfig
from ..permissions import PermissionManager
from ..providers import LLMProvider
from .conversation import (
    compact_conversation,
    create_system_prompt,
    get_token_count,
)
from .exceptions import InterruptedExceptionError
from .loop import AgentLoopConfig, run_agent_loop
from .subagent_manager import SubAgentManager

if TYPE_CHECKING:
    from ..mcp.manager import Manager

logger = logging.getLogger(__name__)

# Type alias for approval callback
ApprovalCallback = Callable[[str, dict[str, Any], str | None], bool]

# Re-export for backward compatibility
__all__ = ["ClippyAgent", "InterruptedExceptionError", "ApprovalCallback"]


class ClippyAgent:
    """AI coding assistant powered by OpenAI-compatible LLMs.

    The primary agent interface that manages conversation state, tool execution,
    and interactions with LLM providers. Supports model switching, conversation
    persistence, and subagent delegation for complex tasks.

    Attributes:
        permission_manager: Permission manager controlling tool access
        executor: Action executor for running tools
        model: Current LLM model identifier
        api_key: API key for the current provider
        base_url: Base URL for OpenAI-compatible API
        provider_config: Provider-specific configuration
        console: Rich console instance for output
        conversation_history: List of conversation messages in OpenAI format
        interrupted: Flag indicating if execution was interrupted
        approval_callback: Optional callback for approval requests
        mcp_manager: Optional MCP manager for external tools
        yolo_mode: Flag for auto-approving all actions
        subagent_manager: Manager for subagent operations
        conversations_dir: Directory for saving conversations
    """

    def __init__(
        self,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        approval_callback: ApprovalCallback | None = None,
        mcp_manager: Manager | None = None,
        max_concurrent_subagents: int = 3,
        provider_config: ProviderConfig | None = None,
    ) -> None:
        """
        Initialize the ClippyAgent.

        Args:
            permission_manager: Permission manager instance
            executor: Action executor instance
            api_key: API key for OpenAI-compatible provider
            model: Model identifier to use (required)
            base_url: Base URL for OpenAI-compatible API (for alternate providers)
            provider_config: Optional provider metadata (used for non-OpenAI providers)
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
        self.provider_config = provider_config

        # Create provider (OpenAI-compatible)
        self.provider = LLMProvider(
            api_key=api_key,
            base_url=base_url,
            provider_config=provider_config,
        )

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
        self.yolo_mode = False  # YOLO mode flag

        # Initialize subagent manager
        self.subagent_manager = SubAgentManager(
            parent_agent=self,
            permission_manager=permission_manager,
            executor=executor,
            max_concurrent=max_concurrent_subagents,
        )

        # Set up conversation persistence
        self.conversations_dir = Path.home() / ".clippy" / "conversations"
        self.conversations_dir.mkdir(exist_ok=True, parents=True)

    def _get_conversation_path(self, name: str) -> Path:
        """
        Get the file path for a conversation.

        Args:
            name: Name of the conversation

        Returns:
            Path to the conversation file
        """
        return self.conversations_dir / f"{name}.json"

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
            # Set conversation start time for filename generation
            self._conversation_start_time = time.time()

        # Add user message
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = self._run_agent_loop(auto_approve_all)

            # Save conversation automatically after each interaction
            success, message = self.save_conversation()
            if not success:
                logger.warning(f"Failed to auto-save conversation: {message}")

            return response
        except InterruptedExceptionError:
            return "Execution interrupted by user."

    def _run_agent_loop(self, auto_approve_all: bool = False) -> str:
        """Run the main agent loop."""
        config = AgentLoopConfig(
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
        return run_agent_loop(
            conversation_history=self.conversation_history,
            config=config,
        )

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
        self.interrupted = False
        # Clear conversation start time so new conversation gets fresh timestamp
        if hasattr(self, "_conversation_start_time"):
            delattr(self, "_conversation_start_time")

    def switch_model(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        provider_config: ProviderConfig | None = None,
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

            # Validate that we're not switching to an empty model
            if not new_model:
                return False, "Cannot switch to empty model"

            # Update provider config if provided
            if provider_config is not None:
                self.provider_config = provider_config

            # Create new provider with updated settings
            self.provider = LLMProvider(
                api_key=new_api_key,
                base_url=new_base_url,
                provider_config=self.provider_config,
            )

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

    def save_conversation(self, name: str | None = None) -> tuple[bool, str]:
        """
        Save the current conversation to disk.

        Args:
            name: Name for the conversation (optional - auto-generates if None)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure the conversations directory exists
            self.conversations_dir.mkdir(exist_ok=True, parents=True)

            # Auto-generate filename if not provided
            if name is None:
                # Use conversation start time if available, otherwise current time
                if hasattr(self, "_conversation_start_time"):
                    start_time = self._conversation_start_time
                else:
                    start_time = time.time()
                    self._conversation_start_time = start_time

                # Format as YYYYMMDD-HHMMSS
                datetime_str = datetime.fromtimestamp(start_time).strftime("%Y%m%d-%H%M%S")
                name = f"conversation-{datetime_str}"

            conversation_file = self.conversations_dir / f"{name}.json"

            # Prepare conversation data
            conversation_data = {
                "model": self.model,
                "base_url": self.base_url,
                "conversation_history": self.conversation_history,
                "timestamp": time.time(),
                "conversation_start_time": getattr(self, "_conversation_start_time", time.time()),
            }

            # Save to file
            with open(conversation_file, "w") as f:
                json.dump(conversation_data, f, indent=2)

            return True, f"Conversation saved as '{name}'"
        except (OSError, IOError, TypeError) as e:
            return False, f"Failed to save conversation: {e}"

    def load_conversation(self, name: str = "default") -> tuple[bool, str]:
        """
        Load a conversation from disk.

        Args:
            name: Name of the conversation to load (default: "default")

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conversation_file = self.conversations_dir / f"{name}.json"

            if not conversation_file.exists():
                return False, f"No saved conversation found with name '{name}'"

            # Load from file
            with open(conversation_file) as f:
                conversation_data = json.load(f)

            # Restore conversation data
            self.model = conversation_data.get("model", self.model)
            self.base_url = conversation_data.get("base_url", self.base_url)

            # Recreate provider with restored settings
            self.provider = LLMProvider(
                api_key=self.api_key,
                base_url=self.base_url,
                provider_config=self.provider_config,
            )

            self.conversation_history = conversation_data.get("conversation_history", [])

            # Restore conversation start time
            self._conversation_start_time = conversation_data.get(
                "conversation_start_time", time.time()
            )

            return True, f"Conversation '{name}' loaded successfully"
        except (OSError, IOError, json.JSONDecodeError) as e:
            return False, f"Failed to load conversation: {e}"

    def list_saved_conversations(self) -> list[str]:
        """
        List all saved conversations.

        Returns:
            List of conversation names
        """
        try:
            conversation_files = self.conversations_dir.glob("*.json")
            return [f.stem for f in conversation_files]
        except Exception:
            return []

    def delete_conversation(self, name: str) -> tuple[bool, str]:
        """
        Delete a saved conversation.

        Args:
            name: Name of the conversation to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conversation_file = self.conversations_dir / f"{name}.json"

            if not conversation_file.exists():
                return False, f"No saved conversation found with name '{name}'"

            conversation_file.unlink()
            return True, f"Conversation '{name}' deleted successfully"
        except Exception as e:
            return False, f"Failed to delete conversation: {e}"

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

    def toggle_yolo_mode(self) -> bool:
        """Toggle YOLO mode (auto-approve all actions).

        Returns:
            New YOLO mode state (True if enabled, False if disabled)
        """
        self.yolo_mode = not self.yolo_mode
        return self.yolo_mode

    def get_auto_actions(self) -> list[str]:
        """Get list of auto-approved actions.

        Returns:
            List of action type names that are auto-approved
        """
        auto_actions = []
        for action_type in self.permission_manager.config.auto_approve:
            auto_actions.append(action_type.value)
        return auto_actions

    def revoke_auto_action(self, action: Any) -> bool:
        """Revoke auto-approval for an action.

        Args:
            action: ActionType to revoke auto-approval for

        Returns:
            True if action was auto-approved and is now revoked, False otherwise
        """
        if action in self.permission_manager.config.auto_approve:
            self.permission_manager.config.auto_approve.remove(action)
            self.permission_manager.config.require_approval.add(action)
            return True
        return False

    def clear_auto_actions(self) -> int:
        """Clear all auto-approvals (move to require_approval).

        Returns:
            Number of actions that were moved from auto-approve to require-approval
        """
        count = len(self.permission_manager.config.auto_approve)
        self.permission_manager.config.require_approval.update(
            self.permission_manager.config.auto_approve
        )
        self.permission_manager.config.auto_approve.clear()
        return count

    def append_user_message(self, message: str) -> None:
        """Append a user message to the conversation.

        Args:
            message: User message to append
        """
        # Initialize with system message if first run
        if not self.conversation_history:
            self.conversation_history.append({"role": "system", "content": create_system_prompt()})

        self.conversation_history.append({"role": "user", "content": message})

    def restart_mcp(self) -> tuple[bool, str]:
        """Restart MCP manager and refresh connections.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.mcp_manager:
            return False, "MCP manager not available"

        try:
            # Stop and restart MCP manager
            self.mcp_manager.stop()
            self.mcp_manager.start()
            return True, "MCP manager restarted successfully"
        except Exception as e:
            return False, f"Error restarting MCP manager: {e}"
