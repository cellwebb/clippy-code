"""Read file tool implementation."""

from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file. Use this to examine existing code or files.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to read"}
            },
            "required": ["path"],
        },
    },
}


def read_file(path: str) -> tuple[bool, str, Any]:
    """Read a file."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        return True, f"Successfully read {path}", content
    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except PermissionError:
        return False, f"Permission denied when reading: {path}", None
    except UnicodeDecodeError:
        return False, f"Unable to decode file (might be binary): {path}", None
    except Exception as e:
        return False, f"Failed to read {path}: {str(e)}", None
