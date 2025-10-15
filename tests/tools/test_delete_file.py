"""Tests for the delete_file tool."""

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


def test_delete_file(executor: ActionExecutor, temp_dir: str) -> None:
    """Test deleting a file."""
    # Create a test file
    test_file = Path(temp_dir) / "to_delete.txt"
    test_file.write_text("Delete me")

    # Delete the file
    success, message, content = executor.execute("delete_file", {"path": str(test_file)})

    assert success is True
    assert "Successfully deleted" in message
    assert not test_file.exists()


def test_delete_file_not_found(executor: ActionExecutor) -> None:
    """Test deleting a non-existent file."""
    success, message, content = executor.execute("delete_file", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "File not found" in message


def test_delete_file_action_requires_approval() -> None:
    """Test that the DELETE_FILE action type requires approval."""
    config = PermissionConfig()

    # The DELETE_FILE action should require approval
    assert ActionType.DELETE_FILE in config.require_approval
    assert config.can_auto_execute(ActionType.DELETE_FILE) is False
