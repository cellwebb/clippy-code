"""Delete file tool implementation."""

import os
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
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
}


def delete_file(path: str) -> tuple[bool, str, Any]:
    """Delete a file."""
    try:
        os.remove(path)
        return True, f"Successfully deleted {path}", None
    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except PermissionError:
        return False, f"Permission denied when deleting: {path}", None
    except OSError as e:
        return False, f"OS error when deleting {path}: {str(e)}", None
    except Exception as e:
        return False, f"Failed to delete {path}: {str(e)}", None
