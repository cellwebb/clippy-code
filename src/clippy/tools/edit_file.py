"""Edit file tool implementation."""

from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Edit a file by inserting, replacing, deleting, or appending content. "
            "Uses pattern-anchored operations for safer editing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to edit"},
                "operation": {
                    "type": "string",
                    "description": (
                        "The edit operation to perform: 'replace', 'delete', 'append', "
                        "'insert_before', or 'insert_after'"
                    ),
                    "enum": ["replace", "delete", "append", "insert_before", "insert_after"],
                },
                "content": {
                    "type": "string",
                    "description": "Content to insert, replace with, or append",
                },
                "pattern": {
                    "type": "string",
                    "description": (
                        "Pattern to match lines for all operations (required for replace, "
                        "delete, insert_before, insert_after). This pattern must match "
                        "exactly one line in the file for replace, delete, insert_before, "
                        "and insert_after operations. For delete, insert_before, and "
                        "insert_after operations, the pattern matches whole lines by "
                        "default (match_pattern_line=true). For replace operations with "
                        "match_pattern_line=false, the pattern can match substrings "
                        "within lines (required for replace, delete, insert_before, "
                        "insert_after)"
                    ),
                },
                "match_pattern_line": {
                    "type": "boolean",
                    "description": (
                        "Whether to match the pattern against entire lines (true) or "
                        "just substrings (false)"
                    ),
                    "default": True,
                },
                "inherit_indent": {
                    "type": "boolean",
                    "description": (
                        "For insert_before/insert_after operations, whether to copy "
                        "leading whitespace from the anchor line to the inserted content"
                    ),
                    "default": True,
                },
            },
            "required": ["path", "operation"],
        },
    },
}


def _detect_eol(content: str) -> str:
    """Detect the dominant EOL style in content."""
    if "\r\n" in content:
        return "\r\n"
    return "\n"


def _normalize_content(content: str, eol: str) -> str:
    """Normalize content to use the specified EOL and ensure trailing EOL."""
    normalized = content.replace("\r\n", "\n").replace("\n", eol)
    if normalized and not normalized.endswith(eol):
        normalized += eol
    return normalized


def _find_matching_lines(lines: list[str], pattern: str, match_pattern_line: bool) -> list[int]:
    """Find all lines matching the pattern."""
    matching_indices = []
    for i, line in enumerate(lines):
        if match_pattern_line:
            # Full line equality match (remove EOL for comparison)
            if line.rstrip("\r\n") == pattern:
                matching_indices.append(i)
        else:
            # Substring match (case insensitive)
            if pattern.lower() in line.lower():
                matching_indices.append(i)
    return matching_indices


def _get_leading_whitespace(line: str) -> str:
    """Extract leading whitespace from a line."""
    whitespace = ""
    for char in line:
        if char in " \t":
            whitespace += char
        else:
            break
    return whitespace


def _apply_indent(content: str, leading_whitespace: str, eol: str) -> str:
    """Apply indentation to multi-line content."""
    content_lines = content.replace("\r\n", "\n").split("\n")
    # Filter out empty strings at the end
    while content_lines and content_lines[-1] == "":
        content_lines.pop()

    indented_lines = []
    for line in content_lines:
        if line.strip():  # Don't indent empty lines
            indented_lines.append(leading_whitespace + line)
        else:
            indented_lines.append(line)

    return eol.join(indented_lines)


def apply_edit_operation(
    original_content: str,
    operation: str,
    content: str = "",
    pattern: str = "",
    match_pattern_line: bool = True,
    inherit_indent: bool = True,
) -> tuple[bool, str, str | None]:
    """
    Apply an edit operation to content and return the result.

    This function is used both for executing edits and generating previews.

    Args:
        original_content: The original file content
        operation: The edit operation to perform
        content: Content to insert, replace with, or append
        pattern: Pattern to match lines for operations
        match_pattern_line: Whether to match the pattern against entire lines
        inherit_indent: For insert operations, whether to copy leading whitespace

    Returns:
        Tuple of (success: bool, message: str, new_content: str | None)
    """
    try:
        eol = _detect_eol(original_content)
        lines = original_content.splitlines(keepends=True)

        # Handle different operations
        if operation == "replace":
            if not pattern:
                return False, "Pattern is required for replace operation", None

            matching_indices = _find_matching_lines(lines, pattern, match_pattern_line)
            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times, "
                    "expected exactly one match",
                    None,
                )

            idx = matching_indices[0]

            if match_pattern_line:
                # Full line replacement
                lines[idx] = _normalize_content(content, eol)
            else:
                # Substring replacement
                line_without_eol = lines[idx].rstrip("\r\n")
                lower_line = line_without_eol.lower()
                start_pos = lower_line.find(pattern.lower())
                if start_pos == -1:
                    return False, f"Pattern '{pattern}' not found in line during replacement", None

                end_pos = start_pos + len(pattern)
                new_line = line_without_eol[:start_pos] + content + line_without_eol[end_pos:]
                lines[idx] = new_line + eol

        elif operation == "delete":
            if not pattern:
                return False, "Pattern is required for delete operation", None

            matching_indices = _find_matching_lines(lines, pattern, match_pattern_line)
            if not matching_indices:
                return False, f"Pattern '{pattern}' not found in file", None

            # Delete in reverse order to avoid index shifting
            for i in reversed(matching_indices):
                lines.pop(i)

        elif operation == "append":
            normalized_content = _normalize_content(content, eol)

            # Add EOL to last line if needed and content doesn't start with EOL
            last_line_needs_eol = (
                lines
                and lines[-1]
                and not lines[-1].endswith(eol)
                and not normalized_content.startswith(eol)
            )
            if last_line_needs_eol:
                lines[-1] = lines[-1].rstrip("\r\n") + eol

            lines.append(normalized_content)

        elif operation in ["insert_before", "insert_after"]:
            if not pattern:
                return False, f"Pattern is required for {operation} operation", None

            matching_indices = _find_matching_lines(lines, pattern, match_pattern_line)
            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times, "
                    "expected exactly one match",
                    None,
                )

            idx = matching_indices[0] if operation == "insert_before" else matching_indices[0] + 1

            # Prepare content with optional indentation
            if inherit_indent:
                leading_ws = _get_leading_whitespace(lines[matching_indices[0]])
                normalized_content = _apply_indent(content, leading_ws, eol)
            else:
                normalized_content = content.replace("\r\n", "\n").replace("\n", eol)

            normalized_content = _normalize_content(normalized_content, eol)
            lines.insert(idx, normalized_content)

        else:
            return False, f"Unknown operation: {operation}", None

        # Return the new content
        new_content = "".join(lines)
        return True, f"Successfully performed {operation} operation", new_content

    except Exception as e:
        return False, f"Failed to apply edit: {str(e)}", None


def edit_file(
    path: str,
    operation: str,
    content: str = "",
    pattern: str = "",
    match_pattern_line: bool = True,
    inherit_indent: bool = True,
) -> tuple[bool, str, Any]:
    """Edit a file with pattern-anchored operations."""
    try:
        # Read current file content
        # Use newline='' to preserve original line endings (CRLF vs LF)
        try:
            with open(path, encoding="utf-8", newline="") as f:
                original_content = f.read()
        except FileNotFoundError:
            return False, f"File not found: {path}", None

        # Apply the edit operation using the helper function
        success, message, new_content = apply_edit_operation(
            original_content, operation, content, pattern, match_pattern_line, inherit_indent
        )

        if not success or new_content is None:
            return success, message, None

        # Write back to file
        # Use newline='' to preserve the line endings we constructed
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_content)

        # Validate that the file wasn't corrupted by the edit
        try:
            with open(path, encoding="utf-8") as f:
                validation_content = f.read()
            # Basic validation - check that we can still parse it as lines
            _ = validation_content.splitlines(keepends=True)
        except Exception as validation_error:
            # If validation fails, restore the original content
            with open(path, "w", encoding="utf-8") as f:
                f.write(original_content)
            return (
                False,
                f"Edit caused file corruption. Reverted changes. Error: {str(validation_error)}",
                None,
            )

        return True, message, None

    except PermissionError:
        return False, f"Permission denied when editing: {path}", None
    except Exception as e:
        return False, f"Failed to edit {path}: {str(e)}", None
