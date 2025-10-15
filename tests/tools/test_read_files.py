"""Tests for the read_files tool."""

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


def test_read_files(executor: ActionExecutor, temp_dir: str) -> None:
    """Test reading multiple files."""
    # Create test files
    test_file1 = Path(temp_dir) / "test1.txt"
    test_file1.write_text("Content of file 1")

    test_file2 = Path(temp_dir) / "test2.txt"
    test_file2.write_text("Content of file 2")

    test_file3 = Path(temp_dir) / "test3.txt"
    test_file3.write_text("Content of file 3")

    # Read multiple files
    success, message, content = executor.execute(
        "read_files", {"paths": [str(test_file1), str(test_file2), str(test_file3)]}
    )

    assert success is True
    assert "Successfully read 3 files" in message
    assert "--- Contents of" in content
    assert "Content of file 1" in content
    assert "Content of file 2" in content
    assert "Content of file 3" in content
    assert "--- End of" in content


def test_read_files_with_nonexistent_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test reading multiple files where one doesn't exist."""
    # Create test files
    test_file1 = Path(temp_dir) / "existing1.txt"
    test_file1.write_text("Content of existing file 1")

    test_file2 = Path(temp_dir) / "existing2.txt"
    test_file2.write_text("Content of existing file 2")

    nonexistent_file = Path(temp_dir) / "nonexistent.txt"

    # Read multiple files including one that doesn't exist
    success, message, content = executor.execute(
        "read_files", {"paths": [str(test_file1), str(nonexistent_file), str(test_file2)]}
    )

    assert success is True
    assert "Successfully read 3 files" in message
    assert "--- Contents of" in content
    assert "Content of existing file 1" in content
    assert "Content of existing file 2" in content
    assert "--- Failed to read" in content
    assert str(nonexistent_file) in content
    assert "--- End of" in content
