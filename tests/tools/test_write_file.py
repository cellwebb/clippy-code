"""Tests for the write_file tool."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig, PermissionManager


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
