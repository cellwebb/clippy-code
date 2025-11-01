"""Write file tool implementation."""

from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write content to a file. Creates the file if it doesn't exist, overwrites if it does. "
            "Automatically validates syntax for common file types: Python, JSON, YAML, XML, HTML, "
            "CSS, JS, TS, Markdown, Dockerfile."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to write"},
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                },
                "skip_validation": {
                    "type": "boolean",
                    "description": "Skip file validation (use with caution)",
                    "default": False,
                },
            },
            "required": ["path", "content"],
        },
    },
}


def write_file(path: str, content: str, skip_validation: bool = False) -> tuple[bool, str, Any]:
    """Write to a file with comprehensive validation."""
    # Use direct file I/O to avoid any event loop issues in async contexts (like document mode)
    # This is simpler and more reliable than using tempfile, which can have issues
    # when called from worker threads in an async application
    try:
        # Skip validation if requested
        if not skip_validation:
            # Validate file content based on file type
            from ..file_validators import validate_file_content

            validation_result = validate_file_content(content, path)
            if not validation_result:
                return False, f"File validation failed: {validation_result.message}", None

        # Create parent directories if needed
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Write file directly
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        validation_note = " (validation skipped)" if skip_validation else ""
        return True, f"Successfully wrote to {path}{validation_note}", None
    except PermissionError:
        return False, f"Permission denied when writing: {path}", None
    except OSError as e:
        return False, f"OS error when writing {path}: {str(e)}", None
    except Exception as e:
        return False, f"Failed to write to {path}: {str(e)}", None
