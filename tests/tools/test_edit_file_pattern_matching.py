"""Tests for edit_file tool - pattern matching edge cases."""

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


def test_edit_file_replace_bare_except_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing a bare except clause - this should work with exact matching."""
    # Create a test file with the problematic pattern
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("try:\n    do_something()\nexcept:\n    pass\n")

    # Try to replace the bare except with specific exception
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except OSError:",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = "try:\n    do_something()\nexcept OSError:\n    pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_pattern_with_exact_whitespace(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing a pattern with specific indentation and whitespace."""
    # Create a test file with indented bare except
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("        except:\n            pass\n")

    # Try to replace the indented except clause
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "        except:",
            "content": "        except OSError:",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked with exact indentation
    expected = "        except OSError:\n            pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_pattern_fails_with_ambiguous_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test that pattern replacement fails when multiple matches exist."""
    # Create a test file with multiple similar patterns
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "try:\n"
        "    do_something()\n"
        "except:\n"
        "    pass\n"
        "try:\n"
        "    do_something_else()\n"
        "except:\n"
        "    pass\n"
    )

    # Try to replace bare except - should fail because there are multiple matches
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except OSError:",
        },
    )

    assert success is False
    assert "found 2 times, expected exactly one match" in message


def test_edit_file_replace_pattern_case_sensitive(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that pattern matching is case-sensitive (exact match)."""
    # Create a test file with mixed case
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("try:\n    do_something()\nEXCEPT:\n    pass\n")

    # Try to replace using exact case match
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "EXCEPT:",  # Must match exact case
            "content": "except OSError:",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = "try:\n    do_something()\nexcept OSError:\n    pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_pattern_substring_match(executor: ActionExecutor, temp_dir: str) -> None:
    """Test pattern matching when pattern is a substring of a line."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("    except Exception as e:\n        pass\n")

    # Try to replace using just "except Exception" - should work
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except Exception",
            "content": "except OSError",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked - indentation should be preserved
    expected = "    except OSError as e:\n        pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_pattern_exact_match_disabled(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern matching with exact matching disabled."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("    except Exception as e:\n        pass\n")

    # Try to replace using pattern matching
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except Exception as e:",
            "content": "except OSError as e:",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked - indentation should be preserved
    expected = "    except OSError as e:\n        pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_pattern_not_found(executor: ActionExecutor, temp_dir: str) -> None:
    """Test pattern replacement when pattern is not found."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("try:\n    do_something()\nexcept ValueError:\n    pass\n")

    # Try to replace a pattern that doesn't exist
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except TypeError:",
            "content": "except OSError:",
        },
    )

    assert success is False
    assert "Pattern 'except TypeError:' not found in file" in message


def test_edit_file_replace_pattern_with_special_characters(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern replacement with special regex characters."""
    # Create a test file with special characters
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text('print("Hello (world)!")\nprint("Another [test] here")\n')

    # Try to replace pattern with parentheses (need to escape them for regex)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": 'print\\("Hello \\(world\\)!"\\)',
            "content": 'print("Hello [world]!")',
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = 'print("Hello [world]!")\nprint("Another [test] here")\n'
    assert test_file.read_text() == expected


def test_edit_file_replace_pattern_multiline_context(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern replacement in multiline context to ensure line-level matching works."""
    # Create a test file with multiline structure
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

    # Try to replace just the bare except in function1
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
    # Verify the replacement worked and other parts are unchanged
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
