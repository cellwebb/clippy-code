"""Tests for MCP transport implementations."""

import inspect

from clippy.mcp.transports import BaseTransport, StdioTransport


class TestBaseTransport:
    """Tests for BaseTransport class."""

    def test_base_transport_initialization(self) -> None:
        """Test BaseTransport initialization."""
        transport = BaseTransport()
        assert transport is not None

    def test_base_transport_has_async_methods(self) -> None:
        """Test BaseTransport has expected async methods."""
        transport = BaseTransport()
        # Check methods exist
        assert hasattr(transport, "connect")
        assert hasattr(transport, "disconnect")
        assert hasattr(transport, "send_request")
        # Methods should be coroutines
        assert inspect.iscoroutinefunction(transport.connect)
        assert inspect.iscoroutinefunction(transport.disconnect)
        assert inspect.iscoroutinefunction(transport.send_request)


class TestStdioTransport:
    """Tests for StdioTransport class."""

    def test_stdio_transport_initialization(self) -> None:
        """Test StdioTransport initialization with basic parameters."""
        transport = StdioTransport(
            command="python",
            args=["-m", "mcp_server"],
        )

        assert transport.command == "python"
        assert transport.args == ["-m", "mcp_server"]
        assert transport.env is None
        assert transport.cwd is None

    def test_stdio_transport_with_env(self) -> None:
        """Test StdioTransport initialization with environment variables."""
        env = {"PATH": "/usr/bin", "DEBUG": "1"}

        transport = StdioTransport(
            command="node",
            args=["server.js"],
            env=env,
        )

        assert transport.env == env
        assert transport.env["PATH"] == "/usr/bin"
        assert transport.env["DEBUG"] == "1"

    def test_stdio_transport_with_cwd(self) -> None:
        """Test StdioTransport initialization with working directory."""
        transport = StdioTransport(
            command="python",
            args=["-m", "server"],
            cwd="/path/to/server",
        )

        assert transport.cwd == "/path/to/server"

    def test_stdio_transport_with_all_parameters(self) -> None:
        """Test StdioTransport with all parameters."""
        env = {"VAR": "value"}

        transport = StdioTransport(
            command="node",
            args=["index.js", "--port", "3000"],
            env=env,
            cwd="/app",
        )

        assert transport.command == "node"
        assert transport.args == ["index.js", "--port", "3000"]
        assert transport.env == env
        assert transport.cwd == "/app"

    def test_stdio_transport_empty_args(self) -> None:
        """Test StdioTransport with empty args list."""
        transport = StdioTransport(
            command="server",
            args=[],
        )

        assert transport.args == []

    def test_stdio_transport_inherits_from_base_transport(self) -> None:
        """Test that StdioTransport inherits from BaseTransport."""
        assert issubclass(StdioTransport, BaseTransport)

    def test_stdio_transport_is_base_transport_instance(self) -> None:
        """Test that StdioTransport instance is also a BaseTransport instance."""
        transport = StdioTransport(command="test", args=[])
        assert isinstance(transport, BaseTransport)

    def test_stdio_transport_inherits_async_methods(self) -> None:
        """Test that StdioTransport inherits async methods from base class."""
        transport = StdioTransport(command="test", args=[])

        # Check async methods are inherited
        assert hasattr(transport, "connect")
        assert hasattr(transport, "disconnect")
        assert hasattr(transport, "send_request")
        assert inspect.iscoroutinefunction(transport.connect)
        assert inspect.iscoroutinefunction(transport.disconnect)
        assert inspect.iscoroutinefunction(transport.send_request)

    def test_stdio_transport_command_with_path(self) -> None:
        """Test StdioTransport with full path to command."""
        transport = StdioTransport(
            command="/usr/local/bin/python3",
            args=["-m", "server"],
        )

        assert transport.command == "/usr/local/bin/python3"

    def test_stdio_transport_args_ordering_preserved(self) -> None:
        """Test that argument order is preserved."""
        args = ["arg1", "arg2", "arg3", "--flag", "value"]

        transport = StdioTransport(
            command="test",
            args=args,
        )

        assert transport.args == args
        assert transport.args[0] == "arg1"
        assert transport.args[-1] == "value"

    def test_stdio_transport_env_none_by_default(self) -> None:
        """Test that env is None when not provided."""
        transport = StdioTransport(command="test", args=[])
        assert transport.env is None

    def test_stdio_transport_cwd_none_by_default(self) -> None:
        """Test that cwd is None when not provided."""
        transport = StdioTransport(command="test", args=[])
        assert transport.cwd is None

    def test_stdio_transport_multiple_instances_independent(self) -> None:
        """Test that multiple StdioTransport instances are independent."""
        transport1 = StdioTransport(
            command="python",
            args=["server1.py"],
            env={"VAR": "1"},
        )

        transport2 = StdioTransport(
            command="node",
            args=["server2.js"],
            env={"VAR": "2"},
        )

        assert transport1.command != transport2.command
        assert transport1.args != transport2.args
        assert transport1.env != transport2.env
