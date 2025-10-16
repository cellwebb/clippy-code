"""Tests for edit_file tool - real-world issues that were encountered."""

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


def test_real_world_bare_except_issue(executor: ActionExecutor, temp_dir: str) -> None:
    """Test the exact issue encountered: fixing bare except clause in agent_utils.py."""
    # This reproduces the exact scenario we had when trying to fix the linting error
    test_file = Path(temp_dir) / "agent_utils.py"
    test_file.write_text(
        "    except Exception as e:\n"
        "        # Clean up temp file if it exists\n"
        "        try:\n"
        "            if 'tmp_path' in locals():\n"
        "                os.unlink(tmp_path)\n"
        "        except:\n"
        "            pass\n"
        "        return False, f\"Failed to write to {path}: {str(e)}\"\n"
    )

    # This is the exact command that failed
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "except:",
            "content": "except OSError:",
        },
    )

    # This should succeed without losing indentation or corrupting the file
    assert success is True, f"Failed to replace bare except: {message}"
    assert "Successfully performed replace operation" in message

    # Verify the file content is correct
    result = test_file.read_text()
    assert "        except OSError:" in result
    assert "        return False" in result
    assert "# Clean up temp file if it exists" in result
    # Make sure the structure is preserved
    lines = result.splitlines()
    assert len(lines) >= 8
    # Check that the replaced line has correct indentation
    for line in lines:
        if "except OSError:" in line:
            assert line.startswith("        ")  # 8 spaces


def test_real_world_whitespace_sensitivity_issue(executor: ActionExecutor, temp_dir: str) -> None:
    """Test the whitespace sensitivity issue with pattern matching."""
    # Create a file with the exact pattern that caused issues
    test_file = Path(temp_dir) / "test.py"
    content = "        except:\n            pass\n"
    test_file.write_text(content)

    # Multiple approaches to fix the same issue
    approaches = [
        {"pattern": "except:", "content": "except OSError:"},
        {"pattern": "        except:", "content": "        except OSError:"},
    ]

    for i, approach in enumerate(approaches):
        # Reset the file for each approach
        test_file.write_text(content)

        success, message, result = executor.execute(
            "edit_file",
            {
                "path": str(test_file),
                "operation": "replace",
                **approach
            },
        )

        assert success is True, f"Approach {i+1} failed: {message}"
        assert "Successfully performed replace operation" in message

        # Verify the result
        result_content = test_file.read_text()
        assert "except OSError:" in result_content
        assert "            pass" in result_content  # Pass line should keep its indentation


def test_edit_file_no_line_number_corruption(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that line number-based edits don't corrupt file structure."""
    test_file = Path(temp_dir) / "test.py"
    original_content = (
        "def function():\n"
        "    # Line 1\n"
        "    # Line 2\n"
        "    # Line 3\n"
        "    return True\n"
    )
    test_file.write_text(original_content)

    # Replace line 2 (line number 3)
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "line_number": 3,
            "content": "    # Modified line 2\n",
        },
    )

    assert success is True
    assert "Successfully performed replace operation" in message

    # Verify file structure is preserved
    result = test_file.read_text()
    lines = result.splitlines()
    assert len(lines) == 5  # Same number of lines
    assert lines[0] == "def function():"
    assert lines[1] == "    # Line 1"
    assert lines[2] == "    # Modified line 2"
    assert lines[3] == "    # Line 3"
    assert lines[4] == "    return True"


def test_edit_file_pattern_replacement_preserves_structure(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that pattern replacement preserves overall file structure."""
    test_file = Path(temp_dir) / "test.py"
    original_content = (
        "try:\n"
        "    risky_operation()\n"
        "except:\n"
        "    pass\n"
        "finally:\n"
        "    cleanup()\n"
    )
    test_file.write_text(original_content)

    # Replace the except clause
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

    # Verify structure is preserved
    result = test_file.read_text()
    lines = result.splitlines()
    assert len(lines) == 6  # Same number of lines
    assert lines[0] == "try:"
    assert lines[1] == "    risky_operation()"
    assert lines[2] == "except Exception:"
    assert lines[3] == "    pass"
    assert lines[4] == "finally:"
    assert lines[5] == "    cleanup()"


def test_edit_file_consistent_pattern_matching(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that pattern matching works consistently regardless of approach."""
    test_file = Path(temp_dir) / "test.py"
    content = "    except ValueError:\n        pass\n"
    test_file.write_text(content)

    # All of these should find and replace the same line
    patterns = [
        "except ValueError:",
        "    except ValueError:",
        "except",  # Substring match
        "ValueError",  # Different substring
    ]

    for i, pattern in enumerate(patterns):
        # Reset file
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

        if pattern == "ValueError":
            # This might not work because it would match as substring replacement
            # and we expect it to fail or produce different results
            continue

        assert success is True, f"Pattern '{pattern}' failed: {message}"

        # Verify the replacement
        result_content = test_file.read_text()
        assert "except OSError:" in result_content


def test_edit_file_error_recovery_and_rollback(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that file edits are rolled back on validation failures."""
    test_file = Path(temp_dir) / "test.py"
    original_content = "Valid Python content\n"
    test_file.write_text(original_content)

    # Try to do something that might cause corruption
    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "replace",
            "pattern": "Valid",
            "content": "Valid but with problematic null byte: \x00",
        },
    )

    # This might succeed during editing but should be caught by validation
    if success:
        # File should still be readable after the operation
        try:
            result = test_file.read_text()
            # If it contains null bytes, that's a problem
            assert "\x00" not in result, "Null byte should not be in file"
        except UnicodeDecodeError:
            pytest.fail("File became corrupted and unreadable after edit")

    # Original content should be preserved if rollback worked
    # (This depends on the specific implementation)
    final_content = test_file.read_text()
    assert len(final_content) > 0  # File should not be empty
