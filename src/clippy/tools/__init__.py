"""Tools module for tool implementations."""

from typing import Any

from .create_directory import TOOL_SCHEMA as CREATE_DIRECTORY_SCHEMA
from .create_directory import create_directory
from .delete_file import TOOL_SCHEMA as DELETE_FILE_SCHEMA
from .delete_file import delete_file
from .edit_file import TOOL_SCHEMA as EDIT_FILE_SCHEMA
from .edit_file import edit_file
from .execute_command import TOOL_SCHEMA as EXECUTE_COMMAND_SCHEMA
from .execute_command import execute_command
from .get_file_info import TOOL_SCHEMA as GET_FILE_INFO_SCHEMA
from .get_file_info import get_file_info
from .grep import TOOL_SCHEMA as GREP_SCHEMA
from .grep import grep, translate_grep_flags_to_rg
from .list_directory import TOOL_SCHEMA as LIST_DIRECTORY_SCHEMA
from .list_directory import list_directory
from .read_file import TOOL_SCHEMA as READ_FILE_SCHEMA
from .read_file import read_file
from .read_files import TOOL_SCHEMA as READ_FILES_SCHEMA
from .read_files import read_files
from .search_files import TOOL_SCHEMA as SEARCH_FILES_SCHEMA
from .search_files import search_files
from .write_file import TOOL_SCHEMA as WRITE_FILE_SCHEMA
from .write_file import write_file

# Aggregate all tool schemas into a single list
TOOLS: list[dict[str, Any]] = [
    CREATE_DIRECTORY_SCHEMA,
    DELETE_FILE_SCHEMA,
    EDIT_FILE_SCHEMA,
    EXECUTE_COMMAND_SCHEMA,
    GET_FILE_INFO_SCHEMA,
    GREP_SCHEMA,
    LIST_DIRECTORY_SCHEMA,
    READ_FILE_SCHEMA,
    READ_FILES_SCHEMA,
    SEARCH_FILES_SCHEMA,
    WRITE_FILE_SCHEMA,
]


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Get a tool definition by name."""
    for tool in TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None


__all__ = [
    "create_directory",
    "delete_file",
    "edit_file",
    "execute_command",
    "get_file_info",
    "grep",
    "translate_grep_flags_to_rg",
    "list_directory",
    "read_file",
    "read_files",
    "search_files",
    "write_file",
    "TOOLS",
    "get_tool_by_name",
]
