"""MCP manager access for CLI commands.

This module provides access to the MCP manager from CLI command handlers.
"""

from typing import Any

# This is a placeholder for MCP manager functionality
# In practice, the MCP manager should be accessed through the agent


class MockMCPManager:
    """Mock MCP manager for when MCP is not available."""

    def list_servers(self) -> list[dict[str, Any]]:
        """Return empty list when MCP is not available."""
        return []

    def add_server(self, name: str, command: list[str]) -> tuple[bool, str]:
        """Return failure when MCP is not available."""
        return False, "MCP support not available"

    def remove_server(self, name: str) -> tuple[bool, str]:
        """Return failure when MCP is not available."""
        return False, "MCP support not available"

    def restart_server(self, name: str) -> tuple[bool, str]:
        """Return failure when MCP is not available."""
        return False, "MCP support not available"

    def restart_all_servers(self) -> tuple[bool, str]:
        """Return failure when MCP is not available."""
        return False, "MCP support not available"


# Global variable to hold the MCP manager instance
_mcp_manager_instance: Any = None


def get_mcp_manager() -> Any:
    """
    Get the MCP manager instance.

    Returns:
        MCP manager instance or mock if not available
    """
    global _mcp_manager_instance
    return _mcp_manager_instance or MockMCPManager()


def set_mcp_manager(manager: Any) -> None:
    """
    Set the MCP manager instance.

    Args:
        manager: MCP manager instance
    """
    global _mcp_manager_instance
    _mcp_manager_instance = manager


__all__ = [
    "get_mcp_manager",
    "set_mcp_manager",
]
