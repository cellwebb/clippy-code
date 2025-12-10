"""Main ActionExecutor class that coordinates all operations."""

import logging
from pathlib import Path
from typing import Any

from .agent.command_safety_checker import CommandSafetyChecker, create_safety_checker
from .mcp.naming import is_mcp_tool, parse_mcp_qualified_name
from .permissions import TOOL_ACTION_MAP, PermissionManager
from .settings import get_settings

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
from .tools.result import ToolResult
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


# Tool dispatch table for better maintainability
# Each handler returns ToolResult format
def _handle_read_file(tool_input: dict[str, Any]) -> ToolResult:
    """Handle read_file tool execution."""
    success, message, data = read_file(tool_input["path"])
    return ToolResult(success=success, message=message, data=data)


def _handle_write_file(tool_input: dict[str, Any], allowed_roots: list[Path] | None) -> ToolResult:
    """Handle write_file tool execution."""
    # Validate path is within allowed roots
    is_valid, error = validate_write_path(tool_input["path"], allowed_roots)
    if not is_valid:
        return ToolResult(success=False, message=error, data=None)
    success, message, data = write_file(
        tool_input["path"],
        tool_input["content"],
        tool_input.get("skip_validation", False),
    )
    return ToolResult(success=success, message=message, data=data)


def _handle_list_directory(tool_input: dict[str, Any]) -> ToolResult:
    """Handle list_directory tool execution."""
    success, message, data = list_directory(tool_input["path"], tool_input.get("recursive", False))
    return ToolResult(success=success, message=message, data=data)


def _handle_execute_command(tool_input: dict[str, Any], safety_checker: Any = None) -> ToolResult:
    """Handle execute_command tool execution."""
    command = tool_input["command"]
    working_dir = tool_input.get("working_dir", ".")

    # Use safety checker if available
    if safety_checker is not None:
        try:
            is_safe, safety_reason = safety_checker.check_command_safety(command, working_dir)
            if not is_safe:
                return ToolResult(
                    success=False,
                    message=f"Command blocked by safety agent: {safety_reason}",
                    data=None,
                )
            logger.debug(f"Command passed safety check: {safety_reason}")
        except Exception as e:
            logger.error(f"Safety check failed, blocking command: {e}")
            return ToolResult(success=False, message=f"Safety check failed: {str(e)}", data=None)

    timeout = tool_input.get("timeout", DEFAULT_COMMAND_TIMEOUT)
    settings = get_settings()
    show_output = tool_input.get("show_output", settings.show_command_output)
    success, message, data = execute_command(command, working_dir, timeout, show_output)
    return ToolResult(success=success, message=message, data=data)


def _handle_search_files(tool_input: dict[str, Any]) -> ToolResult:
    """Handle search_files tool execution."""
    success, message, data = search_files(tool_input["pattern"], tool_input.get("path", "."))
    return ToolResult(success=success, message=message, data=data)


def _handle_get_file_info(tool_input: dict[str, Any]) -> ToolResult:
    """Handle get_file_info tool execution."""
    success, message, data = get_file_info(tool_input["path"])
    return ToolResult(success=success, message=message, data=data)


def _handle_read_files(tool_input: dict[str, Any]) -> ToolResult:
    """Handle read_files tool execution."""
    # Handle both 'path' (singular) and 'paths' (plural)
    paths = tool_input.get("paths")
    if paths is None:
        path = tool_input.get("path")
        if path is None:
            return ToolResult(
                success=False,
                message="read_files requires either 'path' or 'paths' parameter",
                data=None,
            )
        paths = [path] if isinstance(path, str) else path
    success, message, data = read_files(paths)
    return ToolResult(success=success, message=message, data=data)


def _handle_read_lines(tool_input: dict[str, Any]) -> ToolResult:
    """Handle read_lines tool execution."""
    success, message, data = read_lines(
        tool_input["path"],
        tool_input["line_range"],
        tool_input.get("numbering", "auto"),
        tool_input.get("context", 0),
        tool_input.get("show_line_numbers", True),
        tool_input.get("max_lines", 100),
    )
    return ToolResult(success=success, message=message, data=data)


def _handle_grep(tool_input: dict[str, Any]) -> ToolResult:
    """Handle grep tool execution."""
    # Handle both 'path' (singular) and 'paths' (plural)
    paths = tool_input.get("paths")
    if paths is None:
        path = tool_input.get("path")
        if path is None:
            return ToolResult(
                success=False, message="grep requires either 'path' or 'paths' parameter", data=None
            )
        paths = [path] if isinstance(path, str) else path
    success, message, data = grep(tool_input["pattern"], paths, tool_input.get("flags", ""))
    return ToolResult(success=success, message=message, data=data)


def _handle_edit_file(tool_input: dict[str, Any], allowed_roots: list[Path] | None) -> ToolResult:
    """Handle edit_file tool execution."""
    # Validate path is within allowed roots
    is_valid, error = validate_write_path(tool_input["path"], allowed_roots)
    if not is_valid:
        return ToolResult(success=False, message=error, data=None)
    success, message, data = edit_file(
        tool_input["path"],
        tool_input["operation"],
        tool_input.get("content", ""),
        tool_input.get("pattern", ""),
        tool_input.get("inherit_indent", True),
        tool_input.get("start_pattern", ""),
        tool_input.get("end_pattern", ""),
    )
    return ToolResult(success=success, message=message, data=data)


def _handle_find_replace(
    tool_input: dict[str, Any], allowed_roots: list[Path] | None
) -> ToolResult:
    """Handle find_replace tool execution."""
    # Handle both 'path' (singular) and 'paths' (plural)
    paths = tool_input.get("paths")
    if paths is None:
        path = tool_input.get("path")
        if path is None:
            return ToolResult(
                success=False,
                message="find_replace requires either 'path' or 'paths' parameter",
                data=None,
            )
        paths = [path] if isinstance(path, str) else path
    # Validate paths when not in dry_run mode
    if not tool_input.get("dry_run", True):
        is_valid, error = validate_write_paths(paths, allowed_roots)
        if not is_valid:
            return ToolResult(success=False, message=error, data=None)
    success, message, data = find_replace(
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
    return ToolResult(success=success, message=message, data=data)


def _handle_create_directory(
    tool_input: dict[str, Any], allowed_roots: list[Path] | None
) -> ToolResult:
    """Handle create_directory tool execution."""
    # Validate path is within allowed roots
    is_valid, error = validate_write_path(tool_input["path"], allowed_roots)
    if not is_valid:
        return ToolResult(success=False, message=error, data=None)
    success, message, data = _create_directory_util(tool_input["path"])
    return ToolResult(success=success, message=message, data=data)


def _handle_delete_file(tool_input: dict[str, Any], allowed_roots: list[Path] | None) -> ToolResult:
    """Handle delete_file tool execution."""
    # Validate path is within allowed roots
    is_valid, error = validate_write_path(tool_input["path"], allowed_roots)
    if not is_valid:
        return ToolResult(success=False, message=error, data=None)
    success, message, data = _delete_file_util(tool_input["path"])
    return ToolResult(success=success, message=message, data=data)


def _handle_think(tool_input: dict[str, Any]) -> ToolResult:
    """Handle think tool execution."""
    success, message, data = think(tool_input["thought"])
    return ToolResult(success=success, message=message, data=data)


def _handle_fetch_webpage(tool_input: dict[str, Any]) -> ToolResult:
    """Handle fetch_webpage tool execution."""
    success, message, data = fetch_webpage(
        tool_input["url"],
        tool_input.get("timeout", 30),
        tool_input.get("headers"),
        tool_input.get("mode", "raw"),
        tool_input.get("max_length"),
    )
    return ToolResult(success=success, message=message, data=data)


# Tool dispatch table for better maintainability
# Maps tool names to their handler functions
def _build_tool_handlers(safety_checker: Any = None) -> dict[str, Any]:
    """Build tool handlers with optional safety checker."""
    return {
        "read_file": lambda tool_input, allowed_roots: _handle_read_file(tool_input),
        "write_file": lambda tool_input, allowed_roots: _handle_write_file(
            tool_input, allowed_roots
        ),
        "list_directory": lambda tool_input, allowed_roots: _handle_list_directory(tool_input),
        "execute_command": lambda tool_input, allowed_roots: _handle_execute_command(
            tool_input, safety_checker
        ),
        "search_files": lambda tool_input, allowed_roots: _handle_search_files(tool_input),
        "get_file_info": lambda tool_input, allowed_roots: _handle_get_file_info(tool_input),
        "read_files": lambda tool_input, allowed_roots: _handle_read_files(tool_input),
        "read_lines": lambda tool_input, allowed_roots: _handle_read_lines(tool_input),
        "grep": lambda tool_input, allowed_roots: _handle_grep(tool_input),
        "edit_file": lambda tool_input, allowed_roots: _handle_edit_file(tool_input, allowed_roots),
        "find_replace": lambda tool_input, allowed_roots: _handle_find_replace(
            tool_input, allowed_roots
        ),
        "create_directory": lambda tool_input, allowed_roots: _handle_create_directory(
            tool_input, allowed_roots
        ),
        "delete_file": lambda tool_input, allowed_roots: _handle_delete_file(
            tool_input, allowed_roots
        ),
        "think": lambda tool_input, allowed_roots: _handle_think(tool_input),
        "fetch_webpage": lambda tool_input, allowed_roots: _handle_fetch_webpage(tool_input),
    }


# Default handlers without safety checker (for backward compatibility)
_TOOL_HANDLERS = _build_tool_handlers()


class ActionExecutor:
    """Executes actions with permission checking."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        allowed_write_roots: list[Path] | None = None,
        llm_provider: Any = None,
    ):
        """Initialize the executor.

        Args:
            permission_manager: Permission manager for checking action permissions
            allowed_write_roots: Additional directories where write operations are allowed.
                By default, only the current working directory is allowed.
                Set to include temp directories for testing.
            llm_provider: LLM provider for command safety checking. If None, safety
                checking is disabled and only basic pattern matching is used.
        """
        self.permission_manager = permission_manager
        self._mcp_manager = None
        self._allowed_write_roots = allowed_write_roots
        self._safety_checker: CommandSafetyChecker | None = None

        # Create safety checker with cache settings
        settings = get_settings()
        if llm_provider and settings.safety_checker_enabled:
            if settings.safety_cache_enabled:
                self._safety_checker = create_safety_checker(
                    llm_provider,
                    cache_size=settings.safety_cache_size,
                    cache_ttl=settings.safety_cache_ttl,
                )
            else:
                self._safety_checker = create_safety_checker(
                    llm_provider,
                    cache_size=0,  # Disable cache
                    cache_ttl=0,
                )
        else:
            self._safety_checker = None

        if self._safety_checker:
            self._tool_handlers = _build_tool_handlers(self._safety_checker)
        else:
            self._tool_handlers = _build_tool_handlers(None)

    def set_mcp_manager(self, manager: Any | None) -> None:
        """Set the MCP manager for handling MCP tool calls.

        Args:
            manager: MCPManager instance or None to disable MCP
        """
        self._mcp_manager = manager

    def set_llm_provider(self, llm_provider: Any) -> None:
        """Set the LLM provider for safety checking.

        Args:
            llm_provider: LLM provider instance for command safety checking
        """
        # Use cache settings
        settings = get_settings()
        if llm_provider and settings.safety_checker_enabled:
            if settings.safety_cache_enabled:
                self._safety_checker = create_safety_checker(
                    llm_provider,
                    cache_size=settings.safety_cache_size,
                    cache_ttl=settings.safety_cache_ttl,
                )
            else:
                self._safety_checker = create_safety_checker(
                    llm_provider,
                    cache_size=0,  # Disable cache
                    cache_ttl=0,
                )
        else:
            self._safety_checker = None

        self._tool_handlers = _build_tool_handlers(self._safety_checker)

        if self._safety_checker:
            logger.info("LLM provider set for command safety checking")
        else:
            logger.info("LLM provider set but safety checking is disabled")

    def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        bypass_trust_check: bool = False,
    ) -> tuple[
        bool, str, Any
    ]:  # Note: Returns tuple for compatibility, but internally uses ToolResult
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
            except (ConnectionError, RuntimeError, ValueError, KeyError, TimeoutError) as e:
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

        # Execute the action using dispatch table
        logger.debug(f"Executing built-in tool: {tool_name}")
        try:
            handler = self._tool_handlers.get(tool_name)
            if handler is None:
                logger.warning(f"Unimplemented tool: {tool_name}")
                return False, f"Unimplemented tool: {tool_name}", None

            result = handler(tool_input, self._allowed_write_roots)

            # Log result
            if result.success:
                logger.info(f"Tool execution succeeded: {tool_name}")
            else:
                logger.warning(f"Tool execution failed: {tool_name} - {result.message}")
            return (result.success, result.message, result.data)

        except (RuntimeError, ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error(f"Exception during tool execution: {tool_name} - {e}", exc_info=True)
            return False, f"Error executing {tool_name}: {str(e)}", None
