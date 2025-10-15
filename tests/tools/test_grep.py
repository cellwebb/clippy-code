"""Tests for the grep functionality."""

from pathlib import Path

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig


def test_grep_action_is_auto_approved() -> None:
    """Test that the GREP action type is in the auto-approved set."""
    config = PermissionConfig()

    # The GREP action should be auto-approved
    assert ActionType.GREP in config.auto_approve
    assert config.can_auto_execute(ActionType.GREP) is True


def test_grep_single_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality on a single file."""
    # Create a test file with content
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!\nThis is a test file.\nHello again!")

    # Search for "Hello" in the file
    success, message, content = executor.execute(
        "grep", {"pattern": "Hello", "paths": [str(test_file)]}
    )

    assert success is True
    assert "grep search executed successfully" in message or "grep search completed" in message
    assert "Hello, World!" in content
    assert "Hello again!" in content


def test_grep_multiple_files(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality on multiple files."""
    # Create test files with content
    test_file1 = Path(temp_dir) / "file1.txt"
    test_file1.write_text("First file\nContains pattern\nMore content")

    test_file2 = Path(temp_dir) / "file2.txt"
    test_file2.write_text("Second file\nDifferent content\nNo match here")

    test_file3 = Path(temp_dir) / "file3.txt"
    test_file3.write_text("Third file\nAlso contains pattern\nFinal content")

    # Search for "pattern" in all files
    success, message, content = executor.execute(
        "grep", {"pattern": "pattern", "paths": [str(test_file1), str(test_file2), str(test_file3)]}
    )

    assert success is True
    assert "grep search executed successfully" in message or "grep search completed" in message
    assert "file1.txt" in content
    assert "file3.txt" in content
    assert "Contains pattern" in content
    assert "Also contains pattern" in content


def test_grep_with_flags(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality with flags."""
    # Create a test file with content
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!\nThis is a TEST file.\nHello again!")

    # Search for "test" case insensitive
    success, message, content = executor.execute(
        "grep", {"pattern": "test", "paths": [str(test_file)], "flags": "-i"}
    )

    assert success is True
    assert "grep search executed successfully" in message or "grep search completed" in message
    assert "This is a TEST file." in content


def test_grep_no_matches(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality when no matches are found."""
    # Create a test file with content
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!\nThis is a test file.\nHello again!")

    # Search for a pattern that doesn't exist
    success, message, content = executor.execute(
        "grep", {"pattern": "nonexistent", "paths": [str(test_file)]}
    )

    assert success is True
    assert "grep search completed (no matches found)" in message


def test_grep_with_glob_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality with glob patterns."""
    # Create test files with content
    test_file1 = Path(temp_dir) / "file1.txt"
    test_file1.write_text("First file\nContains pattern\nMore content")

    test_file2 = Path(temp_dir) / "file2.py"
    test_file2.write_text("Second file\nDifferent content\nNo match here")

    test_file3 = Path(temp_dir) / "file3.txt"
    test_file3.write_text("Third file\nAlso contains pattern\nFinal content")

    # Search for "pattern" in all .txt files using glob pattern
    success, message, content = executor.execute(
        "grep", {"pattern": "pattern", "paths": [str(Path(temp_dir) / "*.txt")]}
    )

    assert success is True
    assert "grep search executed successfully" in message or "grep search completed" in message
    assert "file1.txt" in content
    assert "file3.txt" in content
    assert "Contains pattern" in content
    assert "Also contains pattern" in content
    # Should not contain file2.py results
    assert "file2.py" not in content
