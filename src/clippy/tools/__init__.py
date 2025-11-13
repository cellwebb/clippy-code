"""Tools module for tool implementations."""

from typing import Any

# Utility functions available for internal use but not exposed as tools
from .copy_file import copy_file as _copy_file_util
from .create_directory import create_directory as _create_directory_util
from .delegate_to_subagent import create_subagent_and_execute
from .delegate_to_subagent import get_tool_schema as get_delegate_schema
from .delete_file import delete_file as _delete_file_util
from .edit_file import TOOL_SCHEMA as EDIT_FILE_SCHEMA
from .edit_file import edit_file
from .execute_command import TOOL_SCHEMA as EXECUTE_COMMAND_SCHEMA
from .execute_command import execute_command
from .find_replace import TOOL_SCHEMA as FIND_REPLACE_SCHEMA
from .find_replace import find_replace
from .get_file_info import TOOL_SCHEMA as GET_FILE_INFO_SCHEMA
from .get_file_info import get_file_info
from .grep import TOOL_SCHEMA as GREP_SCHEMA
from .grep import grep, translate_grep_flags_to_rg
from .list_directory import TOOL_SCHEMA as LIST_DIRECTORY_SCHEMA
from .list_directory import list_directory
from .move_file import move_file as _move_file_util
from .read_file import TOOL_SCHEMA as READ_FILE_SCHEMA
from .read_file import read_file
from .read_files import TOOL_SCHEMA as READ_FILES_SCHEMA
from .read_files import read_files
from .search_files import TOOL_SCHEMA as SEARCH_FILES_SCHEMA
from .search_files import search_files
from .think import TOOL_SCHEMA as THINK_SCHEMA
from .think import think
from .write_file import TOOL_SCHEMA as WRITE_FILE_SCHEMA
from .write_file import write_file


def get_all_tools() -> list[dict[str, Any]]:
    """Get all tool schemas, loading delegate tools dynamically to avoid circular imports."""
    base_tools = [
        EDIT_FILE_SCHEMA,
        EXECUTE_COMMAND_SCHEMA,
        FIND_REPLACE_SCHEMA,
        GET_FILE_INFO_SCHEMA,
        GREP_SCHEMA,
        LIST_DIRECTORY_SCHEMA,
        READ_FILE_SCHEMA,
        READ_FILES_SCHEMA,
        SEARCH_FILES_SCHEMA,
        THINK_SCHEMA,
        WRITE_FILE_SCHEMA,
    ]

    # Add delegate_to_subagent schema if available
    try:
        delegate_schema = get_delegate_schema()
        base_tools.append(delegate_schema)
    except Exception:
        # Skip if schema loading fails
        pass

    # Add run_parallel_subagents schema if available
    try:
        from .run_parallel_subagents import get_tool_schema as get_parallel_schema

        parallel_schema = get_parallel_schema()
        base_tools.append(parallel_schema)
    except Exception:
        # Skip if schema loading fails
        pass

    return base_tools


TOOLS = get_all_tools()


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Get a tool definition by name."""
    for tool in TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None


def get_create_subagent_and_execute() -> Any:
    """Get create_subagent_and_execute function dynamically."""
    try:
        from .delegate_to_subagent import create_subagent_and_execute

        return create_subagent_and_execute
    except ImportError:
        return None


def get_create_parallel_subagents_and_execute() -> Any:
    """Get create_parallel_subagents_and_execute function dynamically."""
    try:
        from .run_parallel_subagents import create_parallel_subagents_and_execute

        return create_parallel_subagents_and_execute
    except ImportError:
        return None


__all__ = [
    "create_subagent_and_execute",
    "create_parallel_subagents_and_execute",
    "edit_file",
    "execute_command",
    "find_replace",
    "get_file_info",
    "grep",
    "translate_grep_flags_to_rg",
    "list_directory",
    "read_file",
    "read_files",
    "search_files",
    "think",
    "write_file",
    "TOOLS",
    "get_tool_by_name",
    "get_create_subagent_and_execute",
    "get_create_parallel_subagents_and_execute",
    "_copy_file_util",
    "_move_file_util",
    "_create_directory_util",
    "_delete_file_util",
]
