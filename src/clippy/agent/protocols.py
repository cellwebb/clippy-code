"""Protocol interfaces for agent system components."""

from typing import Any, Protocol

from rich.console import Console

from ..models import ProviderConfig


class AgentProtocol(Protocol):
    """Protocol defining the interface for agent objects used in tool handling."""

    # Core conversation state
    yolo_mode: bool
    conversation_history: list[dict]

    # Provider configuration
    model: str
    api_key: str | None
    base_url: str | None
    provider_config: ProviderConfig | None

    # UI/IO components
    console: Console

    # MCP manager (optional)
    mcp_manager: Any | None

    def switch_model(self, model: str) -> None:
        """Switch to a different model.

        Args:
            model: New model identifier
        """
        ...

    def get_token_count(self) -> dict[str, Any]:
        """Get token usage statistics for the current conversation.

        Returns:
            Dictionary with token usage information
        """
        ...

    def save_conversation(self) -> tuple[bool, str]:
        """Save the current conversation to disk.

        Returns:
            Tuple of (success: bool, message: str)
        """
        ...


class ConsoleProtocol(Protocol):
    """Protocol for console-like objects that support print()."""

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to the console."""
        ...