"""Tests for MCP exceptions."""

import pytest

from clippy.mcp.errors import (
    MCPConnectionError,
    MCPError,
    MCPPermissionError,
    MCPTimeoutError,
    MCPToolError,
    MCPToolNotFoundError,
)


class TestMCPExceptions:
    """Tests for MCP exception classes."""

    def test_mcp_error_is_exception(self) -> None:
        """Test that MCPError is an Exception."""
        assert issubclass(MCPError, Exception)

    def test_mcp_error_can_be_raised(self) -> None:
        """Test that MCPError can be raised and caught."""
        with pytest.raises(MCPError, match="Test error"):
            raise MCPError("Test error")

    def test_mcp_connection_error_inherits_from_mcp_error(self) -> None:
        """Test that MCPConnectionError inherits from MCPError."""
        assert issubclass(MCPConnectionError, MCPError)

    def test_mcp_connection_error_can_be_raised(self) -> None:
        """Test that MCPConnectionError can be raised."""
        with pytest.raises(MCPConnectionError, match="Connection failed"):
            raise MCPConnectionError("Connection failed")

    def test_mcp_tool_error_inherits_from_mcp_error(self) -> None:
        """Test that MCPToolError inherits from MCPError."""
        assert issubclass(MCPToolError, MCPError)

    def test_mcp_tool_error_can_be_raised(self) -> None:
        """Test that MCPToolError can be raised."""
        with pytest.raises(MCPToolError, match="Tool execution failed"):
            raise MCPToolError("Tool execution failed")

    def test_mcp_tool_not_found_error_inherits_from_mcp_error(self) -> None:
        """Test that MCPToolNotFoundError inherits from MCPError."""
        assert issubclass(MCPToolNotFoundError, MCPError)

    def test_mcp_tool_not_found_error_can_be_raised(self) -> None:
        """Test that MCPToolNotFoundError can be raised."""
        with pytest.raises(MCPToolNotFoundError, match="Tool not found"):
            raise MCPToolNotFoundError("Tool not found")

    def test_mcp_timeout_error_inherits_from_mcp_error(self) -> None:
        """Test that MCPTimeoutError inherits from MCPError."""
        assert issubclass(MCPTimeoutError, MCPError)

    def test_mcp_timeout_error_can_be_raised(self) -> None:
        """Test that MCPTimeoutError can be raised."""
        with pytest.raises(MCPTimeoutError, match="Operation timed out"):
            raise MCPTimeoutError("Operation timed out")

    def test_mcp_permission_error_inherits_from_mcp_error(self) -> None:
        """Test that MCPPermissionError inherits from MCPError."""
        assert issubclass(MCPPermissionError, MCPError)

    def test_mcp_permission_error_can_be_raised(self) -> None:
        """Test that MCPPermissionError can be raised."""
        with pytest.raises(MCPPermissionError, match="Permission denied"):
            raise MCPPermissionError("Permission denied")

    def test_catching_mcp_error_catches_all_subclasses(self) -> None:
        """Test that catching MCPError catches all MCP exception types."""
        exceptions = [
            MCPConnectionError("test"),
            MCPToolError("test"),
            MCPToolNotFoundError("test"),
            MCPTimeoutError("test"),
            MCPPermissionError("test"),
        ]

        for exc in exceptions:
            with pytest.raises(MCPError):
                raise exc

    def test_exception_messages_are_preserved(self) -> None:
        """Test that exception messages are preserved."""
        error_message = "Detailed error information"

        try:
            raise MCPConnectionError(error_message)
        except MCPConnectionError as e:
            assert str(e) == error_message

    def test_exceptions_can_be_chained(self) -> None:
        """Test that exceptions can be chained properly."""
        original_error = ValueError("Original error")

        try:
            try:
                raise original_error
            except ValueError as e:
                raise MCPConnectionError("MCP error") from e
        except MCPConnectionError as e:
            assert e.__cause__ is original_error
            assert isinstance(e.__cause__, ValueError)
