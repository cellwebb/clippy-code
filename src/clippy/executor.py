"""Main ActionExecutor class that coordinates all operations."""

from typing import Any

from .mcp.naming import is_mcp_tool, parse_mcp_qualified_name
from .permissions import ActionType, PermissionManager
from .tools import (
    create_directory,
    delete_file,
    edit_file,
    execute_command,
    get_file_info,
    grep,
    list_directory,
    read_file,
    read_files,
    search_files,
    write_file,
)


class ActionExecutor:
    """Executes actions with permission checking."""

    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self._mcp_manager = None

    def set_mcp_manager(self, manager: Any) -> None:
        """
        Set the MCP manager for handling MCP tool calls.

        Args:
            manager: MCP Manager instance
        """
        self._mcp_manager = manager

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> tuple[bool, str, Any]:
        """
        Execute an action.

        Returns:
            Tuple of (success: bool, message: str, result: Any)
        """
        # Handle MCP tools first
        if is_mcp_tool(tool_name):
            if self._mcp_manager is None:
                return False, "MCP manager not available", None

            try:
                server_id, tool = parse_mcp_qualified_name(tool_name)
                return self._mcp_manager.execute(server_id, tool, tool_input)
            except Exception as e:
                return False, f"Error executing MCP tool {tool_name}: {str(e)}", None

        # Map tool names to action types
        action_map = {
            "read_file": ActionType.READ_FILE,
            "write_file": ActionType.WRITE_FILE,
            "delete_file": ActionType.DELETE_FILE,
            "list_directory": ActionType.LIST_DIR,
            "create_directory": ActionType.CREATE_DIR,
            "execute_command": ActionType.EXECUTE_COMMAND,
            "search_files": ActionType.SEARCH_FILES,
            "get_file_info": ActionType.GET_FILE_INFO,
            "read_files": ActionType.READ_FILE,  # Uses the same permission as read_file
            "grep": ActionType.GREP,  # Use dedicated GREP action type
            "edit_file": ActionType.EDIT_FILE,  # Add mapping for edit_file tool
        }

        action_type = action_map.get(tool_name)
        if not action_type:
            return False, f"Unknown tool: {tool_name}", None

        # Check if action is denied
        if self.permission_manager.config.is_denied(action_type):
            return False, f"Action {tool_name} is denied by policy", None

        # Execute the action
        try:
            if tool_name == "read_file":
                return read_file(tool_input["path"])
            elif tool_name == "write_file":
                return write_file(tool_input["path"], tool_input["content"])
            elif tool_name == "delete_file":
                return delete_file(tool_input["path"])
            elif tool_name == "list_directory":
                return list_directory(tool_input["path"], tool_input.get("recursive", False))
            elif tool_name == "create_directory":
                return create_directory(tool_input["path"])
            elif tool_name == "execute_command":
                return execute_command(tool_input["command"], tool_input.get("working_dir", "."))
            elif tool_name == "search_files":
                return search_files(tool_input["pattern"], tool_input.get("path", "."))
            elif tool_name == "get_file_info":
                return get_file_info(tool_input["path"])
            elif tool_name == "read_files":
                return read_files(tool_input["paths"])
            elif tool_name == "grep":
                return grep(tool_input["pattern"], tool_input["paths"], tool_input.get("flags", ""))
            elif tool_name == "edit_file":
                return edit_file(
                    tool_input["path"],
                    tool_input["operation"],
                    tool_input.get("content", ""),
                    tool_input.get("pattern", ""),
                    tool_input.get("match_pattern_line", True),
                    tool_input.get("inherit_indent", True),
                )
            else:
                return False, f"Unimplemented tool: {tool_name}", None
        except Exception as e:
            return False, f"Error executing {tool_name}: {str(e)}", None
