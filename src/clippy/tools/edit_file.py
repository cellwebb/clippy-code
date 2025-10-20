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
            "Supports pattern-anchored operations, block operations, and regex patterns "
            "for safer editing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to edit"},
                "operation": {
                    "type": "string",
                    "description": (
                        "The edit operation to perform:\n"
                        "- 'replace': Replace content matching a pattern\n"
                        "- 'delete': Delete lines matching a pattern\n"
                        "- 'append': Add content at the end of the file\n"
                        "- 'insert_before': Insert before a line matching a pattern\n"
                        "- 'insert_after': Insert after a line matching a pattern\n"
                        "- 'block_replace': Replace a multi-line block between start/end markers\n"
                        "- 'block_delete': Delete a multi-line block between start/end markers\n"
                        "- 'regex_replace': Replace using regular expressions with capture groups"
                    ),
                    "enum": [
                        "replace",
                        "delete",
                        "append",
                        "insert_before",
                        "insert_after",
                        "block_replace",
                        "block_delete",
                        "regex_replace",
                    ],
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
                "start_pattern": {
                    "type": "string",
                    "description": (
                        "Start pattern for block operations (block_replace, block_delete). "
                        "Marks the beginning of the block to target."
                    ),
                },
                "end_pattern": {
                    "type": "string",
                    "description": (
                        "End pattern for block operations (block_replace, block_delete). "
                        "Marks the end of the block to target."
                    ),
                },
                "regex_pattern": {
                    "type": "string",
                    "description": (
                        "Regular expression pattern for regex_replace operation. "
                        "Can contain capture groups for use in replacement content."
                    ),
                },
                "regex_flags": {
                    "type": "array",
                    "description": (
                        "List of regex flags for regex_replace operation. "
                        "Available flags: 'IGNORECASE', 'MULTILINE', 'DOTALL', 'VERBOSE'"
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


def _split_pattern_lines(pattern: str) -> list[str]:
    """Split a multi-line pattern while preserving intentional blank lines."""
    normalized_pattern = pattern.replace("\r\n", "\n")
    lines = normalized_pattern.splitlines()
    if normalized_pattern.endswith("\n") and not lines:
        return [""]
    return lines


def _find_matching_lines(lines: list[str], pattern: str, match_pattern_line: bool) -> list[int]:
    """Find all lines matching the pattern."""
    matching_indices: list[int] = []

    # Check if pattern contains newlines (multi-line pattern)
    is_multiline_pattern = "\n" in pattern or "\r\n" in pattern

    if is_multiline_pattern and match_pattern_line:
        # For multi-line patterns with exact matching, we need to match across multiple lines
        pattern_lines = _split_pattern_lines(pattern)
        if not pattern_lines:
            return matching_indices

        # Try to find the pattern starting at each line
        for i in range(len(lines) - len(pattern_lines) + 1):
            match = True
            for j, pattern_line in enumerate(pattern_lines):
                line_without_eol = lines[i + j].rstrip("\r\n")
                # Normalize both pattern line and file line to LF for comparison
                normalized_file_line = line_without_eol.replace("\r\n", "\n")
                if normalized_file_line != pattern_line:
                    match = False
                    break
            if match:
                matching_indices.append(i)
    else:
        # Single-line pattern or substring matching
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


def _find_block_bounds(
    lines: list[str], start_pattern: str, end_pattern: str
) -> tuple[int, int] | None:
    """
    Find the start and end indices of a block in the lines.

    Args:
        lines: List of file lines (with EOL)
        start_pattern: Pattern that marks the start of the block
        end_pattern: Pattern that marks the end of the block

    Returns:
        Tuple of (start_idx, end_idx) or None if not found
    """
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        line_text = line.rstrip("\r\n")

        # Find start pattern
        if start_idx is None and start_pattern in line_text:
            start_idx = i
            # Check if end pattern is also on the same line
            if end_pattern in line_text:
                end_idx = i
                break
            continue

        # Find end pattern (must come after start)
        if start_idx is not None and end_pattern in line_text:
            end_idx = i
            break

    if start_idx is not None and end_idx is not None:
        return (start_idx, end_idx)
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


def _apply_regex_replace(
    lines: list[str], pattern: str, replacement: str, flags: int
) -> tuple[bool, str, list[str]]:
    """
    Apply regex replacement to all lines.

    Args:
        lines: List of file lines (with EOL)
        pattern: Regular expression pattern
        replacement: Replacement string (can use capture groups)
        flags: Regex flags

    Returns:
        Tuple of (success, message, new_lines)
    """
    try:
        # If DOTALL flag is used, process the entire content as one piece
        # to allow multi-line matches
        if flags & re.DOTALL:
            full_content = "".join(lines)
            compiled_pattern = re.compile(pattern, flags)
            new_content = compiled_pattern.sub(replacement, full_content)

            if new_content != full_content:
                # Split back into lines preserving original structure as much as possible
                # Try to preserve original line endings by analyzing the original content
                if "\r\n" in full_content:
                    eol = "\r\n"
                else:
                    eol = "\n"

                new_lines = new_content.splitlines(keepends=True)
                # Ensure lines end with proper EOL
                for i, line in enumerate(new_lines):
                    if not line.endswith("\r\n") and not line.endswith("\n"):
                        new_lines[i] = line + eol

                return True, "Regex replacement completed successfully", new_lines
            else:
                return True, "Regex pattern matched no lines", lines
        else:
            # Process line by line for non-DOTALL operations
            compiled_pattern = re.compile(pattern, flags)
            new_lines = []
            made_changes = False

            for line in lines:
                line_text = line.rstrip("\r\n")
                new_line_text = compiled_pattern.sub(replacement, line_text)

                # Preserve the original line ending exactly as it was
                if line.endswith("\r\n"):
                    new_line = new_line_text + "\r\n"
                elif line.endswith("\n"):
                    new_line = new_line_text + "\n"
                else:
                    # Line had no ending, preserve that
                    new_line = new_line_text

                new_lines.append(new_line)

                if new_line_text != line_text:
                    made_changes = True

            if made_changes:
                return True, "Regex replacement completed successfully", new_lines
            else:
                return True, "Regex pattern matched no lines", lines

    except re.error as e:
        return False, f"Invalid regex pattern: {str(e)}", lines
    except Exception as e:
        return False, f"Regex error: {str(e)}", lines


def apply_edit_operation(
    original_content: str,
    operation: str,
    content: str = "",
    pattern: str = "",
    match_pattern_line: bool = True,
    inherit_indent: bool = True,
    start_pattern: str = "",
    end_pattern: str = "",
    regex_pattern: str = "",
    regex_flags: list[str] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Apply an edit operation to content and return the result.

    This function is used both for executing edits and generating previews.

    Args:
        original_content: The original file content
        operation: The edit operation to perform
        content: Content to insert, replace with, or append
        pattern: Pattern to match lines for operations (for basic operations)
        match_pattern_line: Whether to match the pattern against entire lines
        inherit_indent: For insert operations, whether to copy leading whitespace
        start_pattern: Start pattern for block operations (block_replace, block_delete)
        end_pattern: End pattern for block operations (block_replace, block_delete)
        regex_pattern: Regular expression pattern for regex_replace operation
        regex_flags: List of regex flags for regex_replace operation

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
                # For multi-line patterns, we need to replace multiple lines
                is_multiline_pattern = "\n" in pattern or "\r\n" in pattern
                if is_multiline_pattern:
                    pattern_lines = _split_pattern_lines(pattern)
                    if not pattern_lines:
                        return False, "Pattern is empty for multi-line replace", None

                    # Remove the old lines
                    for _ in range(len(pattern_lines)):
                        lines.pop(idx)

                    # Insert the new content (normalized)
                    new_content_normalized = _normalize_content(content, eol)
                    new_lines = new_content_normalized.rstrip(eol).split(eol)

                    # Insert new lines at the same position
                    for new_line in reversed(new_lines):
                        lines.insert(idx, new_line + eol)
                else:
                    # Single line replacement
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

            # For multi-line patterns, we need to handle multiple lines
            is_multiline_pattern = "\n" in pattern or "\r\n" in pattern
            if is_multiline_pattern and match_pattern_line:
                # Delete in reverse order, but account for multi-line patterns
                pattern_lines = _split_pattern_lines(pattern)
                if not pattern_lines:
                    return False, "Pattern is empty for multi-line delete", None

                for start_idx in reversed(matching_indices):
                    for _ in range(len(pattern_lines)):
                        if start_idx < len(lines):
                            lines.pop(start_idx)
            else:
                # Single-line deletion - delete in reverse order to avoid index shifting
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

        elif operation == "block_replace":
            if not start_pattern or not end_pattern:
                return (
                    False,
                    "Both start_pattern and end_pattern are required for block_replace operation",
                    None,
                )

            block_bounds = _find_block_bounds(lines, start_pattern, end_pattern)
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

            block_bounds = _find_block_bounds(lines, start_pattern, end_pattern)
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

        elif operation == "regex_replace":
            if not regex_pattern:
                return False, "regex_pattern is required for regex_replace operation", None

            flags = _parse_regex_flags(regex_flags or [])
            success, message, new_lines = _apply_regex_replace(lines, regex_pattern, content, flags)
            if not success:
                return False, message, None

            lines = new_lines

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
    start_pattern: str = "",
    end_pattern: str = "",
    regex_pattern: str = "",
    regex_flags: list[str] | None = None,
) -> tuple[bool, str, Any]:
    """Edit a file with enhanced block and regex operations."""
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
            match_pattern_line,
            inherit_indent,
            start_pattern,
            end_pattern,
            regex_pattern,
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
