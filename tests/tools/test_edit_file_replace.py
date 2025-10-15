"""Tests for the edit_file tool - replace operations."""

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


def test_edit_file_replace_by_line_number(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing a line by line number."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Replace line 2
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced line",
            "line_number": 2,
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Should replace "Line 2" with "Replaced line\n"
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_by_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing a line by pattern."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Replace line containing "Line 2"
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
    # Should replace "Line 2" with "Replaced line\n"
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_missing_parameters(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replace operation without required parameters."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Try replace without line_number or pattern
    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "replace", "content": "Test content"}
    )

    assert success is False
    assert "Either line_number or pattern is required" in message


def test_edit_file_replace_multiple_matches_fails(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that replacing by pattern with multiple matches fails."""
    # Create a test file with multiple matching lines
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Test line\nAnother test line\nTest line again\n")

    # Try to replace lines containing "Test" - should fail because there are multiple matches
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


def test_edit_file_replace_single_match_succeeds(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that replacing by pattern with exactly one match succeeds."""
    # Create a test file with exactly one matching line
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line\nLine 3\n")

    # Replace the line containing "Test line"
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
    # Should replace "Test line" with "Replaced line\n"
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_by_pattern_substring_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing a line by pattern with substring matching."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Replace line containing "Line 2" with substring matching disabled
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced line",
            "pattern": "Line 2",
            "match_pattern_line": False,
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Should replace "Line 2" with "Replaced line\n"
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert test_file.read_text() == expected
