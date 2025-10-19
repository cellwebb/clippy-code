"""Tests for the MCP manager."""

import asyncio
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


@patch("clippy.mcp.manager.stdio_client")
def test_manager_start(mock_stdio_client) -> None:
    """Test that manager starts sessions correctly."""

    # Create a proper async context manager mock
    class MockSession:
        def __init__(self):
            self.initialize = AsyncMock()
            self.list_tools = AsyncMock()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_session = MockSession()
    mock_session.initialize.return_value = Mock()
    mock_session.list_tools.return_value = Mock(tools=[])

    mock_stdio_client.return_value = mock_session

    config = Config(
        mcp_servers={
            "test-server": ServerConfig(
                command="echo",
                args=["hello"],
            )
        }
    )

    manager = Manager(config=config)

    # Run the async start method
    async def run_start():
        await manager.start()

    asyncio.run(run_start())

    # Verify stdio_client was called with correct parameters
    mock_stdio_client.assert_called_once()
    # Verify session methods were called
    mock_session.initialize.assert_called_once()
    mock_session.list_tools.assert_called_once()


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

    # Initially not trusted
    assert manager.is_trusted("test-server") is False

    # Set trusted
    manager.set_trusted("test-server", True)
    assert manager.is_trusted("test-server") is True

    # Revoke trust
    manager.set_trusted("test-server", False)
    assert manager.is_trusted("test-server") is False
