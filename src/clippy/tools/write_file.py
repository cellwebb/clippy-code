"""Write file tool implementation."""

from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write content to a file with automatic validation. Creates and overwrites files. "
            "Validates syntax for: Python, JSON, YAML, XML, HTML, CSS, JS, TS, Markdown. "
            "Use skip_validation for binary files or when validation is not desired."
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
                    "description": "Skip validation for binary files, minified code, or errors",
                    "default": False,
                },
            },
            "required": ["path", "content"],
        },
    },
}


def write_file(path: str, content: str, skip_validation: bool = False) -> tuple[bool, str, Any]:
    """Write to a file with built-in validation.

    This function automatically validates syntax for supported file types.
    Use skip_validation=True for binary files or when writing files with intentional syntax errors.
    """
    try:
        # Skip validation if explicitly requested
        if not skip_validation:
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
        msg = f"Permission denied: Cannot write to {path}. Check permissions."
        return False, msg, None
    except OSError as e:
        msg = f"File system error: {str(e)} | Check disk space and path"
        return False, msg, None
    except Exception as e:
        return False, f"Unexpected error writing {path}: {str(e)}", None
