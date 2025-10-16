"""Tests for the edit_file tool - error cases."""

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


def test_edit_file_not_found(executor: ActionExecutor) -> None:
    """Test editing a non-existent file."""
    success, message, content = executor.execute(
        "edit_file",
        {"path": "/nonexistent/file.txt", "operation": "append", "content": "Test content"},
    )

    assert success is False
    assert "File not found" in message


def test_edit_file_invalid_operation(executor: ActionExecutor, temp_dir: str) -> None:
    """Test edit file with invalid operation."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Try invalid operation
    success, message, content = executor.execute(
        "edit_file",
        {"path": str(test_file), "operation": "invalid_operation", "content": "Test content"},
    )

    assert success is False
    assert "Unknown operation" in message


def test_edit_file_corruption_validation_reverts(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that file corruption validation handles invalid operations gracefully."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    original_content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(original_content)

    # Try an invalid operation
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "invalid_op",
            "content": "Some content",
        },
    )

    # The operation should fail and the file content should remain unchanged
    assert success is False
    assert "Unknown operation" in message
    assert test_file.read_text() == original_content


def test_edit_file_corruption_validation_passes_when_valid(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test that file corruption validation passes for valid operations."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Perform a valid edit operation using pattern-based replace
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "Line 2",
            "content": "Replaced line",
            "match_pattern_line": False,  # Use substring matching
        },
    )

    # The operation should succeed
    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify content is readable and changed
    assert test_file.read_text() == "Line 1\nReplaced line\nLine 3\n"
