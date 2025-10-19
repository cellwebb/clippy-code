"""Tests for MCP functionality in document mode."""

from unittest.mock import Mock, patch

from clippy.ui.document_app import DocumentApp


class TestMCPDocumentMode:
    """Test MCP commands in document mode."""

    def test_mcp_command_routing(self) -> None:
        """Test that MCP commands are properly routed."""
        # Create a mock agent with MCP manager
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        # Create document app
        app = DocumentApp(mock_agent)

        # Test that MCP command is recognized
        assert hasattr(app, "handle_mcp_command")

    def test_mcp_list_command_no_servers(self) -> None:
        """Test /mcp list when no servers are configured."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_mcp_manager.list_servers.return_value = []
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_list(mock_mcp_manager, conv_log)

        # Should write about no servers configured
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("No MCP servers configured" in call for call in calls)

    def test_mcp_list_command_with_servers(self) -> None:
        """Test /mcp list with configured servers."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_mcp_manager.list_servers.return_value = [
            {"server_id": "test-server", "connected": True, "tools_count": 5},
            {"server_id": "another-server", "connected": False, "tools_count": 0},
        ]
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_list(mock_mcp_manager, conv_log)

        # Should write server information
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("Configured MCP Servers" in call for call in calls)
        assert any("test-server" in call for call in calls)
        assert any("another-server" in call for call in calls)

    def test_mcp_tools_command_no_tools(self) -> None:
        """Test /mcp tools when no tools are available."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_mcp_manager.list_tools.return_value = []
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_tools(mock_mcp_manager, conv_log, "")

        # Should write about no tools available
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("No MCP tools available" in call for call in calls)

    def test_mcp_tools_command_with_tools(self) -> None:
        """Test /mcp tools with available tools."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_mcp_manager.list_tools.return_value = [
            {"server_id": "test-server", "name": "read_file", "description": "Read a file"},
            {"server_id": "test-server", "name": "write_file", "description": "Write a file"},
            {"server_id": "another-server", "name": "search", "description": "Search content"},
        ]
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_tools(mock_mcp_manager, conv_log, "")

        # Should write tool information
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("Available MCP Tools" in call for call in calls)
        assert any("test-server" in call for call in calls)
        assert any("read_file" in call for call in calls)

    def test_mcp_allow_command(self) -> None:
        """Test /mcp allow command."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_allow(mock_mcp_manager, conv_log, "test-server")

        # Should call set_trusted and write success message
        mock_mcp_manager.set_trusted.assert_called_once_with("test-server", True)
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("trusted" in call.lower() for call in calls)

    def test_mcp_allow_command_no_server(self) -> None:
        """Test /mcp allow without server argument."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_allow(mock_mcp_manager, conv_log, "")

        # Should write usage error
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("Usage:" in call for call in calls)

    def test_mcp_revoke_command(self) -> None:
        """Test /mcp revoke command."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_revoke(mock_mcp_manager, conv_log, "test-server")

        # Should call set_trusted and write success message
        mock_mcp_manager.set_trusted.assert_called_once_with("test-server", False)
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("revoked" in call.lower() for call in calls)

    def test_mcp_command_no_manager(self) -> None:
        """Test MCP commands when MCP manager is not available."""
        mock_agent = Mock()
        mock_agent.mcp_manager = None  # Explicitly set to None

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        # Mock the query_one to avoid UI framework issues
        app.query_one = Mock(return_value=conv_log)

        app.handle_mcp_command("/mcp list")

        # Should write error about MCP not available
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("MCP functionality not available" in call for call in calls)

    def test_mcp_command_unknown_subcommand(self) -> None:
        """Test MCP command with unknown subcommand."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        # Mock the query_one to avoid UI framework issues
        app.query_one = Mock(return_value=conv_log)

        app.handle_mcp_command("/mcp unknown")

        # Should write error about unknown command
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("Unknown MCP command" in call for call in calls)

    @patch("threading.Thread")
    def test_mcp_refresh_command(self, mock_thread) -> None:
        """Test /mcp refresh command."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        # Mock list_servers to return servers after refresh
        mock_mcp_manager.list_servers.return_value = [
            {"server_id": "test-server", "connected": True, "tools_count": 5}
        ]

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        app._handle_mcp_refresh(mock_mcp_manager, conv_log)

        # Should create thread and write refresh messages
        mock_thread.assert_called_once()
        conv_log.write.assert_called()
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("Refreshing" in call for call in calls)

    def test_mcp_command_with_spaces_in_args(self) -> None:
        """Test MCP commands with spaces in arguments."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)
        conv_log = Mock()

        # Mock the query_one to avoid UI framework issues
        app.query_one = Mock(return_value=conv_log)

        # Test command with server name containing spaces (edge case)
        app.handle_mcp_command("/mcp allow  test-server  ")

        # Should trim whitespace and call correctly
        mock_mcp_manager.set_trusted.assert_called_once_with("test-server", True)

    def test_individual_handler_methods(self) -> None:
        """Test that individual MCP handler methods exist and work."""
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_mcp_manager.list_servers.return_value = []
        mock_mcp_manager.list_tools.return_value = []
        mock_agent.mcp_manager = mock_mcp_manager

        app = DocumentApp(mock_agent)

        # Test that all handler methods exist
        assert hasattr(app, "_handle_mcp_list")
        assert hasattr(app, "_handle_mcp_tools")
        assert hasattr(app, "_handle_mcp_refresh")
        assert hasattr(app, "_handle_mcp_allow")
        assert hasattr(app, "_handle_mcp_revoke")

        # Test individual handlers with mocked conv_log
        conv_log = Mock()
        app._handle_mcp_list(mock_mcp_manager, conv_log)
        conv_log.write.assert_called()

        # Test allow/revoke with empty args (should show usage)
        conv_log.reset_mock()
        app._handle_mcp_allow(mock_mcp_manager, conv_log, "")
        assert conv_log.write.called
        calls = [str(call.args[0]) for call in conv_log.write.call_args_list]
        assert any("Usage:" in call for call in calls)
