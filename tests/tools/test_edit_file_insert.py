"""Tests for the edit_file tool - insert operations."""

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


def test_edit_file_insert(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting lines into a file."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Insert a line at position 2
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert",
            "content": "Inserted line",
            "line_number": 2,
        },
    )

    assert success is True
    assert "Successfully performed insert operation" in message
    # Should insert "Inserted line\n" before "Line 2"
    expected = "Line 1\nInserted line\nLine 2\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_insert_invalid_line_number(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting at an invalid line number."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Try to insert at invalid line number (beyond the file)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert",
            "content": "Test content",
            "line_number": 10,
        },
    )

    assert success is False
    assert "Invalid line number" in message


def test_edit_file_insert_at_beginning(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting a line at the beginning of a file."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Insert a line at the beginning
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert",
            "content": "First line",
            "line_number": 1,
        },
    )

    assert success is True
    assert "Successfully performed insert operation" in message
    # Should insert "First line\n" at the beginning
    expected = "First line\nLine 1\nLine 2\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_insert_at_end(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting a line at the end of a file."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Insert a line at the end
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert",
            "content": "Last line",
            "line_number": 4,
        },
    )

    assert success is True, f"Operation failed: {message}"
    assert "Successfully performed insert operation" in message
    # Should insert "Last line\n" at the end
    expected = "Line 1\nLine 2\nLine 3\nLast line\n"
    assert test_file.read_text() == expected


def test_edit_file_insert_into_empty_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting into an empty file."""
    # Create an empty test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("")

    # Insert a line into empty file
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert",
            "content": "First line",
            "line_number": 1,
        },
    )

    assert success is True, f"Operation failed: {message}"
    assert "Successfully performed insert operation" in message
    # Should contain just the inserted line
    expected = "First line\n"
    assert test_file.read_text() == expected
