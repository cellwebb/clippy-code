"""Protocol interfaces for agent system components."""

from typing import Any, Protocol

from rich.console import Console

from ..models import ProviderConfig


class AgentProtocol(Protocol):
    """Protocol defining the interface for agent objects used in tool handling."""

    # Core conversation state
    yolo_mode: bool
    conversation_history: list[dict[str, Any]]

    # Provider configuration
    model: str
    api_key: str | None
    base_url: str | None
    provider_config: ProviderConfig | None

    # UI/IO components
    console: Console

    # MCP manager (optional)
    mcp_manager: Any | None

    def switch_model(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        provider_config: ProviderConfig | None = None,
    ) -> tuple[bool, str]:
        """Switch to a different model or provider.

        Args:
            model: New model identifier (if None, keeps current)
            base_url: New base URL (if None, keeps current)
            api_key: New API key (if None, keeps current)
            provider_config: New provider config (if None, keeps current)

        Returns:
            Tuple of (success: bool, message: str)
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
