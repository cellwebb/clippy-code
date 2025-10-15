"""Tests for the read_file tool."""

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


def test_read_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test reading a file."""
    # Create a test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    # Read the file
    success, message, content = executor.execute("read_file", {"path": str(test_file)})

    assert success is True
    assert "Successfully read" in message
    assert content == "Hello, World!"


def test_read_file_not_found(executor: ActionExecutor) -> None:
    """Test reading a non-existent file."""
    success, message, content = executor.execute("read_file", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "File not found" in message


def test_read_file_action_is_auto_approved() -> None:
    """Test that the READ_FILE action type is in the auto-approved set."""
    config = PermissionConfig()

    # The READ_FILE action should be auto-approved
    assert ActionType.READ_FILE in config.auto_approve
    assert config.can_auto_execute(ActionType.READ_FILE) is True
