"""Tests for the edit_file tool."""

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


def test_edit_file_corruption_validation_reverts(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that file corruption validation reverts changes when file becomes unreadable."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    original_content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(original_content)

    # Try to perform an operation that would corrupt the file (insert invalid content at invalid line)  # noqa: E501
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert",
            "content": "Inserted line",
            "line_number": 100,  # This should cause an error
        },
    )

    # The operation should fail and the file content should remain unchanged
    assert success is False
    assert "Invalid line number" in message or "corrupted after edit" in message
    assert test_file.read_text() == original_content


def test_edit_file_corruption_validation_passes_when_valid(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test that file corruption validation passes for valid operations."""
    # Create a test file
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Perform a valid edit operation
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "content": "Replaced line",
            "line_number": 2,
        },
    )

    # The operation should succeed
    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify content is readable and changed
    assert test_file.read_text() == "Line 1\nReplaced line\nLine 3\n"


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
