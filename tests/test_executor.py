"""Tests for the action executor."""

import os
import tempfile
from pathlib import Path

import pytest
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


@pytest.fixture
def executor():
    """Create an executor instance."""
    manager = PermissionManager()
    return ActionExecutor(manager)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_read_file(executor, temp_dir):
    """Test reading a file."""
    # Create a test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    # Read the file
    success, message, content = executor.execute("read_file", {"path": str(test_file)})

    assert success is True
    assert "Successfully read" in message
    assert content == "Hello, World!"


def test_write_file(executor, temp_dir):
    """Test writing a file."""
    test_file = Path(temp_dir) / "output.txt"

    # Write the file
    success, message, _ = executor.execute(
        "write_file",
        {"path": str(test_file), "content": "Test content"}
    )

    assert success is True
    assert "Successfully wrote" in message
    assert test_file.exists()
    assert test_file.read_text() == "Test content"


def test_list_directory(executor, temp_dir):
    """Test listing a directory."""
    # Create some test files
    (Path(temp_dir) / "file1.txt").touch()
    (Path(temp_dir) / "file2.txt").touch()
    (Path(temp_dir) / "subdir").mkdir()

    # List the directory
    success, message, result = executor.execute(
        "list_directory",
        {"path": temp_dir, "recursive": False}
    )

    assert success is True
    assert "Successfully listed" in message
    assert "file1.txt" in result
    assert "file2.txt" in result
    assert "subdir/" in result


def test_delete_file(executor, temp_dir):
    """Test deleting a file."""
    # Create a test file
    test_file = Path(temp_dir) / "to_delete.txt"
    test_file.write_text("Delete me")

    # Delete the file
    success, message, _ = executor.execute("delete_file", {"path": str(test_file)})

    assert success is True
    assert "Successfully deleted" in message
    assert not test_file.exists()


def test_create_directory(executor, temp_dir):
    """Test creating a directory."""
    new_dir = Path(temp_dir) / "new_directory"

    # Create the directory
    success, message, _ = executor.execute("create_directory", {"path": str(new_dir)})

    assert success is True
    assert "Successfully created" in message
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_execute_command(executor):
    """Test executing a shell command."""
    # Execute a simple command
    success, message, output = executor.execute(
        "execute_command",
        {"command": "echo 'Hello from command'", "working_dir": "."}
    )

    assert success is True
    assert "Hello from command" in output


def test_get_file_info(executor, temp_dir):
    """Test getting file info."""
    # Create a test file
    test_file = Path(temp_dir) / "info_test.txt"
    test_file.write_text("Content")

    # Get file info
    success, message, result = executor.execute("get_file_info", {"path": str(test_file)})

    assert success is True
    assert "is_file: True" in result
    assert "size:" in result


def test_error_handling(executor):
    """Test error handling for non-existent file."""
    success, message, _ = executor.execute("read_file", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "Failed to read" in message
