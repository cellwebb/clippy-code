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
    """Test replacing a multi-line pattern with exact matching."""
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

    # Try to replace the multi-line except block
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:\n        pass",
            "content": "    except OSError:\n        pass",
            "match_pattern_line": True,  # Use exact line matching
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
    """Test replacing a three-line multi-line pattern."""
    # Create a test file with a three-line pattern
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function():\n"
        "    # TODO: This is a temporary\n"
        "    # implementation that needs\n"
        "    # to be replaced\n"
        "    return None\n"
    )

    # Try to replace the three-line TODO comment
    pattern = (
        "    # TODO: This is a temporary\n    # implementation that needs\n    # to be replaced"
    )
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": pattern,
            "content": "    # This is the final implementation",
            "match_pattern_line": True,
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = "def function():\n    # This is the final implementation\n    return None\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_multiline_pattern_trailing_newline(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing a multi-line pattern that ends with a trailing newline."""
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("alpha\nbeta\nomega\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "alpha\nbeta\n",
            "content": "gamma\n",
            "match_pattern_line": True,
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    assert test_file.read_text() == "gamma\nomega\n"


def test_edit_file_delete_multiline_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting a multi-line pattern."""
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

    # Try to delete the multi-line except block
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "    except:\n        pass",
            "match_pattern_line": True,
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
    """Test that multi-line pattern replacement fails when multiple matches exist."""
    # Create a test file with multiple similar multi-line patterns
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

    # Try to replace the multi-line except block - should fail because there are multiple matches
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:\n        pass",
            "content": "    except OSError:\n        pass",
            "match_pattern_line": True,
        },
    )

    assert success is False
    assert "found 2 times, expected exactly one match" in message


def test_edit_file_replace_multiline_pattern_not_found(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test multi-line pattern replacement when pattern is not found."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def function():\n    try:\n        risky_operation()\n    except OSError:\n        pass\n"
    )

    # Try to replace a multi-line pattern that doesn't exist
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except ValueError:\n        pass",
            "content": "    except TypeError:\n        pass",
            "match_pattern_line": True,
        },
    )

    assert success is False
    assert "Pattern '    except ValueError:\n        pass' not found in file" in message


def test_edit_file_replace_multiline_pattern_empty_lines(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test multi-line pattern replacement with empty lines."""
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

    # Try to replace a pattern that includes an empty line
    pattern = "\n    except:\n        pass"  # Pattern starts with empty line
    replacement = "\n    except OSError:\n        pass"
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": pattern,
            "content": replacement,
            "match_pattern_line": True,
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
