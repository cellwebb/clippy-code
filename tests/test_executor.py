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


def test_read_file_not_found(executor: ActionExecutor) -> None:
    """Test reading a non-existent file."""
    success, message, content = executor.execute("read_file", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "File not found" in message


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


def test_write_file_permission_denied(executor: ActionExecutor, temp_dir: str) -> None:
    """Test writing to a file without permission."""
    # Try to write to a protected path
    test_file = "/root/protected_file.txt"

    # This might not work on all systems, so we just check that it handles the error gracefully
    success, message, content = executor.execute(
        "write_file", {"path": test_file, "content": "Test content"}
    )

    # Should fail, but gracefully
    assert success is False
    assert (
        "Error executing write_file" in message
        or "Permission denied" in message
        or "OS error" in message
    )


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


def test_list_directory_not_found(executor: ActionExecutor) -> None:
    """Test listing a non-existent directory."""
    success, message, content = executor.execute(
        "list_directory", {"path": "/nonexistent/directory", "recursive": False}
    )

    assert success is False
    assert "Directory not found" in message


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


def test_delete_file_not_found(executor: ActionExecutor) -> None:
    """Test deleting a non-existent file."""
    success, message, content = executor.execute("delete_file", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "File not found" in message


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


def test_get_file_info_not_found(executor: ActionExecutor) -> None:
    """Test getting info for a non-existent file."""
    success, message, content = executor.execute("get_file_info", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "File not found" in message


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


def test_grep(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality."""
    # Create test files
    test_file = Path(temp_dir) / "grep_test.txt"
    test_file.write_text("Hello World\nThis is a test\nAnother line")

    # Search for pattern in file
    success, message, content = executor.execute(
        "grep", {"pattern": "test", "paths": [str(test_file)], "flags": "-i"}
    )

    # grep returns 0 when matches are found
    assert success is True
    assert "search executed successfully" in message or "search completed" in message
    assert "This is a test" in content


def test_grep_no_matches(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep with no matches."""
    # Create test file
    test_file = Path(temp_dir) / "grep_test.txt"
    test_file.write_text("Hello World\nThis is a test\nAnother line")

    # Search for pattern that doesn't exist
    success, message, content = executor.execute(
        "grep", {"pattern": "nonexistent", "paths": [str(test_file)], "flags": ""}
    )

    # grep returns 1 when no matches found, which we treat as success
    assert success is True
    assert "no matches found" in message


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
