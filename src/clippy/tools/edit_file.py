"""Edit file tool implementation."""

from typing import Any

from rapidfuzz.distance import JaroWinkler

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Edit a file by inserting, replacing, deleting, or appending content. "
            "All pattern matching uses EXACT STRING MATCHING with FUZZY MATCHING FALLBACK.\n\n"
            "PATTERN MATCHING:\n"
            "1. EXACT MATCH: Pattern must appear exactly in file (copy text from file)\n"
            "2. FUZZY FALLBACK: If no exact match, tries fuzzy matching (Jaro-Winkler ≥ 0.95)\n"
            "   - Handles minor whitespace differences automatically\n"
            "   - No need to escape special characters!\n\n"
            "CRITICAL BEST PRACTICES:\n"
            "1. ALWAYS use read_file BEFORE edit_file to see exact content\n"
            "2. COPY exact text you want to match (including whitespace)\n"
            "3. If 'pattern found N times' error: Include more surrounding context\n"
            "   to make pattern unique\n"
            "4. Multi-line patterns work naturally - just use \\n in pattern string\n"
            "   Example: pattern='class Foo:\\n    def bar'\n"
            "5. NO special character escaping needed (. * + ? etc. are literal)\n"
            "6. NEVER retry the same failing pattern twice - read file and adjust\n"
            "7. Fuzzy matching handles minor typos/spacing automatically (≥95% similar)\n"
            "8. Pattern can be a substring - doesn't need to match entire line"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to edit"},
                "operation": {
                    "type": "string",
                    "description": (
                        "The edit operation to perform:\n"
                        "- 'replace': Replace content matching exact pattern "
                        "(must match exactly once)\n"
                        "- 'delete': Delete lines matching exact pattern "
                        "(can match multiple lines)\n"
                        "- 'append': Add content at the end of the file\n"
                        "- 'insert_before': Insert before a line matching exact pattern "
                        "(must match exactly once)\n"
                        "- 'insert_after': Insert after a line matching exact pattern "
                        "(must match exactly once)\n"
                        "- 'block_replace': Replace a multi-line block between start/end "
                        "markers (exact string match)\n"
                        "- 'block_delete': Delete a multi-line block between start/end "
                        "markers (exact string match)"
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
                    "description": "Content to insert, replace with, or append.",
                },
                "pattern": {
                    "type": "string",
                    "description": (
                        "Exact text to match (required for replace, delete, insert_before, "
                        "insert_after). Copy the exact text from the file you want to match. "
                        "Can include newlines (\\n) for multi-line patterns. For "
                        "replace/insert_before/insert_after, pattern must match exactly once. "
                        "For delete, can match multiple lines. If exact match fails, fuzzy "
                        "matching (≥95% similarity) is tried automatically."
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
                        "Exact text for block operations (block_replace, block_delete). "
                        "Marks the beginning of the block to target. Uses exact substring "
                        "matching."
                    ),
                },
                "end_pattern": {
                    "type": "string",
                    "description": (
                        "Exact text for block operations (block_replace, block_delete). "
                        "Marks the end of the block to target. Uses exact substring matching."
                    ),
                },
            },
            "required": ["path", "operation"],
        },
    },
}


def _find_best_window(
    haystack_lines: list[str], needle: str
) -> tuple[tuple[int, int] | None, float]:
    """
    Find the window in haystack_lines with highest Jaro-Winkler similarity to needle.

    Uses a sliding window approach to find the best matching sequence of lines
    that most closely resembles the needle text. This is used as a fuzzy fallback
    when exact pattern matching fails.

    Args:
        haystack_lines: List of lines to search through (with EOL characters)
        needle: The text to find (will be split into lines for comparison)

    Returns:
        A tuple of ((start_line, end_line), score) where:
        - (start_line, end_line) is the best matching window, or None if no good match
        - score is the Jaro-Winkler similarity score (0.0 to 1.0)
    """
    needle = needle.rstrip("\n")
    needle_lines = needle.splitlines()
    win_size = len(needle_lines)

    if win_size == 0:
        return (None, 0.0)

    best_score = 0.0
    best_span: tuple[int, int] | None = None

    # Slide a window of size win_size over the haystack
    for i in range(len(haystack_lines) - win_size + 1):
        # Extract window and join lines
        window_lines = [haystack_lines[j].rstrip("\r\n") for j in range(i, i + win_size)]
        window = "\n".join(window_lines)

        # Calculate similarity score
        score = JaroWinkler.normalized_similarity(window, needle)

        if score > best_score:
            best_score = score
            best_span = (i, i + win_size)

    return (best_span, best_score)


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


def _find_matching_lines(lines: list[str], pattern: str) -> tuple[list[int], bool, float]:
    """
    Find all lines matching the pattern using exact string matching with fuzzy fallback.

    First attempts exact substring matching. If no matches are found, attempts fuzzy
    matching using Jaro-Winkler similarity with a threshold of 0.95.

    Args:
        lines: List of file lines (with EOL)
        pattern: Exact text to find (can include newlines for multi-line patterns)

    Returns:
        A tuple of (matching_indices, fuzzy_used, similarity_score) where:
        - matching_indices: List of line indices that match
        - fuzzy_used: True if fuzzy matching was used to find matches
        - similarity_score: Jaro-Winkler score if fuzzy matching was used, else 1.0
    """
    matching_indices: list[int] = []
    fuzzy_used = False
    similarity_score = 1.0

    # Check if pattern contains newlines (multi-line pattern)
    if "\n" in pattern:
        # Multi-line pattern - search across full content
        full_content = "".join(lines)
        pattern_normalized = pattern.replace("\r\n", "\n")

        # Find all occurrences of the pattern
        start = 0
        while True:
            idx = full_content.find(pattern_normalized, start)
            if idx == -1:
                break

            # Map character indices (start and end of pattern) to line numbers
            pattern_start_idx = idx
            pattern_end_idx = idx + len(pattern_normalized)

            # Find which lines the pattern spans
            chars_seen = 0
            start_line = None
            end_line = None

            for i, line in enumerate(lines):
                line_start = chars_seen
                line_end = chars_seen + len(line)

                # Check if pattern starts in this line
                if start_line is None and line_start <= pattern_start_idx < line_end:
                    start_line = i

                # Check if pattern ends in or before this line
                if pattern_end_idx <= line_end:
                    end_line = i
                    break

                chars_seen += len(line)

            # Add only the start line to matching_indices
            # (This counts matches, not individual lines in the match)
            if start_line is not None and end_line is not None:
                matching_indices.append(start_line)

            # Skip past the entire pattern to avoid overlapping matches
            start = idx + len(pattern_normalized)
    else:
        # Single-line pattern - search line by line
        for i, line in enumerate(lines):
            line_text = line.rstrip("\r\n")
            if pattern in line_text:
                matching_indices.append(i)

    # If no exact matches found, try fuzzy matching
    if not matching_indices:
        best_span, best_score = _find_best_window(lines, pattern)

        # Use fuzzy match if similarity score is >= 0.95
        if best_score >= 0.95 and best_span is not None:
            fuzzy_used = True
            similarity_score = best_score
            # Add all lines in the matched window
            matching_indices = list(range(best_span[0], best_span[1]))

    return (matching_indices, fuzzy_used, similarity_score)


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
    Find the start and end indices of a block in the lines using exact string matching.

    Args:
        lines: List of file lines (with EOL)
        start_pattern: Exact text that marks the start of the block
        end_pattern: Exact text that marks the end of the block

    Returns:
        Tuple of (start_idx, end_idx) or None if not found
    """
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        line_text = line.rstrip("\r\n")

        # Find start pattern (exact substring match)
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


def apply_edit_operation(
    original_content: str,
    operation: str,
    content: str = "",
    pattern: str = "",
    inherit_indent: bool = True,
    start_pattern: str = "",
    end_pattern: str = "",
) -> tuple[bool, str, str | None]:
    """
    Apply an edit operation to content and return the result.

    This function is used both for executing edits and generating previews.
    All pattern matching uses exact string matching with fuzzy fallback.

    Args:
        original_content: The original file content
        operation: The edit operation to perform
        content: Content to insert, replace with, or append
        pattern: Exact text to match (can include newlines for multi-line patterns)
        inherit_indent: For insert operations, whether to copy leading whitespace
        start_pattern: Exact text for block operations start marker
        end_pattern: Exact text for block operations end marker

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

            matching_indices, fuzzy_used, similarity_score = _find_matching_lines(lines, pattern)
            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                fuzzy_note = (
                    f" (fuzzy match, similarity={similarity_score:.3f})" if fuzzy_used else ""
                )
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times{fuzzy_note}, "
                    "expected exactly one match",
                    None,
                )

            # If fuzzy matching was used, replace the entire matched window
            if fuzzy_used:
                # Fuzzy match returns a window of lines to replace
                start_idx = matching_indices[0]
                end_idx = matching_indices[-1] + 1

                # Replace all lines in the window with the new content
                normalized_content = _normalize_content(content, eol)
                new_content_lines = normalized_content.splitlines(keepends=True)

                # Remove old lines and insert new ones
                for _ in range(start_idx, end_idx):
                    lines.pop(start_idx)

                for i, new_line in enumerate(new_content_lines):
                    lines.insert(start_idx + i, new_line)
            else:
                # Use simple string replacement for exact matches
                if "\n" in pattern:
                    # Multi-line pattern - replace in full content
                    full_content = "".join(lines)
                    pattern_normalized = pattern.replace("\r\n", "\n")
                    new_full_content = full_content.replace(pattern_normalized, content, 1)

                    # Re-split into lines, preserving EOL style
                    new_lines = new_full_content.splitlines(keepends=True)

                    # Ensure trailing EOL is preserved if original had one
                    if lines and lines[-1].endswith(eol):
                        if new_lines and not new_lines[-1].endswith(eol):
                            new_lines[-1] += eol

                    lines.clear()
                    lines.extend(new_lines)
                else:
                    # Single-line pattern - replace within the matched line
                    idx = matching_indices[0]
                    line_without_eol = lines[idx].rstrip("\r\n")
                    new_line_text = line_without_eol.replace(pattern, content, 1)
                    lines[idx] = new_line_text + eol

        elif operation == "delete":
            if not pattern:
                return False, "Pattern is required for delete operation", None

            matching_indices, fuzzy_used, similarity_score = _find_matching_lines(lines, pattern)
            if not matching_indices:
                return False, f"Pattern '{pattern}' not found in file", None

            # Handle multi-line patterns with string replacement
            if "\n" in pattern:
                # Multi-line pattern - use string replacement to delete entire pattern
                full_content = "".join(lines)
                pattern_normalized = pattern.replace("\r\n", "\n")

                # If pattern doesn't end with newline, also delete the trailing newline
                # This prevents leaving blank lines behind
                delete_pattern = pattern_normalized
                if not delete_pattern.endswith("\n"):
                    delete_pattern += "\n"

                # Delete all occurrences
                new_full_content = full_content.replace(delete_pattern, "")

                # Re-split into lines, preserving EOL style
                new_lines = new_full_content.splitlines(keepends=True)

                # Ensure trailing EOL is preserved if original had one
                if lines and lines[-1].endswith(eol):
                    if new_lines and not new_lines[-1].endswith(eol):
                        new_lines[-1] += eol

                lines.clear()
                lines.extend(new_lines)
            elif fuzzy_used:
                # Fuzzy match returns window of lines to delete
                start_idx = matching_indices[0]
                end_idx = matching_indices[-1] + 1
                # Delete all lines in the window
                for _ in range(start_idx, end_idx):
                    lines.pop(start_idx)
            else:
                # Single-line pattern - delete matching lines
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

            matching_indices, fuzzy_used, similarity_score = _find_matching_lines(lines, pattern)
            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                fuzzy_note = (
                    f" (fuzzy match, similarity={similarity_score:.3f})" if fuzzy_used else ""
                )
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times{fuzzy_note}, "
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
) -> tuple[bool, str, Any]:
    """Edit a file using exact string matching with fuzzy fallback for all operations."""
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
