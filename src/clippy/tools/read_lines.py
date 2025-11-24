"""Read line ranges from files tool implementation."""

from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_lines",
        "description": (
            "Read specific line ranges from a file. Perfect for focused analysis "
            "of code sections without loading entire files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to read"},
                "line_range": {
                    "type": "string",
                    "description": (
                        "Line range specification (e.g., '10-20', '10:20', '15', "
                        "':10', '10:', '-10:', ':10+5')"
                    ),
                },
                "numbering": {
                    "type": "string",
                    "description": (
                        "How line numbers are interpreted: 'top' (from file start), "
                        "'bottom' (from file end), 'auto' (detect based on format)"
                    ),
                    "enum": ["top", "bottom", "auto"],
                    "default": "auto",
                },
                "context": {
                    "type": "integer",
                    "description": (
                        "Number of context lines to include before and after the specified range"
                    ),
                    "default": 0,
                },
                "show_line_numbers": {
                    "type": "boolean",
                    "description": "Whether to include line numbers in the output",
                    "default": True,
                },
                "max_lines": {
                    "type": "integer",
                    "description": (
                        "Maximum number of lines to return (prevents accidental large reads)"
                    ),
                    "default": 100,
                },
            },
            "required": ["path", "line_range"],
        },
    },
}


def parse_line_range(range_spec: str, total_lines: int, numbering: str) -> tuple[int, int]:
    """Parse line range specification into start and end indices (1-based, inclusive).

    Args:
        range_spec: Range specification like '10-20', '15', ':10', '10:', '-10:', ':10+5'
        total_lines: Total number of lines in the file
        numbering: How to interpret numbers ('top', 'bottom', 'auto')

    Returns:
        Tuple of (start_line, end_line) as 1-based indices

    Examples:
        parse_line_range('10-20', 100, 'top') -> (10, 20)
        parse_line_range('-10:', 100, 'bottom') -> (91, 100)  # Last 10 lines
        parse_line_range(':10+5', 100, 'top') -> (10, 15)   # Lines 10-15
    """
    start = 1
    end = total_lines

    # Detect bottom numbering with explicit prefix
    if numbering == "auto" and range_spec.startswith("-"):
        numbering = "bottom"

    # Normalize the range specification
    # Replace colons with hyphens for easier parsing
    normalized = range_spec.replace(":", "-")

    # Handle bottom numbering
    if numbering == "bottom" and normalized.startswith("-"):
        # Remove the initial hyphen for bottom numbering
        normalized = normalized[1:]

        # Parse as positive numbers, then convert to bottom indexing
        if not normalized or normalized == "-":
            return (1, total_lines)

        # Handle range like "-10-20" (bottom: lines 10-20 from end)
        if "-" in normalized and not normalized.startswith("-"):
            parts = normalized.split("-")
            if len(parts) == 2:
                try:
                    start_from_bottom = int(parts[0])
                    end_from_bottom = int(parts[1])
                    start = max(1, total_lines - start_from_bottom + 1)
                    end = max(1, total_lines - end_from_bottom + 1)
                    # Ensure start <= end
                    if start > end:
                        start, end = end, start
                except ValueError:
                    return (1, total_lines)

        # Handle range like "-10" (bottom: last 10 lines)
        elif "-" not in normalized:
            try:
                count = int(normalized)
                start = max(1, total_lines - count + 1)
                end = total_lines
            except ValueError:
                return (1, total_lines)

    # Handle top numbering or auto-detected top numbering
    else:
        # Pattern matching for different formats
        if "+" in normalized:
            # Format like "10+5" (start at line 10, include 5 more lines)
            try:
                start_line, offset = normalized.split("+")
                start = int(start_line)
                end = start + int(offset)
            except (ValueError, IndexError):
                return (1, total_lines)
        elif normalized.count("-") == 1 and not normalized.startswith("-"):
            # Format like "10-20" (range from line 10 to 20)
            try:
                start_str, end_str = normalized.split("-")
                start = int(start_str) if start_str else 1
                end = int(end_str) if end_str else total_lines
            except ValueError:
                return (1, total_lines)
        elif normalized == "-":
            # Just a hyphen means entire file
            return (1, total_lines)
        elif normalized.count("-") == 2:
            # Format like "10-20+" with offset
            try:
                parts = normalized.split("-")
                start = int(parts[0]) if parts[0] else 1
                end = int(parts[1]) if parts[1] else total_lines
                if parts[2] == "":
                    end = total_lines
                else:
                    # Handle offset after second hyphen
                    # This is complex, fallback to safer parsing
                    pass
            except ValueError:
                return (1, total_lines)
        else:
            # Single number like "15" (just line 15)
            try:
                line_num = int(normalized)
                start = line_num
                end = line_num
            except ValueError:
                return (1, total_lines)

    # Clamp to valid range
    start = max(1, min(start, total_lines))
    end = max(1, min(end, total_lines))

    # Ensure start <= end
    if start > end:
        start, end = end, start

    return (start, end)


def read_lines(
    path: str,
    line_range: str,
    numbering: str = "auto",
    context: int = 0,
    show_line_numbers: bool = True,
    max_lines: int = 100,
) -> tuple[bool, str, Any]:
    """Read specific line ranges from a file.

    Args:
        path: Path to the file
        line_range: Line range specification
        numbering: How to interpret line numbers ('top', 'bottom', 'auto')
        context: Number of context lines before/after
        show_line_numbers: Whether to show line numbers in output
        max_lines: Maximum lines to return

    Returns:
        Tuple of (success, message, content)
    """
    try:
        # Read all lines first to get total count
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
            total_lines = len(lines)

        if not lines:
            return True, f"File {path} is empty", ""

        # Parse the line range
        start, end = parse_line_range(line_range, total_lines, numbering)

        # Add context lines
        if context > 0:
            start = max(1, start - context)
            end = min(total_lines, end + context)

        # Apply max_lines limit
        if (end - start + 1) > max_lines:
            end = start + max_lines - 1
            warning_msg = f" (limited to {max_lines} lines)"
        else:
            warning_msg = ""

        # Extract the lines (convert to 0-based indexing)
        selected_lines = lines[start - 1 : end]

        # Format output
        if show_line_numbers:
            # Prepend line numbers
            numbered_lines = []
            for i, line in enumerate(selected_lines, start=start):
                # Remove existing line endings, add our own
                line_content = line.rstrip("\n\r")
                numbered_lines.append(f"{i:4d}: {line_content}")
            content = "\n".join(numbered_lines)
        else:
            # Just return the content without line numbers
            content = "".join(selected_lines).rstrip("\r\n")

        # Create informative message
        range_desc = f"{start}-{end}" if start != end else str(start)

        # Add context info to message
        context_info = f" with {context} context lines" if context > 0 else ""
        numbering_info = f" ({numbering} numbering)" if numbering != "auto" else ""

        message = (
            f"Read lines {range_desc} from {path} "
            f"(total: {total_lines} lines){context_info}{numbering_info}{warning_msg}"
        )

        return True, message, content

    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except PermissionError:
        return False, f"Permission denied when reading: {path}", None
    except UnicodeDecodeError:
        return False, f"Unable to decode file (might be binary): {path}", None
    except Exception as e:
        return False, f"Failed to read {path}: {str(e)}", None
