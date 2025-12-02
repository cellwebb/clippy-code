"""Tests for the write_file tool."""

from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig

# Note: executor and temp_dir fixtures are provided by tests/tools/conftest.py


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
    # Try to write to a protected path outside CWD
    test_file = "/root/protected_file.txt"

    # This should fail due to path validation (outside CWD)
    success, message, content = executor.execute(
        "write_file", {"path": test_file, "content": "Test content"}
    )

    # Should fail with path validation or permission error
    assert success is False
    assert (
        "restricted to current directory" in message
        or "Error executing write_file" in message
        or "Permission denied" in message
        or "OS error" in message
        or "Failed to write" in message
        or "Read-only file system" in message
    )


def test_write_file_action_requires_approval() -> None:
    """Test that the WRITE_FILE action type requires approval."""
    config = PermissionConfig()

    # The WRITE_FILE action should require approval
    assert ActionType.WRITE_FILE in config.require_approval
    assert config.can_auto_execute(ActionType.WRITE_FILE) is False


def test_write_file_creates_parent_directories(executor: ActionExecutor, temp_dir: str) -> None:
    """Ensure the tool creates missing parent directories."""
    nested_file = Path(temp_dir) / "nested" / "dir" / "output.txt"

    success, message, _ = executor.execute(
        "write_file", {"path": str(nested_file), "content": "hello"}
    )

    assert success is True
    assert nested_file.exists()
    assert nested_file.read_text() == "hello"
    assert "Successfully wrote" in message


def test_write_file_python_syntax_error(executor: ActionExecutor, temp_dir: str) -> None:
    """Python syntax errors should be surfaced instead of writing invalid code."""
    bad_file = Path(temp_dir) / "broken.py"

    success, message, _ = executor.execute(
        "write_file", {"path": str(bad_file), "content": "def broken("}
    )

    assert success is False
    assert any(phrase in message for phrase in ["Syntax error", "File validation failed"])
    assert bad_file.exists() is False


def test_write_file_handles_os_error(
    executor: ActionExecutor, temp_dir: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unexpected OS errors should be reported to the caller."""
    target = Path(temp_dir) / "fail.txt"

    def _boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", _boom)

    success, message, _ = executor.execute("write_file", {"path": str(target), "content": "data"})

    assert success is False
    assert "File system error" in message
    assert target.exists() is False
