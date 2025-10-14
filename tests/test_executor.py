"""Tests for the action executor."""

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


def test_read_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test reading a file."""
    # Create a test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    # Read the file
    success, message, content = executor.execute("read_file", {"path": str(test_file)})

    assert success is True
    assert "Successfully read" in message
    assert content == "Hello, World!"


def test_write_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test writing a file."""
    test_file = Path(temp_dir) / "output.txt"

    # Write the file
    success, message, content = executor.execute(
        "write_file", {"path": str(test_file), "content": "Test content"}
    )

    assert success is True
    assert "Successfully wrote" in message
    assert test_file.exists()
    assert test_file.read_text() == "Test content"


def test_list_directory(executor: ActionExecutor, temp_dir: str) -> None:
    """Test listing a directory."""
    # Create some test files
    (Path(temp_dir) / "file1.txt").touch()
    (Path(temp_dir) / "file2.txt").touch()
    (Path(temp_dir) / "subdir").mkdir()

    # List the directory
    success, message, content = executor.execute(
        "list_directory", {"path": temp_dir, "recursive": False}
    )

    assert success is True
    assert "Successfully listed" in message
    assert "file1.txt" in content
    assert "file2.txt" in content
    assert "subdir/" in content


def test_delete_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting a file."""
    # Create a test file
    test_file = Path(temp_dir) / "to_delete.txt"
    test_file.write_text("Delete me")

    # Delete the file
    success, message, content = executor.execute("delete_file", {"path": str(test_file)})

    assert success is True
    assert "Successfully deleted" in message
    assert not test_file.exists()


def test_create_directory(executor: ActionExecutor, temp_dir: str) -> None:
    """Test creating a directory."""
    new_dir = Path(temp_dir) / "new_directory"

    # Create the directory
    success, message, content = executor.execute("create_directory", {"path": str(new_dir)})

    assert success is True
    assert "Successfully created" in message
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_execute_command(executor: ActionExecutor) -> None:
    """Test executing a shell command."""
    # Execute a simple command
    success, message, content = executor.execute(
        "execute_command", {"command": "echo 'Hello from command'", "working_dir": "."}
    )

    assert success is True
    assert "Hello from command" in content


def test_get_file_info(executor: ActionExecutor, temp_dir: str) -> None:
    """Test getting file info."""
    # Create a test file
    test_file = Path(temp_dir) / "info_test.txt"
    test_file.write_text("Content")

    # Get file info
    success, message, content = executor.execute("get_file_info", {"path": str(test_file)})

    assert success is True
    assert "is_file: True" in content
    assert "size:" in content


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
    assert "--- End of" in content


def test_error_handling(executor: ActionExecutor) -> None:
    """Test error handling for non-existent file."""
    success, message, content = executor.execute("read_file", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "Failed to read" in message
