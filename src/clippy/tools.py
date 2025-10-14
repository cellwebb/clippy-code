"""Tool definitions for OpenAI-compatible APIs."""

from typing import Any

# Tool definitions in OpenAI format
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Use this to examine existing "
            "code or files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file to read"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates the file if it doesn't "
            "exist, overwrites if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file to write"},
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file. Use with caution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file to delete"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List the contents of a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the directory to list. Defaults to "
                        "current directory.",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to list recursively. Defaults to false.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Create a new directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the directory to create"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command. Use with caution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"},
                    "working_dir": {
                        "type": "string",
                        "description": "The working directory for the command. Defaults to "
                        "current directory.",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a pattern (supports glob patterns "
            "like *.py).",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The glob pattern to search for (e.g., '*.py', "
                        "'src/**/*.ts')",
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory to search in. Defaults to current directory.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_info",
            "description": "Get metadata about a file (size, modification time, etc.).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "The path to the file"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_files",
            "description": "Read the contents of multiple files at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The paths to the files to read",
                    }
                },
                "required": ["paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for patterns in files using grep. "
            "This is a safe read-only operation that requires no approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The pattern to search for in files",
                    },
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The file paths or glob patterns to search in",
                    },
                    "flags": {
                        "type": "string",
                        "description": "Optional flags for grep command (e.g., '-i', '-r', etc.)",
                    },
                },
                "required": ["pattern", "paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by inserting, replacing, or deleting lines. "
            "More efficient than rewriting entire files for small changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file to edit"},
                    "operation": {
                        "type": "string",
                        "description": (
                            "The edit operation to perform: 'insert', 'replace', 'delete', "
                            "or 'append'"
                        ),
                        "enum": ["insert", "replace", "delete", "append"],
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to insert, replace with, or append",
                    },
                    "line_number": {
                        "type": "integer",
                        "description": (
                            "Line number for insert/replace/delete operations (1-indexed)"
                        ),
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to match lines for replace/delete operations",
                    },
                    "match_pattern_line": {
                        "type": "boolean",
                        "description": (
                            "Whether to match the pattern against entire lines (true) or "
                            "just substrings (false)"
                        ),
                        "default": True,
                    },
                },
                "required": ["path", "operation"],
            },
        },
    },
]


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Get a tool definition by name."""
    for tool in TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None
