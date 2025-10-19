"""Tests for the MCP manager."""

from unittest.mock import AsyncMock, Mock, patch

from clippy.mcp.config import Config, ServerConfig
from clippy.mcp.manager import Manager


def test_manager_initialization() -> None:
    """Test that manager initializes correctly."""
    config = Config(
        mcp_servers={
            "test-server": ServerConfig(
                command="echo",
                args=["hello"],
            )
        }
    )

    manager = Manager(config=config)
    assert manager.config == config
    assert len(manager._sessions) == 0
    assert len(manager._tools) == 0


@patch("clippy.mcp.manager.ClientSession")
@patch("clippy.mcp.manager.stdio_client")
def test_manager_start(mock_stdio_client, mock_client_session) -> None:
    """Test that manager starts sessions correctly."""

    # Create mock streams
    mock_read_stream = Mock()
    mock_write_stream = Mock()

    # Create mock session
    mock_session = Mock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=Mock(tools=[]))
    mock_session.call_tool = AsyncMock()

    # Create stdio context manager that returns streams
    class MockStdioContext:
        async def __aenter__(self):
            return mock_read_stream, mock_write_stream

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_stdio_client.return_value = MockStdioContext()

    # Create session context manager that returns session
    class MockSessionContext:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client_session.return_value = MockSessionContext()

    config = Config(
        mcp_servers={
            "test-server": ServerConfig(
                command="echo",
                args=["hello"],
            )
        }
    )

    manager = Manager(config=config)

    # Start is now synchronous
    manager.start()

    # Give the background thread time to complete
    import time

    time.sleep(0.1)

    # Verify stdio_client was called
    mock_stdio_client.assert_called_once()
    # Verify ClientSession was created with streams
    mock_client_session.assert_called_once_with(mock_read_stream, mock_write_stream)
    # Verify session methods were called
    mock_session.initialize.assert_called_once()
    mock_session.list_tools.assert_called_once()
    # Verify session is kept alive (stored in _sessions)
    assert "test-server" in manager._sessions
    assert manager._sessions["test-server"] == mock_session

    # Clean up
    manager.stop()


def test_manager_list_servers() -> None:
    """Test listing servers."""
    config = Config(
        mcp_servers={
            "test-server": ServerConfig(
                command="echo",
                args=["hello"],
            )
        }
    )

    manager = Manager(config=config)
    servers = manager.list_servers()

    assert len(servers) == 1
    assert servers[0]["server_id"] == "test-server"
    assert servers[0]["connected"] is False
    assert servers[0]["tools_count"] == 0


def test_manager_trust_functionality() -> None:
    """Test server trust functionality."""
    config = Config(
        mcp_servers={
            "test-server": ServerConfig(
                command="echo",
                args=["hello"],
            )
        }
    )

    manager = Manager(config=config)

    # Initially not trusted (before connection)
    assert manager.is_trusted("test-server") is False

    # Set trusted manually
    manager.set_trusted("test-server", True)
    assert manager.is_trusted("test-server") is True

    # Revoke trust
    manager.set_trusted("test-server", False)
    assert manager.is_trusted("test-server") is False


@patch("clippy.mcp.manager.ClientSession")
@patch("clippy.mcp.manager.stdio_client")
def test_manager_manual_trust(mock_stdio_client, mock_client_session) -> None:
    """Test that servers require manual trust and are not auto-trusted on connection."""

    # Create mock streams
    mock_read_stream = Mock()
    mock_write_stream = Mock()

    # Create mock session
    mock_session = Mock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=Mock(tools=[]))

    # Create stdio context manager that returns streams
    class MockStdioContext:
        async def __aenter__(self):
            return mock_read_stream, mock_write_stream

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_stdio_client.return_value = MockStdioContext()

    # Create session context manager that returns session
    class MockSessionContext:
        async def __aenter__(self):
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client_session.return_value = MockSessionContext()

    config = Config(
        mcp_servers={
            "test-server": ServerConfig(
                command="echo",
                args=["hello"],
            )
        }
    )

    manager = Manager(config=config)

    # Before connection, not trusted
    assert manager.is_trusted("test-server") is False

    # Start is now synchronous
    manager.start()

    # Give the background thread time to complete
    import time

    time.sleep(0.1)

    # After successful connection, should still NOT be auto-trusted
    assert manager.is_trusted("test-server") is False

    # But can be manually trusted
    manager.set_trusted("test-server", True)
    assert manager.is_trusted("test-server") is True

    # Clean up
    manager.stop()
