"""Utility functions for generating diffs."""

import difflib


def generate_diff(old_content: str, new_content: str, filepath: str) -> str:
    """
    Generate a unified diff between old and new content.

    Args:
        old_content: The original content of the file
        new_content: The new content to be written to the file
        filepath: The path to the file being modified

    Returns:
        A string containing the unified diff
    """
    # Split content into lines for difflib
    old_lines = old_content.splitlines(keepends=True) if old_content else []
    new_lines = new_content.splitlines(keepends=True) if new_content else []

    # Generate unified diff
    diff = difflib.unified_diff(
        old_lines, new_lines, fromfile=f"a/{filepath}", tofile=f"b/{filepath}", lineterm=""
    )

    # Convert diff generator to string
    diff_str = "\n".join(diff)

    # Return empty string if no diff
    if not diff_str:
        return ""

    return diff_str


def format_diff_for_display(diff: str, max_lines: int = 100) -> tuple[str, bool]:
    """
    Format diff for display, truncating if too long.

    Args:
        diff: The diff string to format
        max_lines: Maximum number of lines to display before truncating

    Returns:
        Tuple of (formatted_diff, is_truncated)
    """
    diff_lines = diff.splitlines()

    if len(diff_lines) > max_lines:
        # Truncate and add notice
        truncated_diff = "\n".join(diff_lines[:max_lines])
        truncated_diff += f"\n\n... ({len(diff_lines) - max_lines} more lines not shown)\n"
        truncated_diff += "Use --show-full-diff to see the complete diff."
        return truncated_diff, True

    return diff, False
