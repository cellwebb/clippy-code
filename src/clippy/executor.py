"""Main ActionExecutor class that coordinates all operations."""

import logging
from typing import Any

from .mcp.naming import is_mcp_tool, parse_mcp_qualified_name
from .permissions import ActionType, PermissionManager

# Import tool functions explicitly to avoid module/function conflicts
from .tools.create_directory import create_directory as _create_directory_util
from .tools.delete_file import delete_file as _delete_file_util
from .tools.edit_file import edit_file
from .tools.execute_command import execute_command
from .tools.find_replace import find_replace
from .tools.get_file_info import get_file_info
from .tools.grep import grep
from .tools.list_directory import list_directory
from .tools.read_file import read_file
from .tools.read_files import read_files
from .tools.search_files import search_files
from .tools.think import think
from .tools.write_file import write_file

logger = logging.getLogger(__name__)


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

    def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        bypass_trust_check: bool = False,
    ) -> tuple[bool, str, Any]:
        """
        Execute an action.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            bypass_trust_check: If True, skip MCP trust check (for user-approved calls)

        Returns:
            Tuple of (success: bool, message: str, result: Any)
        """
        logger.debug(f"Executing tool: {tool_name}, bypass_trust={bypass_trust_check}")

        # Handle MCP tools first
        if is_mcp_tool(tool_name):
            if self._mcp_manager is None:
                logger.error("MCP tool execution failed: MCP manager not available")
                return False, "MCP manager not available", None

            try:
                server_id, tool = parse_mcp_qualified_name(tool_name)
                logger.debug(f"Delegating to MCP manager: server={server_id}, tool={tool}")
                return self._mcp_manager.execute(server_id, tool, tool_input, bypass_trust_check)
            except Exception as e:
                logger.error(f"Error executing MCP tool {tool_name}: {e}", exc_info=True)
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
            "find_replace": ActionType.FIND_REPLACE,
            "think": ActionType.THINK,
            "delegate_to_subagent": ActionType.DELEGATE_TO_SUBAGENT,
            "run_parallel_subagents": ActionType.RUN_PARALLEL_SUBAGENTS,
        }

        action_type = action_map.get(tool_name)
        if not action_type:
            logger.warning(f"Unknown tool requested: {tool_name}")
            return False, f"Unknown tool: {tool_name}", None

        logger.debug(f"Tool mapped to action type: {action_type}")

        # Check if action is denied
        if self.permission_manager.config.is_denied(action_type):
            logger.warning(f"Action denied by permission manager: {tool_name} ({action_type})")
            return False, f"Action {tool_name} is denied by policy", None

        # Execute the action
        logger.debug(f"Executing built-in tool: {tool_name}")
        try:
            if tool_name == "read_file":
                result = read_file(tool_input["path"])
            elif tool_name == "write_file":
                result = write_file(
                    tool_input["path"],
                    tool_input["content"],
                    tool_input.get("skip_validation", False),
                )
            elif tool_name == "list_directory":
                result = list_directory(tool_input["path"], tool_input.get("recursive", False))
            elif tool_name == "execute_command":
                timeout = tool_input.get("timeout", 300)  # Default to 5 minutes
                result = execute_command(
                    tool_input["command"], tool_input.get("working_dir", "."), timeout
                )
            elif tool_name == "search_files":
                result = search_files(tool_input["pattern"], tool_input.get("path", "."))
            elif tool_name == "get_file_info":
                result = get_file_info(tool_input["path"])
            elif tool_name == "read_files":
                result = read_files(tool_input["paths"])
            elif tool_name == "grep":
                # Handle both 'path' (singular) and 'paths' (plural)
                paths = tool_input.get("paths")
                if paths is None:
                    # If 'paths' not provided, check for 'path' (singular)
                    path = tool_input.get("path")
                    if path is None:
                        return False, "grep requires either 'path' or 'paths' parameter", None
                    paths = [path]
                result = grep(tool_input["pattern"], paths, tool_input.get("flags", ""))
            elif tool_name == "edit_file":
                result = edit_file(
                    tool_input["path"],
                    tool_input["operation"],
                    tool_input.get("content", ""),
                    tool_input.get("pattern", ""),
                    tool_input.get("inherit_indent", True),
                    tool_input.get("start_pattern", ""),
                    tool_input.get("end_pattern", ""),
                )
            elif tool_name == "find_replace":
                result = find_replace(
                    tool_input["pattern"],
                    tool_input["replacement"],
                    tool_input["paths"],
                    tool_input.get("regex", False),
                    tool_input.get("case_sensitive", False),
                    tool_input.get("dry_run", True),
                    tool_input.get("include_patterns", ["*"]),
                    tool_input.get("exclude_patterns", []),
                    tool_input.get("max_file_size", 10485760),
                    tool_input.get("backup", False),
                )
            elif tool_name == "create_directory":
                result = _create_directory_util(tool_input["path"])
            elif tool_name == "delete_file":
                result = _delete_file_util(tool_input["path"])
            elif tool_name == "think":
                result = think(tool_input["thought"])

            else:
                logger.warning(f"Unimplemented tool: {tool_name}")
                return False, f"Unimplemented tool: {tool_name}", None

            # Log result
            success = result[0]
            if success:
                logger.info(f"Tool execution succeeded: {tool_name}")
            else:
                logger.warning(f"Tool execution failed: {tool_name} - {result[1]}")
            return result

        except Exception as e:
            logger.error(f"Exception during tool execution: {tool_name} - {e}", exc_info=True)
            return False, f"Error executing {tool_name}: {str(e)}", None
