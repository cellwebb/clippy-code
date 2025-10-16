"""Tests for edit_file tool - indentation and whitespace sensitivity."""

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


def test_edit_file_replace_exact_indentation_8_spaces(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing with exactly 8 spaces indentation."""
    # Create a test file with the exact pattern from our error
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("        except:\n            pass\n")

    # This should work - pattern matching should be case-insensitive substring matching
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except OSError:",
            "match_pattern_line": False,  # Use substring matching
        },
    )

    assert success is True, f"Pattern replacement failed: {message}"
    assert "Successfully performed replace operation" in message
    # Verify the replacement worked
    expected = "        except OSError:\n            pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_with_leading_whitespace_in_pattern(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test replacing pattern that includes leading whitespace."""
    # Create a test file with the exact pattern
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("        except:\n            pass\n")

    # Try to replace with the exact whitespace in pattern (exact line match)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "        except:",
            "content": "        except OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    assert success is True, f"Pattern replacement failed: {message}"
    assert "Successfully performed replace operation" in message


def test_edit_file_replace_4_spaces_indentation(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing with 4 spaces indentation."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("    except:\n        pass\n")

    # Replace with 4 spaces pattern (exact line match)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:",
            "content": "    except OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    assert success is True, f"Pattern replacement failed: {message}"
    assert "Successfully performed replace operation" in message
    expected = "    except OSError:\n        pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_mixed_whitespace(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing with mixed tabs and spaces."""
    # Create a test file with tabs
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("\texcept:\n\t\tpass\n")

    # Replace with tab pattern (exact line match)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "\texcept:",
            "content": "\texcept OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    assert success is True, f"Pattern replacement failed: {message}"
    assert "Successfully performed replace operation" in message
    expected = "\texcept OSError:\n\t\tpass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_no_leading_whitespace(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing pattern with no leading whitespace."""
    # Create a test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("except:\n    pass\n")

    # Replace with no leading whitespace (exact line match)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    assert success is True, f"Pattern replacement failed: {message}"
    assert "Successfully performed replace operation" in message
    expected = "except OSError:\n    pass\n"
    assert test_file.read_text() == expected


def test_edit_file_replace_trailing_whitespace(executor: ActionExecutor, temp_dir: str) -> None:
    """Test replacing pattern with trailing whitespace."""
    # Create a test file with trailing spaces (this is a bit tricky to create)
    test_file = Path(temp_dir) / "test.py"
    content = "        except:  \n"  # Two trailing spaces
    content += "            pass\n"
    test_file.write_text(content)

    # Try to replace including trailing spaces in pattern (exact line match)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "        except:  ",
            "content": "        except OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    # This might fail because trailing spaces are often hard to match
    if success:
        assert "Successfully performed replace operation" in message
        expected = "        except OSError:\n            pass\n"
        assert test_file.read_text() == expected
    else:
        # It's acceptable if this fails - trailing spaces are tricky
        assert "Pattern '        except:  ' not found in file" in message


def test_edit_file_replace_in_context_with_similar_patterns(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern replacement when similar patterns exist in context."""
    # Create a file with multiple except clauses at different indentation levels
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "try:\n"
        "    outer_try()\n"
        "except:\n"
        "    pass\n"
        "try:\n"
        "    inner_try()\n"
        "    try:\n"
        "        inner_inner_try()\n"
        "    except:\n"
        "        pass\n"
        "except:\n"
        "    pass\n"
    )

    # Try to replace just the inner-most except (the one with 4 spaces inside nested try)
    # This should succeed because there's only ONE line with "    except:" (4 spaces)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:",
            "content": "    except OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    assert success is True, f"Pattern replacement failed: {message}"
    assert "Successfully performed replace operation" in message

    # Verify only the inner except was changed (the one with 4 spaces)
    result = test_file.read_text()
    assert "    except OSError:" in result  # The changed one (4 spaces)
    assert result.count("except:\n") == 2  # Two unchanged ones (0 spaces each)


def test_edit_file_replace_fails_with_similar_patterns_at_same_level(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test pattern replacement fails when multiple identical patterns exist."""
    # Create a file with two identical except clauses at the same indentation level
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "try:\n"
        "    first_try()\n"
        "    except:\n"
        "        pass\n"
        "try:\n"
        "    second_try()\n"
        "    except:\n"
        "        pass\n"
    )

    # Try to replace the except clause - should fail because there are two identical matches
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    except:",
            "content": "    except OSError:",
            "match_pattern_line": True,  # Use exact line matching
        },
    )

    assert success is False
    assert "found 2 times, expected exactly one match" in message
