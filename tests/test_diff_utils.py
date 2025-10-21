"""Tests for diff utilities."""

from clippy.diff_utils import format_diff_for_display, generate_diff


def test_generate_diff() -> None:
    """Test generating a diff between two file contents."""
    old_content = "Hello, world!\nThis is a test file.\n"
    new_content = "Hello, world!\nThis is a modified test file.\n"
    filepath = "test.txt"

    diff = generate_diff(old_content, new_content, filepath)
    assert diff != ""
    assert "--- a/test.txt" in diff
    assert "+++ b/test.txt" in diff
    assert "-This is a test file." in diff
    assert "+This is a modified test file." in diff


def test_generate_diff_new_file() -> None:
    """Test generating a diff for a new file."""
    old_content = ""
    new_content = "Hello, world!\nThis is a new file.\n"
    filepath = "new.txt"

    diff = generate_diff(old_content, new_content, filepath)
    assert diff != ""
    assert "--- a/new.txt" in diff
    assert "+++ b/new.txt" in diff
    assert "+Hello, world!" in diff
    assert "+This is a new file." in diff


def test_generate_diff_deleted_file() -> None:
    """Test generating a diff for a deleted file."""
    old_content = "Hello, world!\nThis file will be deleted.\n"
    new_content = ""
    filepath = "deleted.txt"

    diff = generate_diff(old_content, new_content, filepath)
    assert diff != ""
    assert "--- a/deleted.txt" in diff
    assert "+++ b/deleted.txt" in diff
    assert "-Hello, world!" in diff
    assert "-This file will be deleted." in diff


def test_generate_diff_no_changes() -> None:
    """Test generating a diff when there are no changes."""
    old_content = "Hello, world!\nThis is a test file.\n"
    new_content = "Hello, world!\nThis is a test file.\n"
    filepath = "unchanged.txt"

    diff = generate_diff(old_content, new_content, filepath)
    assert diff == ""


def test_generate_diff_multiline_changes() -> None:
    """Test generating a diff with multiple line changes."""
    old_content = """Line 1
Line 2
Line 3
Line 4
Line 5
"""

    new_content = """Line 1
Line 2 modified
Line 3
New line inserted
Line 4
Line 5 changed
"""

    filepath = "multiline.txt"

    diff = generate_diff(old_content, new_content, filepath)
    assert diff != ""
    assert "--- a/multiline.txt" in diff
    assert "+++ b/multiline.txt" in diff
    assert "-Line 2" in diff
    assert "+Line 2 modified" in diff
    assert "+New line inserted" in diff
    assert "-Line 5" in diff
    assert "+Line 5 changed" in diff


def test_format_diff_for_display_no_truncation() -> None:
    diff = """--- a/file\n+++ b/file\n@@\n-Line\n+Line changed\n"""
    formatted, truncated = format_diff_for_display(diff, max_lines=10)
    assert formatted == diff
    assert truncated is False


def test_format_diff_for_display_truncates_long_diff() -> None:
    diff_lines = [f"line {i}" for i in range(120)]
    diff = "\n".join(diff_lines)
    formatted, truncated = format_diff_for_display(diff, max_lines=50)
    assert truncated is True
    assert "70 more lines not shown" in formatted
    assert formatted.endswith("Use --show-full-diff to see the complete diff.")
