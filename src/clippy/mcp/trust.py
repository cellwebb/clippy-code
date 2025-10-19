"""MCP trust utilities."""


class TrustStore:
    """Handles trust decisions for MCP servers."""

    def __init__(self) -> None:
        self._trusted_servers: set[str] = set()

    def is_trusted(self, server_id: str) -> bool:
        """
        Check if a server is trusted for this session.

        Args:
            server_id: Server identifier

        Returns:
            True if server is trusted
        """
        return server_id in self._trusted_servers

    def set_trusted(self, server_id: str, trusted: bool) -> None:
        """
        Set trust status for a server.

        Args:
            server_id: Server identifier
            trusted: Trust status
        """
        if trusted:
            self._trusted_servers.add(server_id)
        else:
            self._trusted_servers.discard(server_id)

    def get_trusted_servers(self) -> set[str]:
        """
        Get all trusted servers.

        Returns:
            Set of trusted server IDs
        """
        return self._trusted_servers.copy()
