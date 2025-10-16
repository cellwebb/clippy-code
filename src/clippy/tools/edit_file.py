"""Edit file tool implementation."""

from typing import Any


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

        # Detect dominant EOL style from existing content
        if "\r\n" in original_content:
            dominant_eol = "\r\n"
        elif original_content and not original_content.endswith("\n"):
            # File has no trailing EOL on last line
            dominant_eol = "\n"  # Default for new content
        else:
            dominant_eol = "\n"

        lines = original_content.splitlines(keepends=True)

        # Handle different operations
        if operation == "replace":
            if not pattern:
                return False, "Pattern is required for replace operation", None

            # Find all lines matching the pattern to ensure exactly one match
            matching_indices = []
            for i, line in enumerate(lines):
                if match_pattern_line:
                    # Full line equality match (no trimming, just remove EOL for comparison)
                    line_without_eol = line.rstrip("\r\n")
                    if line_without_eol == pattern:
                        matching_indices.append(i)
                else:
                    # Substring match (case insensitive)
                    if pattern.lower() in line.lower():
                        matching_indices.append(i)

            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times, "
                    f"expected exactly one match",
                    None,
                )

            # Exactly one match - proceed with replacement
            idx = matching_indices[0]

            if match_pattern_line:
                # Full line replacement - replace entire line with content
                normalized_content = content.replace("\r\n", "\n").replace("\n", dominant_eol)

                # Ensure content ends with the detected EOL
                if normalized_content and not normalized_content.endswith(dominant_eol):
                    normalized_content += dominant_eol

                lines[idx] = normalized_content
            else:
                # Substring replacement - replace only the matching substring within the line
                line = lines[idx]
                line_without_eol = line.rstrip("\r\n")

                # Find the pattern in the line (case insensitive)
                lower_line = line_without_eol.lower()
                lower_pattern = pattern.lower()
                start_pos = lower_line.find(lower_pattern)

                if start_pos != -1:
                    # Replace just the matching part
                    end_pos = start_pos + len(pattern)
                    new_line = line_without_eol[:start_pos] + content + line_without_eol[end_pos:]
                    # Add back the EOL
                    lines[idx] = new_line + dominant_eol
                else:
                    # This shouldn't happen since we already found the match
                    return (
                        False,
                        f"Pattern '{pattern}' not found in line during replacement",
                        None,
                    )

        elif operation == "delete":
            if not pattern:
                return False, "Pattern is required for delete operation", None

            # Find and delete lines matching the pattern
            # Need to iterate backwards to avoid index shifting issues
            found = False
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                if match_pattern_line:
                    # Full line equality match (no trimming, just remove EOL for comparison)
                    line_without_eol = line.rstrip("\r\n")
                    if line_without_eol == pattern:
                        lines.pop(i)
                        found = True
                else:
                    # Substring match (case insensitive)
                    if pattern.lower() in line.lower():
                        lines.pop(i)
                        found = True

            if not found:
                return False, f"Pattern '{pattern}' not found in file", None

        elif operation == "append":
            # Normalize content for append
            normalized_content = content.replace("\r\n", "\n").replace("\n", dominant_eol)

            # If the file doesn't end with newline but we're appending, add proper EOL first
            # However, if the content starts with a newline, don't add EOL to last line
            # because the content's leading newline will serve as the separator
            last_line_needs_eol = lines and lines[-1] and not lines[-1].endswith(dominant_eol)
            content_starts_with_newline = normalized_content.startswith(dominant_eol)

            if last_line_needs_eol and not content_starts_with_newline:
                lines[-1] = lines[-1].rstrip("\r\n") + dominant_eol

            # Ensure content ends with the detected EOL
            if normalized_content and not normalized_content.endswith(dominant_eol):
                normalized_content += dominant_eol

            lines.append(normalized_content)

        elif operation == "insert_before":
            if not pattern:
                return False, "Pattern is required for insert_before operation", None

            # Find the line matching the pattern
            matching_indices = []
            for i, line in enumerate(lines):
                if match_pattern_line:
                    # Full line equality match (no trimming, just remove EOL for comparison)
                    line_without_eol = line.rstrip("\r\n")
                    if line_without_eol == pattern:
                        matching_indices.append(i)
                else:
                    # Substring match (case insensitive)
                    if pattern.lower() in line.lower():
                        matching_indices.append(i)

            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times, "
                    f"expected exactly one match",
                    None,
                )

            # Insert before the matched line
            idx = matching_indices[0]

            # Process content for insertion
            if inherit_indent:
                # Extract leading whitespace from the anchor line
                anchor_line = lines[idx]
                leading_whitespace = ""
                for char in anchor_line:
                    if char in " \t":
                        leading_whitespace += char
                    else:
                        break

                # Normalize content to internal \n format for processing
                content_lines = content.replace("\r\n", "\n").split("\n")
                # Filter out empty strings at the end
                while content_lines and content_lines[-1] == "":
                    content_lines.pop()

                # Add leading whitespace to each line and rejoin with dominant EOL
                indented_lines = []
                for line in content_lines:
                    if line.strip():  # Don't indent empty lines
                        indented_lines.append(leading_whitespace + line)
                    else:
                        indented_lines.append(line)

                normalized_content = dominant_eol.join(indented_lines)
            else:
                # Just normalize EOLs without indentation changes
                normalized_content = content.replace("\r\n", "\n").replace("\n", dominant_eol)

            # Ensure content ends with the detected EOL
            if normalized_content and not normalized_content.endswith(dominant_eol):
                normalized_content += dominant_eol

            lines.insert(idx, normalized_content)

        elif operation == "insert_after":
            if not pattern:
                return False, "Pattern is required for insert_after operation", None

            # Find the line matching the pattern
            matching_indices = []
            for i, line in enumerate(lines):
                if match_pattern_line:
                    # Full line equality match (no trimming, just remove EOL for comparison)
                    line_without_eol = line.rstrip("\r\n")
                    if line_without_eol == pattern:
                        matching_indices.append(i)
                else:
                    # Substring match (case insensitive)
                    if pattern.lower() in line.lower():
                        matching_indices.append(i)

            if len(matching_indices) == 0:
                return False, f"Pattern '{pattern}' not found in file", None
            elif len(matching_indices) > 1:
                return (
                    False,
                    f"Pattern '{pattern}' found {len(matching_indices)} times, "
                    f"expected exactly one match",
                    None,
                )

            # Insert after the matched line
            idx = matching_indices[0] + 1

            # Process content for insertion
            if inherit_indent:
                # Extract leading whitespace from the anchor line
                anchor_line = lines[matching_indices[0]]
                leading_whitespace = ""
                for char in anchor_line:
                    if char in " \t":
                        leading_whitespace += char
                    else:
                        break

                # Normalize content to internal \n format for processing
                content_lines = content.replace("\r\n", "\n").split("\n")
                # Filter out empty strings at the end
                while content_lines and content_lines[-1] == "":
                    content_lines.pop()

                # Add leading whitespace to each line and rejoin with dominant EOL
                indented_lines = []
                for line in content_lines:
                    if line.strip():  # Don't indent empty lines
                        indented_lines.append(leading_whitespace + line)
                    else:
                        indented_lines.append(line)

                normalized_content = dominant_eol.join(indented_lines)
            else:
                # Just normalize EOLs without indentation changes
                normalized_content = content.replace("\r\n", "\n").replace("\n", dominant_eol)

            # Ensure content ends with the detected EOL
            if normalized_content and not normalized_content.endswith(dominant_eol):
                normalized_content += dominant_eol

            lines.insert(idx, normalized_content)

        else:
            return False, f"Unknown operation: {operation}", None

        # Write back to file
        # Use newline='' to preserve the line endings we constructed
        new_content = "".join(lines)
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

        return True, f"Successfully performed {operation} operation", None

    except PermissionError:
        return False, f"Permission denied when editing: {path}", None
    except Exception as e:
        return False, f"Failed to edit {path}: {str(e)}", None
