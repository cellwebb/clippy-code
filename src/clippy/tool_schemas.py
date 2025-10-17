"""Tool definitions for OpenAI-compatible APIs.

This module aggregates tool schemas from individual tool implementations.
Each tool schema is now co-located with its implementation in the tools/ directory.
"""

from typing import Any

from .tools.create_directory import TOOL_SCHEMA as CREATE_DIRECTORY_SCHEMA
from .tools.delete_file import TOOL_SCHEMA as DELETE_FILE_SCHEMA
from .tools.edit_file import TOOL_SCHEMA as EDIT_FILE_SCHEMA
from .tools.execute_command import TOOL_SCHEMA as EXECUTE_COMMAND_SCHEMA
from .tools.get_file_info import TOOL_SCHEMA as GET_FILE_INFO_SCHEMA
from .tools.grep import TOOL_SCHEMA as GREP_SCHEMA
from .tools.list_directory import TOOL_SCHEMA as LIST_DIRECTORY_SCHEMA
from .tools.read_file import TOOL_SCHEMA as READ_FILE_SCHEMA
from .tools.read_files import TOOL_SCHEMA as READ_FILES_SCHEMA
from .tools.search_files import TOOL_SCHEMA as SEARCH_FILES_SCHEMA
from .tools.write_file import TOOL_SCHEMA as WRITE_FILE_SCHEMA

# Aggregate all tool schemas into a single list
TOOLS: list[dict[str, Any]] = [
    READ_FILE_SCHEMA,
    WRITE_FILE_SCHEMA,
    DELETE_FILE_SCHEMA,
    LIST_DIRECTORY_SCHEMA,
    CREATE_DIRECTORY_SCHEMA,
    EXECUTE_COMMAND_SCHEMA,
    SEARCH_FILES_SCHEMA,
    GET_FILE_INFO_SCHEMA,
    READ_FILES_SCHEMA,
    GREP_SCHEMA,
    EDIT_FILE_SCHEMA,
]


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Get a tool definition by name."""
    for tool in TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None
