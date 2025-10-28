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
    Generate a diff preview for file operations, including MCP tools.

    Args:
        tool_name: Name of the tool being executed
        tool_input: Tool input parameters

    Returns:
        Diff content as string, or None if not applicable or if an error occurred
    """
    try:
        # Check if this is an MCP tool that might affect files
        is_mcp = tool_name.startswith("mcp__")

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
            return generate_diff(old_content, new_content, filepath, context=1)

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
                inherit_indent = tool_input.get("inherit_indent", True)
                start_pattern = tool_input.get("start_pattern", "")
                end_pattern = tool_input.get("end_pattern", "")

                # Apply the edit operation to get the new content
                success, _, new_content = apply_edit_operation(
                    old_content,
                    operation,
                    content,
                    pattern,
                    inherit_indent,
                    start_pattern,
                    end_pattern,
                )
                if success and new_content:
                    # Generate diff between old and new content
                    return generate_diff(old_content, new_content, filepath, context=1)
            except Exception:
                # If simulation fails, we can't generate preview
                return None

        elif is_mcp:
            # For MCP tools, try to detect file operations by analyzing tool_input
            # Look for common file operation patterns in MCP tool parameters
            file_operations = _detect_mcp_file_operations(tool_input)

            if file_operations:
                # Generate a summary diff for MCP file operations
                return _generate_mcp_diff_summary(tool_name, file_operations, tool_input)

        return None
    except Exception:
        # If diff generation fails, we'll just proceed without it
        return None


def _detect_mcp_file_operations(tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Detect if MCP tool input contains file operations.

    Args:
        tool_input: MCP tool input parameters

    Returns:
        Dictionary with file operation details or empty dict if none detected
    """
    file_ops = {}

    # Look for common file operation parameter names
    file_params = ["path", "file", "filepath", "filename", "directory", "folder"]
    content_params = ["content", "text", "data", "code"]

    for key, value in tool_input.items():
        key_lower = key.lower()

        # Detect file path
        if any(param in key_lower for param in file_params):
            file_ops["path"] = str(value)

        # Detect content
        if any(param in key_lower for param in content_params):
            file_ops["content"] = str(value)

    # Only return file operations if we found at least a path
    if "path" in file_ops:
        return file_ops

    return {}


def _generate_mcp_diff_summary(
    tool_name: str, file_ops: dict[str, Any], tool_input: dict[str, Any]
) -> str:
    """
    Generate a summary diff for MCP file operations.

    Args:
        tool_name: MCP tool name
        file_ops: Detected file operations
        tool_input: Original tool input

    Returns:
        Summary diff as string
    """
    filepath = file_ops.get("path", "unknown")
    content = file_ops.get("content", "")

    # Try to read existing file content
    old_content = ""
    if os.path.exists(filepath):
        try:
            with open(filepath, encoding="utf-8") as f:
                old_content = f.read()
        except Exception:
            old_content = "[Could not read existing file content]"

    # Generate a summary diff
    diff_lines = []
    diff_lines.append("--- MCP Tool File Operation Summary ---")
    diff_lines.append(f"Tool: {tool_name}")
    diff_lines.append(f"File: {filepath}")

    if content:
        diff_lines.append(f"Operation: Write/Update content ({len(content)} characters)")
        if old_content:
            diff_lines.append(f"Existing file: {len(old_content)} characters")
            if len(content) != len(old_content):
                size_change = len(content) - len(old_content)
                diff_lines.append(f"Size change: {size_change:+d} characters")
        else:
            diff_lines.append("Existing file: None (new file)")
    else:
        diff_lines.append("Operation: Read/Access file")
        if old_content:
            diff_lines.append(f"Existing file: {len(old_content)} characters")
        else:
            diff_lines.append("Existing file: None")

    # Show first few lines of content if available
    if content and len(content) > 0:
        content_lines = content.split("\n")
        preview_lines = min(5, len(content_lines))
        diff_lines.append("Content preview:")
        for i in range(preview_lines):
            diff_lines.append(f"+ {content_lines[i]}")
        if len(content_lines) > preview_lines:
            diff_lines.append(f"... and {len(content_lines) - preview_lines} more lines")

    return "\n".join(diff_lines)
