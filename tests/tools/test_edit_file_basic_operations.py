"""Tests for basic edit_file operations: append, delete, and replace."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


@pytest.fixture
def executor() -> ActionExecutor:
    """Create an executor instance."""
    manager = PermissionManager()
    return ActionExecutor(manager)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# APPEND OPERATIONS
# ============================================================================


def test_edit_file_append(executor: ActionExecutor, temp_dir: str) -> None:
    """Test appending content to a file."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "append", "content": "Appended line"}
    )

    assert success is True
    assert "Successfully performed append operation" in message
    expected = "Line 1\nLine 2\nLine 3\nAppended line\n"
    assert test_file.read_text() == expected


def test_edit_file_append_to_file_without_trailing_newline(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test appending to a file that doesn't end with a newline."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "append", "content": "Appended line"}
    )

    assert success is True
    assert "Successfully performed append operation" in message
    expected = "Line 1\nLine 2\nLine 3\nAppended line\n"
    assert test_file.read_text() == expected


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


def test_edit_file_delete_by_pattern_exact_line(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting a line by exact string match (must match full line content exactly)."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line\nLine 3\nAnother Test line\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "Test line",  # Exact string match (substring)
        },
    )

    assert success is True
    assert "Successfully performed delete operation" in message
    # Pattern matches twice, so both occurrences are removed.
    expected = "Line 1\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_delete_by_pattern_substring_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test deleting lines by exact substring match (case-sensitive)."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line\nLine 3\nAnother test line\nFull test line\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "test line",  # Exact substring (case-sensitive)
        },
    )

    assert success is True
    assert "Successfully performed delete operation" in message
    # Matches "Another test line" and "Full test line" (lowercase "test")
    expected = "Line 1\nTest line\nLine 3\n"
    assert test_file.read_text() == expected


# ============================================================================
# REPLACE OPERATIONS
# ============================================================================


def test_edit_file_replace_by_pattern_exact_line(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing a line by exact pattern match (using regex substitution)."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced line",
            "pattern": "Line 2",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_by_pattern_substring_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing a substring within a line using regex substitution."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2 with extra content\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced",
            "pattern": "Line 2",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    expected = "Line 1\nReplaced with extra content\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_single_match_succeeds(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that replacing by pattern with exactly one match succeeds."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced line",
            "pattern": "Test line",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_multiple_matches_fails(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that replacing by pattern with multiple matches fails."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Test line\nAnother Test line\nTest line again\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced line",
            "pattern": "Test",
        },
    )

    assert success is False
    assert "Pattern 'Test' found 3 times, expected exactly one match" in message


def test_edit_file_replace_missing_parameters(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replace operation without required parameters."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "replace", "content": "Test content"}
    )

    assert success is False
    assert "Pattern is required for replace operation" in message
