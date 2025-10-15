"""Tests for the edit_file tool - append operations."""

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


def test_edit_file_append(executor: ActionExecutor, temp_dir: str) -> None:
    """Test appending content to a file."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    # Append content
    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "append", "content": "Appended line"}
    )

    assert success is True
    assert "Successfully performed append operation" in message
    # Should append with proper line ending
    expected = "Line 1\nLine 2\nLine 3\nAppended line\n"
    assert test_file.read_text() == expected


def test_edit_file_append_to_file_without_trailing_newline(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test appending to a file that doesn't end with a newline."""
    # Create a test file without trailing newline
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    # Append content
    success, message, content = executor.execute(
        "edit_file", {"path": str(test_file), "operation": "append", "content": "Appended line"}
    )

    assert success is True
    assert "Successfully performed append operation" in message
    # Should append with proper line ending, adding newline to existing last line as well
    expected = "Line 1\nLine 2\nLine 3\nAppended line\n"
    assert test_file.read_text() == expected
