"""Edit file tool implementation."""

import re
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Edit a file by inserting, replacing, deleting, or appending content. "
            "All pattern matching uses regular expressions for maximum flexibility."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to edit"},
                "operation": {
                    "type": "string",
                    "description": (
                        "The edit operation to perform:\n"
                        "- 'replace': Replace content matching a regex pattern "
                        "(must match exactly once)\n"
                        "- 'delete': Delete lines matching a regex pattern "
                        "(can match multiple lines)\n"
                        "- 'append': Add content at the end of the file\n"
                        "- 'insert_before': Insert before a line matching a regex pattern "
                        "(must match exactly once)\n"
                        "- 'insert_after': Insert after a line matching a regex pattern "
                        "(must match exactly once)\n"
                        "- 'block_replace': Replace a multi-line block between start/end regex "
                        "markers\n"
                        "- 'block_delete': Delete a multi-line block between start/end regex "
                        "markers"
                    ),
                    "enum": [
                        "replace",
                        "delete",
                        "append",
                        "insert_before",
                        "insert_after",
                        "block_replace",
                        "block_delete",
                    ],
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Content to insert, replace with, or append. For replace operations, "
                        "can use regex capture groups (\\1, \\2, etc.)"
                    ),
                },
                "pattern": {
                    "type": "string",
                    "description": (
                        "Regular expression pattern to match lines (required for replace, delete, "
                        "insert_before, insert_after). The pattern is searched within each line "
                        "using re.search(). Use anchors (^ for start, $ for end) to match full "
                        "lines. For replace/insert_before/insert_after, the pattern must match "
                        "exactly one line. For delete, can match multiple lines. Use regex_flags "
                        "to control matching behavior (e.g., IGNORECASE, MULTILINE, DOTALL)."
                    ),
                },
                "inherit_indent": {
                    "type": "boolean",
                    "description": (
                        "For insert_before/insert_after operations, whether to copy "
                        "leading whitespace from the anchor line to the inserted content"
                    ),
                    "default": True,
                },
                "start_pattern": {
                    "type": "string",
                    "description": (
                        "Regular expression pattern for block operations (block_replace, "
                        "block_delete). Marks the beginning of the block to target. Searched "
                        "within each line using re.search()."
                    ),
                },
                "end_pattern": {
                    "type": "string",
                    "description": (
                        "Regular expression pattern for block operations (block_replace, "
                        "block_delete). Marks the end of the block to target. Searched within each "
                        "line using re.search()."
                    ),
                },
                "regex_flags": {
                    "type": "array",
                    "description": (
                        "List of regex flags to apply to pattern matching. "
                        "Available flags: 'IGNORECASE', 'MULTILINE', 'DOTALL', 'VERBOSE'. "
                        "Default is [] (no flags). Common usage: ['IGNORECASE'] for "
                        "case-insensitive matching, ['MULTILINE', 'DOTALL'] for multi-line pattern "
                        "matching."
                    ),
                    "items": {"type": "string"},
                    "default": [],
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


def _find_matching_lines(lines: list[str], pattern: str, flags: int) -> list[int]:
    """
    Find all lines matching the regex pattern.

    Args:
        lines: List of file lines (with EOL)
        pattern: Regular expression pattern
        flags: Compiled regex flags

    Returns:
        List of line indices that match the pattern
    """
    matching_indices: list[int] = []

    try:
        compiled_pattern = re.compile(pattern, flags)

        for i, line in enumerate(lines):
            # Search within the line (without EOL for cleaner matching)
            line_text = line.rstrip("\r\n")
            if compiled_pattern.search(line_text):
                matching_indices.append(i)

    except re.error:
        # If regex compilation fails, return empty list
        # Error will be reported by the caller
        return []

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


def _find_block_bounds(
    lines: list[str], start_pattern: str, end_pattern: str, flags: int
) -> tuple[int, int] | None:
    """
    Find the start and end indices of a block in the lines using regex patterns.

    Args:
        lines: List of file lines (with EOL)
        start_pattern: Regex pattern that marks the start of the block
        end_pattern: Regex pattern that marks the end of the block
        flags: Compiled regex flags

    Returns:
        Tuple of (start_idx, end_idx) or None if not found
    """
    start_idx = None
    end_idx = None

    try:
        compiled_start = re.compile(start_pattern, flags)
        compiled_end = re.compile(end_pattern, flags)

        for i, line in enumerate(lines):
            line_text = line.rstrip("\r\n")

            # Find start pattern
            if start_idx is None and compiled_start.search(line_text):
                start_idx = i
                # Check if end pattern is also on the same line
                if compiled_end.search(line_text):
                    end_idx = i
                    break
                continue

            # Find end pattern (must come after start)
            if start_idx is not None and compiled_end.search(line_text):
                end_idx = i
                break

        if start_idx is not None and end_idx is not None:
            return (start_idx, end_idx)
        return None

    except re.error:
        # If regex compilation fails, return None
        return None


def _parse_regex_flags(flags_list: list[str]) -> int:
    """
    Parse a list of regex flag strings into re module flags.

    Args:
        flags_list: List of flag strings like ['IGNORECASE', 'MULTILINE']

    Returns:
        Combined regex flags integer
    """
    flags = 0
    flag_map = {
        "IGNORECASE": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "DOTALL": re.DOTALL,
        "VERBOSE": re.VERBOSE,
    }

    for flag_str in flags_list:
        if flag_str.upper() in flag_map:
            flags |= flag_map[flag_str.upper()]

    return flags


def apply_edit_operation(
    original_content: str,
    operation: str,
    content: str = "",
    pattern: str = "",
    inherit_indent: bool = True,
    start_pattern: str = "",
    end_pattern: str = "",
    regex_flags: list[str] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Apply an edit operation to content and return the result.

    This function is used both for executing edits and generating previews.
    All pattern matching uses regular expressions.

    Args:
        original_content: The original file content
        operation: The edit operation to perform
        content: Content to insert, replace with, or append. Can use capture groups (\\1, \\2, etc.)
        pattern: Regular expression pattern to match lines
        inherit_indent: For insert operations, whether to copy leading whitespace
        start_pattern: Regex pattern for block operations start marker
        end_pattern: Regex pattern for block operations end marker
        regex_flags: List of regex flags (IGNORECASE, MULTILINE, DOTALL, VERBOSE)

    Returns:
        Tuple of (success: bool, message: str, new_content: str | None)
    """
    try:
        eol = _detect_eol(original_content)
        lines = original_content.splitlines(keepends=True)
        flags = _parse_regex_flags(regex_flags or [])

        # Handle different operations
        if operation == "replace":
            if not pattern:
                return False, "Pattern is required for replace operation", None

            matching_indices = _find_matching_lines(lines, pattern, flags)
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

            # Use regex substitution to replace within the matched line
            try:
                line_without_eol = lines[idx].rstrip("\r\n")
                compiled_pattern = re.compile(pattern, flags)
                new_line_text = compiled_pattern.sub(content, line_without_eol)
                lines[idx] = new_line_text + eol
            except re.error as e:
                return False, f"Invalid regex pattern: {str(e)}", None

        elif operation == "delete":
            if not pattern:
                return False, "Pattern is required for delete operation", None

            matching_indices = _find_matching_lines(lines, pattern, flags)
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

            matching_indices = _find_matching_lines(lines, pattern, flags)
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

        elif operation == "block_replace":
            if not start_pattern or not end_pattern:
                return (
                    False,
                    "Both start_pattern and end_pattern are required for block_replace operation",
                    None,
                )

            block_bounds = _find_block_bounds(lines, start_pattern, end_pattern, flags)
            if not block_bounds:
                return (
                    False,
                    f"Block with start_pattern '{start_pattern}' and end_pattern "
                    f"'{end_pattern}' not found",
                    None,
                )

            start_idx, end_idx = block_bounds

            # Check if markers are on the same line
            if start_idx == end_idx:
                # Adjacent markers on same line
                line = lines[start_idx].rstrip("\r\n")
                # Split the line to insert content between markers
                start_pos = line.find(start_pattern)
                end_pos = line.find(end_pattern, start_pos + len(start_pattern))
                if start_pos != -1 and end_pos != -1:
                    # Reconstruct the line with new content
                    before_start = line[: start_pos + len(start_pattern)]
                    after_end = line[end_pos:]
                    new_line = before_start + content + after_end
                    lines[start_idx] = new_line + eol
                else:
                    return False, "Could not locate adjacent markers on same line", None
            else:
                # Markers on different lines
                # Remove content between markers (but keep the markers)
                for _ in range(end_idx - start_idx - 1):
                    lines.pop(start_idx + 1)

                # Insert new content between markers
                if content.strip():  # Non-empty content
                    normalized_content = _normalize_content(content, eol)
                    new_lines = normalized_content.rstrip(eol).split(eol)

                    # Insert new lines at the position after start marker
                    for new_line in reversed(new_lines):
                        lines.insert(start_idx + 1, new_line + eol)
                else:  # Empty content - just add empty line
                    lines.insert(start_idx + 1, eol)

        elif operation == "block_delete":
            if not start_pattern or not end_pattern:
                return (
                    False,
                    "Both start_pattern and end_pattern are required for block_delete operation",
                    None,
                )

            block_bounds = _find_block_bounds(lines, start_pattern, end_pattern, flags)
            if not block_bounds:
                return (
                    False,
                    f"Block with start_pattern '{start_pattern}' and end_pattern "
                    f"'{end_pattern}' not found",
                    None,
                )

            start_idx, end_idx = block_bounds

            # Check if markers are on the same line
            if start_idx == end_idx:
                # Adjacent markers on same line - nothing to delete between them
                pass  # No action needed, preserve the line as is
            else:
                # Markers on different lines
                # Remove content between markers (but keep the markers)
                for _ in range(end_idx - start_idx - 1):
                    lines.pop(start_idx + 1)

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
    inherit_indent: bool = True,
    start_pattern: str = "",
    end_pattern: str = "",
    regex_flags: list[str] | None = None,
) -> tuple[bool, str, Any]:
    """Edit a file using regex-based pattern matching for all operations."""
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
            original_content,
            operation,
            content,
            pattern,
            inherit_indent,
            start_pattern,
            end_pattern,
            regex_flags,
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
