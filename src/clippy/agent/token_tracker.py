"""Token usage tracking for agent sessions."""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics for a single operation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    operation_type: str = "unknown"  # "main_agent", "subagent", "tool_call"
    operation_id: str = ""  # Subagent name or tool call identifier
    model: str = ""

    @classmethod
    def from_api_response(
        cls,
        usage_data: dict[str, int],
        operation: str = "unknown",
        operation_id: str = "",
        model: str = "",
    ) -> "TokenUsage":
        """Create TokenUsage from API response usage data.

        Args:
            usage_data: Usage dict from API response with prompt_tokens, completion_tokens,
                      total_tokens
            operation: Type of operation (main_agent, subagent, etc.)
            operation_id: Identifier for the specific operation
            model: Model name used

        Returns:
            TokenUsage instance
        """
        if not usage_data:
            return cls(operation_type=operation, operation_id=operation_id, model=model)

        return cls(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            operation_type=operation,
            operation_id=operation_id,
            model=model,
        )

    def add(self, other: "TokenUsage") -> "TokenUsage":
        """Add another TokenUsage to this one.

        Args:
            other: Another TokenUsage to add

        Returns:
            New TokenUsage with summed values
        """
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            operation_type="aggregated",
            operation_id="",
            model="",
        )


@dataclass
class SessionTokenStats:
    """Complete token statistics for a session."""

    main_agent: TokenUsage = field(default_factory=TokenUsage)
    subagents: list[TokenUsage] = field(default_factory=list)
    total: TokenUsage = field(default_factory=TokenUsage)


class SessionTracker:
    """Session-level token usage tracker."""

    def __init__(self, enabled: bool = True):
        """
        Initialize the session tracker.

        Args:
            enabled: Whether token tracking is enabled
        """
        self.enabled = enabled
        self.main_agent = TokenUsage()
        self.subagents: list[TokenUsage] = []

    def track_main_agent_usage(self, usage_data: dict[str, int], model: str) -> None:
        """Track token usage from main agent.

        Args:
            usage_data: Usage dict from API response
            model: Model name used
        """
        if not self.enabled or not usage_data:
            return

        new_usage = TokenUsage.from_api_response(usage_data, operation="main_agent", model=model)
        self.main_agent = self.main_agent.add(new_usage)

    def track_subagent_usage(
        self, usage_data: dict[str, int], subagent_name: str, model: str
    ) -> None:
        """Track token usage from a subagent.

        Args:
            usage_data: Usage dict from API response
            subagent_name: Name of the subagent
            model: Model name used
        """
        if not self.enabled or not usage_data:
            return

        new_usage = TokenUsage.from_api_response(
            usage_data, operation="subagent", operation_id=subagent_name, model=model
        )
        self.subagents.append(new_usage)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all token usage.

        Returns:
            Dictionary with token usage summary
        """
        # Calculate total subagent usage
        subagent_total = TokenUsage()
        for usage in self.subagents:
            subagent_total = subagent_total.add(usage)

        # Calculate grand total
        grand_total = self.main_agent.add(subagent_total)

        # Build subagent details
        subagent_details = []
        for usage in self.subagents:
            subagent_details.append(
                {
                    "name": usage.operation_id,
                    "model": usage.model,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }
            )

        return {
            "total": {
                "prompt_tokens": grand_total.prompt_tokens,
                "completion_tokens": grand_total.completion_tokens,
                "total_tokens": grand_total.total_tokens,
            },
        }

    def is_enabled(self) -> bool:
        """Check if token tracking is enabled.

        Returns:
            True if tracking is enabled
        """
        return self.enabled

    def enable(self) -> None:
        """Enable token tracking."""
        self.enabled = True

    def disable(self) -> None:
        """Disable token tracking."""
        self.enabled = False

    def reset(self) -> None:
        """Reset all token usage statistics."""
        self.main_agent = TokenUsage()
        self.subagents.clear()


# Global session tracker instance
_session_tracker: SessionTracker | None = None


def get_session_tracker() -> SessionTracker:
    """Get the global session tracker instance.

    Returns:
        The global SessionTracker instance
    """
    global _session_tracker
    if _session_tracker is None:
        _session_tracker = SessionTracker()
    return _session_tracker
