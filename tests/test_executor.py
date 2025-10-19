"""Tests for the action executor."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig, PermissionManager


@pytest.fixture
def permission_manager() -> PermissionManager:
    """Create a permission manager."""
    return PermissionManager(PermissionConfig())


@pytest.fixture
def executor(permission_manager: PermissionManager) -> ActionExecutor:
    """Create an executor instance."""
    return ActionExecutor(permission_manager)


class TestExecutorInitialization:
    """Tests for ActionExecutor initialization."""

    def test_executor_initialization(self, permission_manager: PermissionManager) -> None:
        """Test that executor initializes correctly."""
        executor = ActionExecutor(permission_manager)

        assert executor.permission_manager is permission_manager
        assert executor._mcp_manager is None

    def test_set_mcp_manager(self, executor: ActionExecutor) -> None:
        """Test setting MCP manager."""
        mock_manager = MagicMock()
        executor.set_mcp_manager(mock_manager)

        assert executor._mcp_manager is mock_manager


class TestExecutorBasicActions:
    """Tests for basic executor actions."""

    def test_execute_unknown_action(self, executor: ActionExecutor) -> None:
        """Test executing an unknown action."""
        success, message, content = executor.execute("unknown_action", {})

        assert success is False
        assert "Unknown tool" in message
        assert content is None

    def test_execute_read_file(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing read_file action."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        success, message, content = executor.execute("read_file", {"path": str(test_file)})

        assert success is True
        assert "Hello, World!" in content

    def test_execute_write_file(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing write_file action."""
        test_file = tmp_path / "output.txt"

        success, message, content = executor.execute(
            "write_file", {"path": str(test_file), "content": "Test content"}
        )

        assert success is True
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "Test content"

    def test_execute_delete_file(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing delete_file action."""
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("delete me", encoding="utf-8")

        success, message, content = executor.execute("delete_file", {"path": str(test_file)})

        assert success is True
        assert not test_file.exists()

    def test_execute_create_directory(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing create_directory action."""
        new_dir = tmp_path / "new_directory"

        success, message, content = executor.execute("create_directory", {"path": str(new_dir)})

        assert success is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_execute_list_directory(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing list_directory action."""
        # Create some files
        (tmp_path / "file1.txt").write_text("test", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("test", encoding="utf-8")

        success, message, content = executor.execute(
            "list_directory", {"path": str(tmp_path), "recursive": False}
        )

        assert success is True
        assert "file1.txt" in content
        assert "file2.txt" in content

    def test_execute_list_directory_recursive(
        self, executor: ActionExecutor, tmp_path: Path
    ) -> None:
        """Test executing list_directory with recursive option."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("test", encoding="utf-8")

        success, message, content = executor.execute(
            "list_directory", {"path": str(tmp_path), "recursive": True}
        )

        assert success is True
        assert "nested.txt" in content or "subdir" in content

    def test_execute_get_file_info(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing get_file_info action."""
        test_file = tmp_path / "info.txt"
        test_file.write_text("test content", encoding="utf-8")

        success, message, content = executor.execute("get_file_info", {"path": str(test_file)})

        assert success is True
        assert "size:" in content or "modified:" in content

    def test_execute_search_files(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing search_files action."""
        (tmp_path / "test.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "main.py").write_text("print('world')", encoding="utf-8")

        success, message, content = executor.execute(
            "search_files", {"pattern": "*.py", "path": str(tmp_path)}
        )

        assert success is True
        assert "test.py" in content or "main.py" in content

    def test_execute_read_files(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing read_files action."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1", encoding="utf-8")
        file2.write_text("Content 2", encoding="utf-8")

        success, message, content = executor.execute(
            "read_files", {"paths": [str(file1), str(file2)]}
        )

        assert success is True
        assert "Content 1" in content
        assert "Content 2" in content

    def test_execute_grep(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing grep action with paths parameter."""
        test_file = tmp_path / "grep_test.txt"
        test_file.write_text("line 1\npattern match\nline 3", encoding="utf-8")

        success, message, content = executor.execute(
            "grep", {"pattern": "pattern", "paths": [str(test_file)], "flags": ""}
        )

        assert success is True

    def test_execute_grep_with_path_singular(
        self, executor: ActionExecutor, tmp_path: Path
    ) -> None:
        """Test executing grep with path (singular) parameter."""
        test_file = tmp_path / "grep_test.txt"
        test_file.write_text("search term here", encoding="utf-8")

        success, message, content = executor.execute(
            "grep", {"pattern": "search", "path": str(test_file), "flags": ""}
        )

        assert success is True

    def test_execute_grep_without_path_or_paths(self, executor: ActionExecutor) -> None:
        """Test executing grep without path or paths parameter."""
        success, message, content = executor.execute("grep", {"pattern": "test", "flags": ""})

        assert success is False
        assert "requires either 'path' or 'paths'" in message

    def test_execute_command(self, executor: ActionExecutor) -> None:
        """Test executing execute_command action."""
        success, message, content = executor.execute(
            "execute_command", {"command": "echo hello", "working_dir": "."}
        )

        assert success is True
        assert "hello" in content.lower()

    def test_execute_command_default_working_dir(self, executor: ActionExecutor) -> None:
        """Test execute_command with default working directory."""
        success, message, content = executor.execute("execute_command", {"command": "echo test"})

        assert success is True

    def test_execute_edit_file(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test executing edit_file action."""
        test_file = tmp_path / "edit_test.txt"
        test_file.write_text("original content\nline 2\nline 3", encoding="utf-8")

        success, message, content = executor.execute(
            "edit_file",
            {
                "path": str(test_file),
                "operation": "replace",
                "pattern": "original content",
                "content": "new content",
                "match_pattern_line": True,
                "inherit_indent": True,
            },
        )

        assert success is True


class TestExecutorPermissions:
    """Tests for executor permission checking."""

    def test_denied_action(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test that denied actions are blocked."""
        # Deny write_file action
        executor.permission_manager.config.deny.add(ActionType.WRITE_FILE)

        test_file = tmp_path / "test.txt"
        success, message, content = executor.execute(
            "write_file", {"path": str(test_file), "content": "test"}
        )

        assert success is False
        assert "denied" in message.lower()

    def test_allowed_action_after_permission_change(
        self, executor: ActionExecutor, tmp_path: Path
    ) -> None:
        """Test that action succeeds after permission is granted."""
        test_file = tmp_path / "test.txt"

        # First, ensure it's not denied
        executor.permission_manager.config.deny.discard(ActionType.READ_FILE)

        success, message, content = executor.execute("read_file", {"path": str(test_file)})

        # Should fail because file doesn't exist, not because of permissions
        assert "denied" not in message.lower()


class TestExecutorErrorHandling:
    """Tests for executor error handling."""

    def test_execute_handles_tool_exception(self, executor: ActionExecutor) -> None:
        """Test that tool execution exceptions are caught."""
        # Try to read a file that doesn't exist
        success, message, content = executor.execute(
            "read_file", {"path": "/nonexistent/path/to/file.txt"}
        )

        assert success is False
        assert "Error executing" in message or "not found" in message.lower()

    def test_execute_handles_missing_required_parameter(self, executor: ActionExecutor) -> None:
        """Test handling of missing required parameters."""
        success, message, content = executor.execute("read_file", {})

        assert success is False
        assert "Error executing" in message

    def test_execute_handles_invalid_parameter_type(self, executor: ActionExecutor) -> None:
        """Test handling of invalid parameter types."""
        success, message, content = executor.execute("read_file", {"path": None})

        assert success is False


class TestExecutorMCPTools:
    """Tests for MCP tool execution."""

    def test_mcp_tool_without_manager(self, executor: ActionExecutor) -> None:
        """Test that MCP tools fail when manager is not set."""
        success, message, content = executor.execute("mcp__server__tool", {})

        assert success is False
        assert "MCP manager not available" in message

    def test_mcp_tool_with_manager(self, executor: ActionExecutor) -> None:
        """Test executing MCP tool with manager set."""
        mock_manager = MagicMock()
        mock_manager.execute.return_value = (True, "Success", "result")
        executor.set_mcp_manager(mock_manager)

        success, message, content = executor.execute("mcp__server__tool", {"arg": "value"})

        assert success is True
        mock_manager.execute.assert_called_once_with("server", "tool", {"arg": "value"}, False)

    def test_mcp_tool_execution_error(self, executor: ActionExecutor) -> None:
        """Test handling of MCP tool execution errors."""
        mock_manager = MagicMock()
        mock_manager.execute.side_effect = Exception("MCP Error")
        executor.set_mcp_manager(mock_manager)

        success, message, content = executor.execute("mcp__server__tool", {})

        assert success is False
        assert "Error executing MCP tool" in message
        assert "MCP Error" in message

    def test_mcp_tool_with_invalid_qualified_name(self, executor: ActionExecutor) -> None:
        """Test MCP tool with invalid qualified name."""
        mock_manager = MagicMock()
        executor.set_mcp_manager(mock_manager)

        # "mcp__invalid" is actually invalid because it only has 2 parts, not 3
        # It won't be recognized as an MCP tool
        success, message, content = executor.execute("mcp__invalid", {})

        assert success is False
        # Will be treated as unknown tool since it's not a valid MCP format
        assert "Unknown tool" in message or "Error executing MCP tool" in message


class TestExecutorEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def test_execute_with_empty_tool_input(self, executor: ActionExecutor) -> None:
        """Test executing with empty tool input."""
        success, message, content = executor.execute("unknown_tool", {})

        assert success is False

    def test_execute_list_directory_defaults_recursive_to_false(
        self, executor: ActionExecutor, tmp_path: Path
    ) -> None:
        """Test that list_directory defaults recursive to False."""
        success, message, content = executor.execute("list_directory", {"path": str(tmp_path)})

        # Should succeed with default recursive=False
        assert success is True

    def test_execute_search_files_defaults_path_to_current_dir(
        self, executor: ActionExecutor
    ) -> None:
        """Test that search_files defaults path to current directory."""
        success, message, content = executor.execute("search_files", {"pattern": "*.py"})

        # Should execute (may or may not find files, but shouldn't error)
        assert message is not None

    def test_execute_grep_with_flags(self, executor: ActionExecutor, tmp_path: Path) -> None:
        """Test grep with flags parameter."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("TEST content", encoding="utf-8")

        success, message, content = executor.execute(
            "grep", {"pattern": "test", "path": str(test_file), "flags": "i"}
        )

        # Should execute (behavior depends on grep implementation)
        assert message is not None

    def test_executor_permission_manager_is_accessible(
        self, executor: ActionExecutor, permission_manager: PermissionManager
    ) -> None:
        """Test that permission manager is accessible."""
        assert executor.permission_manager is permission_manager
        assert executor.permission_manager.config is not None
