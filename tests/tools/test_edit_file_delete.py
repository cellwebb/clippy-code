"""Tests for the edit_file tool - delete operations."""

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


def test_edit_file_delete_by_line_number(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting a line by line number."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Delete line 2
    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "delete", "line_number": 2}
    )

    assert success is True
    assert "Successfully performed delete operation" in message
    # Should remove "Line 2\n"
    expected = "Line 1\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_delete_by_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting lines by pattern."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line\nLine 3\nAnother test line\n")

    # Delete lines containing "test" (case insensitive)
    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "delete", "pattern": "Test"}
    )

    assert success is True
    assert "Successfully performed delete operation" in message
    # Should remove "Test line\n" and "Another test line\n"
    expected = "Line 1\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_delete_by_pattern_substring_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test deleting lines by pattern with substring matching disabled."""
    # Create a test file with lines that partially match the pattern
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line\nLine 3\nAnother test line\nFull test line\n")

    # Delete lines that exactly match "test" (not substring matching)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "Test line",
            "match_pattern_line": False,
        },
    )

    assert success is True
    assert "Successfully performed delete operation" in message
    # Should only remove the line that exactly matches "Test line"
    expected = "Line 1\nLine 3\nAnother test line\nFull test line\n"
    assert test_file.read_text() == expected
