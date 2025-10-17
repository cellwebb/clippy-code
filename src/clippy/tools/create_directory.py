"""Create directory tool implementation."""

from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
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
}


def create_directory(path: str) -> tuple[bool, str, Any]:
    """Create a directory."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True, f"Successfully created directory {path}", None
    except PermissionError:
        return False, f"Permission denied when creating directory: {path}", None
    except OSError as e:
        return False, f"OS error when creating directory {path}: {str(e)}", None
    except Exception as e:
        return False, f"Failed to create directory {path}: {str(e)}", None
