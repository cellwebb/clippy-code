"""Get file info tool implementation."""

import os
from datetime import datetime
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
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
}


def get_file_info(path: str) -> tuple[bool, str, Any]:
    """Get file metadata."""
    try:
        stat = os.stat(path)
        info = {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "is_directory": os.path.isdir(path),
            "is_file": os.path.isfile(path),
        }

        # Format the info as a string to match test expectations
        info_str = "\n".join([f"{key}: {value}" for key, value in info.items()])
        return True, f"Successfully retrieved file info for {path}", info_str
    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except PermissionError:
        return False, f"Permission denied when getting info for: {path}", None
    except Exception as e:
        return False, f"Failed to get file info for {path}: {str(e)}", None
