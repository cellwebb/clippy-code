"""Tests for edit_file tool - real-world scenarios and issues."""

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


# ============================================================================
# BARE EXCEPT CLAUSE FIXES (Real-world issue)
# ============================================================================


def test_real_world_bare_except_issue(executor: ActionExecutor, temp_dir: str) -> None:
    """Test the exact issue encountered: fixing bare except clause in agent_utils.py."""
    test_file = Path(temp_dir) / "agent_utils.py"
    test_file.write_text(
        "    except Exception as e:\n"
        "        # Clean up temp file if it exists\n"
        "        try:\n"
        "            if 'tmp_path' in locals():\n"
        "                os.unlink(tmp_path)\n"
        "        except:\n"
        "            pass\n"
        '        return False, f"Failed to write to {path}: {str(e)}"\n'
    )

    # Fix using exact line matching
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "        except:",
            "content": "        except OSError:",
        },
    )

    assert success is True, f"Failed to replace bare except: {message}"
    assert "Successfully performed replace operation" in message

    result = test_file.read_text()
    assert "        except OSError:" in result
    assert "        return False" in result
    assert "# Clean up temp file if it exists" in result

    lines = result.splitlines()
    for line in lines:
        if "except OSError:" in line:
            assert line.startswith("        ")  # 8 spaces


def test_real_world_bare_except_with_substring_match(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test fixing bare except using substring matching."""
    test_file = Path(temp_dir) / "agent_utils.py"
    test_file.write_text(
        "    except Exception as e:\n"
        "        # Clean up temp file if it exists\n"
        "        try:\n"
        "            if 'tmp_path' in locals():\n"
        "                os.unlink(tmp_path)\n"
        "        except:\n"
        "            pass\n"
        '        return False, f"Failed to write to {path}: {str(e)}"\n'
    )

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except OSError:",
        },
    )

    assert success is True, f"Failed to replace bare except: {message}"

    expected_content = (
        "    except Exception as e:\n"
        "        # Clean up temp file if it exists\n"
        "        try:\n"
        "            if 'tmp_path' in locals():\n"
        "                os.unlink(tmp_path)\n"
        "        except OSError:\n"
        "            pass\n"
        '        return False, f"Failed to write to {path}: {str(e)}"\n'
    )
    assert test_file.read_text() == expected_content


def test_real_world_bare_except_with_delete_and_insert(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test fixing bare except using delete + insert operations."""
    test_file = Path(temp_dir) / "agent_utils.py"
    original_content = (
        "    except Exception as e:\n"
        "        # Clean up temp file if it exists\n"
        "        try:\n"
        "            if 'tmp_path' in locals():\n"
        "                os.unlink(tmp_path)\n"
        "        except:\n"
        "            pass\n"
        '        return False, f"Failed to write to {path}: {str(e)}"\n'
    )
    test_file.write_text(original_content)

    # Delete the bare except line
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "delete",
            "pattern": "        except:",
        },
    )
    assert success is True, f"Failed to delete bare except: {message}"

    # Insert the corrected except before the pass statement
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "pattern": "            pass",
            "content": "        except OSError:",
            "inherit_indent": False,
        },
    )
    assert success is True, f"Failed to insert correct except: {message}"

    expected_content = (
        "    except Exception as e:\n"
        "        # Clean up temp file if it exists\n"
        "        try:\n"
        "            if 'tmp_path' in locals():\n"
        "                os.unlink(tmp_path)\n"
        "        except OSError:\n"
        "            pass\n"
        '        return False, f"Failed to write to {path}: {str(e)}"\n'
    )
    assert test_file.read_text() == expected_content


# ============================================================================
# WHITESPACE SENSITIVITY
# ============================================================================


def test_real_world_whitespace_sensitivity_issue(executor: ActionExecutor, temp_dir: str) -> None:
    """Test the whitespace sensitivity issue with pattern matching."""
    test_file = Path(temp_dir) / "test.py"
    content = "        except:\n            pass\n"
    test_file.write_text(content)

    # Multiple approaches should all work
    approaches = [
        {"pattern": "except:", "content": "except OSError:"},
        {
            "pattern": "        except:",
            "content": "        except OSError:",
        },
    ]

    for i, approach in enumerate(approaches):
        test_file.write_text(content)

        success, message, result = executor.execute(
            "edit_file",
            {"path": str(test_file), "operation": "replace", **approach},
        )

        assert success is True, f"Approach {i + 1} failed: {message}"
        assert "Successfully performed replace operation" in message

        result_content = test_file.read_text()
        assert "except OSError:" in result_content
        assert "            pass" in result_content


def test_whitespace_preservation_in_replacement(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that replacement operations preserve whitespace correctly."""
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text(
        "def test():\n    if True:\n        print('hello')\n        return True\n    return False\n"
    )

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "        print\\('hello'\\)",
            "content": "        print('hello world')",
        },
    )

    assert success is True
    expected_content = (
        "def test():\n"
        "    if True:\n"
        "        print('hello world')\n"
        "        return True\n"
        "    return False\n"
    )
    assert test_file.read_text() == expected_content


# ============================================================================
# FILE STRUCTURE PRESERVATION
# ============================================================================


def test_edit_file_no_line_number_corruption(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that pattern-based edits don't corrupt file structure."""
    test_file = Path(temp_dir) / "test.py"
    original_content = (
        "def function():\n    # Line 1\n    # Line 2\n    # Line 3\n    return True\n"
    )
    test_file.write_text(original_content)

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "    # Line 2",
            "content": "    # Modified line 2",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message

    result = test_file.read_text()
    lines = result.splitlines()
    assert len(lines) == 5
    assert lines[0] == "def function():"
    assert lines[1] == "    # Line 1"
    assert lines[2] == "    # Modified line 2"
    assert lines[3] == "    # Line 3"
    assert lines[4] == "    return True"


def test_edit_file_pattern_replacement_preserves_structure(
    executor: ActionExecutor, temp_dir: str
) -> None:
    """Test that pattern replacement preserves overall file structure."""
    test_file = Path(temp_dir) / "test.py"
    original_content = "try:\n    risky_operation()\nexcept:\n    pass\nfinally:\n    cleanup()\n"
    test_file.write_text(original_content)

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except Exception:",
        },
    )

    assert success is True

    result = test_file.read_text()
    lines = result.splitlines()
    assert len(lines) == 6
    assert lines[0] == "try:"
    assert lines[1] == "    risky_operation()"
    assert lines[2] == "except Exception:"
    assert lines[3] == "    pass"
    assert lines[4] == "finally:"
    assert lines[5] == "    cleanup()"


# ============================================================================
# PATTERN MATCHING CONSISTENCY
# ============================================================================


def test_edit_file_consistent_pattern_matching(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that pattern matching works consistently regardless of approach."""
    test_file = Path(temp_dir) / "test.py"
    content = "    except ValueError:\n        pass\n"
    test_file.write_text(content)

    patterns = [
        ("except ValueError:", False),  # Substring match
        ("    except ValueError:", True),  # Exact line match
        ("except", False),  # Substring match
    ]

    for i, (pattern, match_full_line) in enumerate(patterns):
        test_file.write_text(content)

        success, message, result = executor.execute(
            "edit_file",
            {
                "path": str(test_file),
                "operation": "replace",
                "pattern": pattern,
                "content": "except OSError:",
            },
        )

        assert success is True, f"Pattern '{pattern}' failed: {message}"

        result_content = test_file.read_text()
        assert "except OSError:" in result_content


# ============================================================================
# EOL STYLE PRESERVATION
# ============================================================================


def test_eol_style_preservation(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that EOL style is preserved across operations."""
    test_file = Path(temp_dir) / "test.py"
    # Write with CRLF line endings
    test_file.write_text("line 1\r\nline 2\r\nline 3\r\n", newline="")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "line 2",
            "content": "new line 2",
        },
    )

    assert success is True

    file_content = test_file.read_text(newline="")
    assert "\r\n" in file_content
    assert file_content == "line 1\r\nnew line 2\r\nline 3\r\n"


def test_append_operation_proper_eol_handling(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that append operations handle EOLs correctly without gluing lines."""
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("def test():\n    pass")  # No trailing newline

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "append",
            "content": "\n\n# Additional code",
        },
    )

    assert success is True
    expected_content = "def test():\n    pass\n\n# Additional code\n"
    assert test_file.read_text() == expected_content


# ============================================================================
# ERROR RECOVERY
# ============================================================================


def test_edit_file_error_recovery_and_rollback(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that file edits handle operations appropriately."""
    test_file = Path(temp_dir) / "test.py"
    original_content = "Valid Python content\n"
    test_file.write_text(original_content)

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "Valid",
            "content": "Modified",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message

    final_content = test_file.read_text()
    assert "Modified Python content" in final_content
    assert len(final_content) > 0


def test_no_more_line_number_operations(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that line_number operations are no longer supported."""
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("line 1\nline 2\nline 3\n")

    # Pattern matching should be used
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "line 2",
            "content": "new line 2",
        },
    )

    assert success is True
    expected = "line 1\nnew line 2\nline 3\n"
    assert test_file.read_text() == expected
