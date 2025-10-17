"""Utility functions for the ClippyAgent."""

import ast
import os
from typing import Any

from ..diff_utils import generate_diff


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

        elif tool_name == "edit_file":
            filepath = tool_input.get("path")
            if not filepath:
                return None

            # Read current file content
            if not os.path.exists(filepath):
                return None  # Can't preview edit on non-existent file

            try:
                with open(filepath, encoding="utf-8") as f:
                    old_content = f.read()
            except Exception:
                return None  # Can't read file for preview

            # Extract edit operation parameters from tool_input
            operation = tool_input.get("operation")
            if not operation:
                return None

            # Import edit_file tool to simulate the operation
            from ..tools.edit_file import apply_edit_operation

            try:
                # Extract all operation parameters from tool_input
                content = tool_input.get("content", "")
                pattern = tool_input.get("pattern", "")
                match_pattern_line = tool_input.get("match_pattern_line", True)
                inherit_indent = tool_input.get("inherit_indent", True)

                # Apply the edit operation to get the new content
                success, _, new_content = apply_edit_operation(
                    old_content, operation, content, pattern, match_pattern_line, inherit_indent
                )
                if success and new_content:
                    # Generate diff between old and new content
                    return generate_diff(old_content, new_content, filepath)
            except Exception:
                # If simulation fails, we can't generate preview
                return None

        return None
    except Exception:
        # If diff generation fails, we'll just proceed without it
        return None
