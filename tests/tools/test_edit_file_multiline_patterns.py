"""Tests for edit_file tool - multi-line pattern matching."""

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


def test_edit_file_replace_multiline_pattern_exact_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing a line within a multi-line context."""
    # Create a test file with the multi-line pattern
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function1():\n"
        "    try:\n"
        "        risky_operation()\n"
        "    except:\n"
        "        pass\n"
        "\n"
        "def function2():\n"
        "    return 42\n"
    )

    # Try to replace the except line
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:",
            "content": "    except OSError:",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = (
        "def function1():\n"
        "    try:\n"
        "        risky_operation()\n"
        "    except OSError:\n"
        "        pass\n"
        "\n"
        "def function2():\n"
        "    return 42\n"
    )
    assert test_file.read_text() == expected


def test_edit_file_replace_multiline_pattern_three_lines(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test deleting multiple lines and inserting a single line."""
    # Create a test file with a three-line pattern
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function():\n"
        "    # TODO: This is a temporary\n"
        "    # implementation that needs\n"
        "    # to be replaced\n"
        "    return None\n"
    )

    # Delete all three TODO comment lines (using multi-line pattern)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": (
                "    # TODO: This is a temporary\n"
                "    # implementation that needs\n"
                "    # to be replaced"
            ),
        },
    )

    assert success is True

    # Insert the final implementation
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "pattern": "return None",
            "content": "# This is the final implementation",
        },
    )

    assert success is True
    # Verify the replacement worked
    expected = "def function():\n    # This is the final implementation\n    return None\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_multiline_pattern_trailing_newline(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test deleting multiple lines and inserting a replacement."""
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("alpha\nbeta\nomega\n")

    # Delete alpha line
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "alpha",
        },
    )
    assert success is True

    # Delete beta line
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "beta",
        },
    )
    assert success is True

    # Insert gamma before omega
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "pattern": "omega",
            "content": "gamma",
        },
    )

    assert success is True
    assert test_file.read_text() == "gamma\nomega\n"


def test_edit_file_delete_multiline_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting multiple lines with a pattern."""
    # Create a test file with a multi-line pattern to delete
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function():\n"
        "    try:\n"
        "        risky_operation()\n"
        "    except:\n"
        "        pass\n"
        "    # This comment should stay\n"
        "    return True\n"
    )

    # Delete the except and pass lines (multi-line pattern)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "    except:\n        pass",
        },
    )

    assert success is True
    assert "Successfully performed delete operation" in message
    # Verify the deletion worked
    expected = (
        "def function():\n"
        "    try:\n"
        "        risky_operation()\n"
        "    # This comment should stay\n"
        "    return True\n"
    )
    assert test_file.read_text() == expected


def test_edit_file_replace_multiline_pattern_fails_with_ambiguous_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test that pattern replacement fails when multiple matches exist."""
    # Create a test file with multiple similar patterns
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function1():\n"
        "    try:\n"
        "        risky_operation()\n"
        "    except:\n"
        "        pass\n"
        "\n"
        "def function2():\n"
        "    try:\n"
        "        another_operation()\n"
        "    except:\n"
        "        pass\n"
    )

    # Try to replace the except line - should fail because there are multiple matches
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:",
            "content": "    except OSError:",
        },
    )

    assert success is False
    assert "found 2 times, expected exactly one match" in message


def test_edit_file_replace_multiline_pattern_not_found(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern replacement when pattern is not found."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function():\n    try:\n        risky_operation()\n    except OSError:\n        pass\n"
    )

    # Try to replace a pattern that doesn't exist
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except ValueError:",
            "content": "except TypeError:",
        },
    )

    assert success is False
    assert "not found in file" in message


def test_edit_file_replace_multiline_pattern_empty_lines(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern replacement with empty lines in the file."""
    # Create a test file with empty lines in the pattern
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function():\n"
        "    try:\n"
        "        risky_operation()\n"
        "\n"  # Empty line
        "    except:\n"
        "        pass\n"
    )

    # Replace just the except line
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:",
            "content": "    except OSError:",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = (
        "def function():\n"
        "    try:\n"
        "        risky_operation()\n"
        "\n"
        "    except OSError:\n"
        "        pass\n"
    )
    assert test_file.read_text() == expected
