"""Main ActionExecutor class that coordinates all operations."""

import logging
from pathlib import Path
from typing import Any

from .mcp.naming import is_mcp_tool, parse_mcp_qualified_name
from .permissions import TOOL_ACTION_MAP, PermissionManager

# Import tool functions explicitly to avoid module/function conflicts
from .tools.create_directory import create_directory as _create_directory_util
from .tools.delete_file import delete_file as _delete_file_util
from .tools.edit_file import edit_file
from .tools.execute_command import execute_command
from .tools.fetch_webpage import fetch_webpage
from .tools.find_replace import find_replace
from .tools.get_file_info import get_file_info
from .tools.grep import grep
from .tools.list_directory import list_directory
from .tools.read_file import read_file
from .tools.read_files import read_files
from .tools.read_lines import read_lines
from .tools.search_files import search_files
from .tools.think import think
from .tools.write_file import write_file

logger = logging.getLogger(__name__)
# Execution constants
DEFAULT_COMMAND_TIMEOUT = 60  # 1 minute in seconds (can be overridden via tool_input)


def validate_write_path(path: str, allowed_roots: list[Path] | None = None) -> tuple[bool, str]:
    """Validate that a path is safe for write operations.

    Write operations are restricted to the current working directory and its
    subdirectories (plus any additional allowed roots) to prevent accidental
    modification of system files.

    Args:
        path: The path to validate
        allowed_roots: Additional allowed root directories. If None, only CWD is allowed.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    try:
        # Resolve the path to absolute, following symlinks
        resolved_path = Path(path).resolve()
        cwd = Path.cwd().resolve()

        # Build list of allowed roots
        roots = [cwd]
        if allowed_roots:
            roots.extend(r.resolve() for r in allowed_roots)

        # Check if the resolved path is within any allowed root
        for root in roots:
            try:
                resolved_path.relative_to(root)
                return True, ""
            except ValueError:
                continue

        # Path is outside all allowed roots
        return False, (
            f"Write operations restricted to current directory. "
            f"Path '{path}' resolves outside of '{cwd}'"
        )
    except (OSError, RuntimeError) as e:
        return False, f"Invalid path '{path}': {e}"


def validate_write_paths(
    paths: list[str], allowed_roots: list[Path] | None = None
) -> tuple[bool, str]:
    """Validate multiple paths for write operations.

    Args:
        paths: List of paths to validate
        allowed_roots: Additional allowed root directories

    Returns:
        Tuple of (all_valid, first_error_message)
    """
    for path in paths:
        is_valid, error = validate_write_path(path, allowed_roots)
        if not is_valid:
            return False, error
    return True, ""


class ActionExecutor:
    """Executes actions with permission checking."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        allowed_write_roots: list[Path] | None = None,
    ):
        """Initialize the executor.

        Args:
            permission_manager: Permission manager for checking action permissions
            allowed_write_roots: Additional directories where write operations are allowed.
                By default, only the current working directory is allowed.
                Set to include temp directories for testing.
        """
        self.permission_manager = permission_manager
        self._mcp_manager = None
        self._allowed_write_roots = allowed_write_roots

    def set_mcp_manager(self, manager: Any | None) -> None:
        """Set the MCP manager for handling MCP tool calls.

        Args:
            manager: MCPManager instance or None to disable MCP
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

        # Use centralized tool-to-action mapping
        action_type = TOOL_ACTION_MAP.get(tool_name)
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
                # Validate path is within allowed roots
                is_valid, error = validate_write_path(tool_input["path"], self._allowed_write_roots)
                if not is_valid:
                    return False, error, None
                result = write_file(
                    tool_input["path"],
                    tool_input["content"],
                    tool_input.get("skip_validation", False),
                )
            elif tool_name == "list_directory":
                result = list_directory(tool_input["path"], tool_input.get("recursive", False))
            elif tool_name == "execute_command":
                timeout = tool_input.get("timeout", DEFAULT_COMMAND_TIMEOUT)
                result = execute_command(
                    tool_input["command"], tool_input.get("working_dir", "."), timeout
                )
            elif tool_name == "search_files":
                result = search_files(tool_input["pattern"], tool_input.get("path", "."))
            elif tool_name == "get_file_info":
                result = get_file_info(tool_input["path"])
            elif tool_name == "read_files":
                # Handle both 'path' (singular) and 'paths' (plural)
                paths = tool_input.get("paths")
                if paths is None:
                    path = tool_input.get("path")
                    if path is None:
                        return False, "read_files requires either 'path' or 'paths' parameter", None
                    paths = [path] if isinstance(path, str) else path
                result = read_files(paths)
            elif tool_name == "read_lines":
                result = read_lines(
                    tool_input["path"],
                    tool_input["line_range"],
                    tool_input.get("numbering", "auto"),
                    tool_input.get("context", 0),
                    tool_input.get("show_line_numbers", True),
                    tool_input.get("max_lines", 100),
                )
            elif tool_name == "grep":
                # Handle both 'path' (singular) and 'paths' (plural)
                paths = tool_input.get("paths")
                if paths is None:
                    path = tool_input.get("path")
                    if path is None:
                        return False, "grep requires either 'path' or 'paths' parameter", None
                    paths = [path] if isinstance(path, str) else path
                result = grep(tool_input["pattern"], paths, tool_input.get("flags", ""))
            elif tool_name == "edit_file":
                # Validate path is within allowed roots
                is_valid, error = validate_write_path(tool_input["path"], self._allowed_write_roots)
                if not is_valid:
                    return False, error, None
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
                # Handle both 'path' (singular) and 'paths' (plural)
                paths = tool_input.get("paths")
                if paths is None:
                    path = tool_input.get("path")
                    if path is None:
                        return (
                            False,
                            ("find_replace requires either 'path' or 'paths' parameter"),
                            None,
                        )
                    paths = [path] if isinstance(path, str) else path
                # Validate paths when not in dry_run mode
                if not tool_input.get("dry_run", True):
                    is_valid, error = validate_write_paths(paths, self._allowed_write_roots)
                    if not is_valid:
                        return False, error, None
                result = find_replace(
                    tool_input["pattern"],
                    tool_input["replacement"],
                    paths,
                    tool_input.get("regex", False),
                    tool_input.get("case_sensitive", False),
                    tool_input.get("dry_run", True),
                    tool_input.get("include_patterns", ["*"]),
                    tool_input.get("exclude_patterns", []),
                    tool_input.get("max_file_size", 10485760),
                    tool_input.get("backup", False),
                )
            elif tool_name == "create_directory":
                # Validate path is within allowed roots
                is_valid, error = validate_write_path(tool_input["path"], self._allowed_write_roots)
                if not is_valid:
                    return False, error, None
                result = _create_directory_util(tool_input["path"])
            elif tool_name == "delete_file":
                # Validate path is within allowed roots
                is_valid, error = validate_write_path(tool_input["path"], self._allowed_write_roots)
                if not is_valid:
                    return False, error, None
                result = _delete_file_util(tool_input["path"])
            elif tool_name == "think":
                result = think(tool_input["thought"])
            elif tool_name == "fetch_webpage":
                result = fetch_webpage(
                    tool_input["url"],
                    tool_input.get("timeout", 30),
                    tool_input.get("headers"),
                    tool_input.get("mode", "raw"),
                    tool_input.get("max_length"),
                )

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
