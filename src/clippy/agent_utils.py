"""Utility functions for the ClippyAgent."""

import ast
import os
import tempfile
from pathlib import Path
from typing import Any

from .diff_utils import generate_diff


def validate_python_syntax(content: str, filepath: str) -> tuple[bool, str]:
    """
    Validate Python syntax for a file.

    Args:
        content: The file content to validate
        filepath: The path to the file (for error messages)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if filepath.endswith(".py"):
        try:
            ast.parse(content)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error in {filepath}: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Error validating Python syntax in {filepath}: {str(e)}"
    return True, ""


def safe_write_file(path: str, content: str) -> tuple[bool, str]:
    """
    Safely write a file with validation.

    Args:
        path: Path to the file
        content: Content to write

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Validate Python syntax if it's a Python file
        is_valid, error_msg = validate_python_syntax(content, path)
        if not is_valid:
            return False, error_msg

        # Create parent directories if needed
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=Path(path).parent) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # If we get here, the write was successful
        # Move temporary file to final location
        os.replace(tmp_path, path)
        return True, f"Successfully wrote to {path}"
    except Exception as e:
        # Clean up temp file if it exists
        try:
            if "tmp_path" in locals():
                os.unlink(tmp_path)
        except OSError:
            pass
        return False, f"Failed to write to {path}: {str(e)}"


def generate_preview_diff(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    """
    Generate a diff preview for file operations.

    Args:
        tool_name: Name of the tool being executed
        tool_input: Tool input parameters

    Returns:
        Diff content as string, or None if not applicable or if an error occurred
    """
    try:
        if tool_name == "write_file":
            filepath = tool_input["path"]
            new_content = tool_input["content"]

            # Read existing content if file exists
            old_content = ""
            if os.path.exists(filepath):
                try:
                    with open(filepath, encoding="utf-8") as f:
                        old_content = f.read()
                except Exception:
                    old_content = "[Could not read existing file content]"

            # Generate diff
            return generate_diff(old_content, new_content, filepath)
        return None
    except Exception:
        # If diff generation fails, we'll just proceed without it
        return None
