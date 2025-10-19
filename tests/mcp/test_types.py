"""Tests for MCP type definitions."""

from clippy.mcp.types import ServerInfo, TargetTool


class TestServerInfo:
    """Tests for ServerInfo class."""

    def test_server_info_initialization(self) -> None:
        """Test ServerInfo initialization."""
        server = ServerInfo(
            server_id="test_server",
            name="Test Server",
            description="A test MCP server",
            connection_status="connected",
        )

        assert server.server_id == "test_server"
        assert server.name == "Test Server"
        assert server.description == "A test MCP server"
        assert server.connection_status == "connected"

    def test_server_info_with_disconnected_status(self) -> None:
        """Test ServerInfo with disconnected status."""
        server = ServerInfo(
            server_id="test_server",
            name="Test Server",
            description="Test",
            connection_status="disconnected",
        )

        assert server.connection_status == "disconnected"

    def test_server_info_with_error_status(self) -> None:
        """Test ServerInfo with error status."""
        server = ServerInfo(
            server_id="test_server",
            name="Test Server",
            description="Test",
            connection_status="error",
        )

        assert server.connection_status == "error"

    def test_server_info_attributes_are_mutable(self) -> None:
        """Test that ServerInfo attributes can be modified."""
        server = ServerInfo(
            server_id="test",
            name="Original Name",
            description="Original Description",
            connection_status="disconnected",
        )

        # Modify attributes
        server.name = "New Name"
        server.description = "New Description"
        server.connection_status = "connected"

        assert server.name == "New Name"
        assert server.description == "New Description"
        assert server.connection_status == "connected"

    def test_server_info_with_empty_strings(self) -> None:
        """Test ServerInfo with empty string values."""
        server = ServerInfo(
            server_id="",
            name="",
            description="",
            connection_status="",
        )

        assert server.server_id == ""
        assert server.name == ""
        assert server.description == ""
        assert server.connection_status == ""


class TestTargetTool:
    """Tests for TargetTool class."""

    def test_target_tool_initialization(self) -> None:
        """Test TargetTool initialization."""
        tool = TargetTool(
            server_id="test_server",
            tool_name="read_file",
            description="Read a file from the filesystem",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        )

        assert tool.server_id == "test_server"
        assert tool.tool_name == "read_file"
        assert tool.description == "Read a file from the filesystem"
        assert tool.input_schema == {"type": "object", "properties": {"path": {"type": "string"}}}

    def test_target_tool_with_complex_schema(self) -> None:
        """Test TargetTool with complex input schema."""
        complex_schema = {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "encoding": {"type": "string", "default": "utf-8"},
                "max_lines": {"type": "integer", "minimum": 1},
            },
            "required": ["file_path"],
        }

        tool = TargetTool(
            server_id="test_server",
            tool_name="advanced_read",
            description="Advanced file reading",
            input_schema=complex_schema,
        )

        assert tool.input_schema == complex_schema
        assert "required" in tool.input_schema
        assert tool.input_schema["required"] == ["file_path"]

    def test_target_tool_attributes_are_mutable(self) -> None:
        """Test that TargetTool attributes can be modified."""
        tool = TargetTool(
            server_id="test",
            tool_name="original_name",
            description="Original description",
            input_schema={},
        )

        # Modify attributes
        tool.tool_name = "new_name"
        tool.description = "New description"
        tool.input_schema = {"type": "string"}

        assert tool.tool_name == "new_name"
        assert tool.description == "New description"
        assert tool.input_schema == {"type": "string"}

    def test_target_tool_with_empty_schema(self) -> None:
        """Test TargetTool with empty input schema."""
        tool = TargetTool(
            server_id="test",
            tool_name="simple_tool",
            description="A simple tool with no inputs",
            input_schema={},
        )

        assert tool.input_schema == {}

    def test_target_tool_with_nested_schema(self) -> None:
        """Test TargetTool with nested schema structures."""
        nested_schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "integer"},
                        "retry": {"type": "boolean"},
                    },
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }

        tool = TargetTool(
            server_id="test",
            tool_name="batch_process",
            description="Process multiple files",
            input_schema=nested_schema,
        )

        assert "config" in tool.input_schema["properties"]
        assert "files" in tool.input_schema["properties"]
        assert tool.input_schema["properties"]["files"]["type"] == "array"

    def test_target_tool_multiple_instances(self) -> None:
        """Test creating multiple TargetTool instances."""
        tool1 = TargetTool(
            server_id="server1",
            tool_name="tool1",
            description="First tool",
            input_schema={"type": "object"},
        )

        tool2 = TargetTool(
            server_id="server2",
            tool_name="tool2",
            description="Second tool",
            input_schema={"type": "string"},
        )

        # Instances should be independent
        assert tool1.server_id != tool2.server_id
        assert tool1.tool_name != tool2.tool_name
        assert tool1.description != tool2.description
        assert tool1.input_schema != tool2.input_schema
