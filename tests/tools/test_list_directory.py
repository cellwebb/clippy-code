"""Tests for the list_directory tool."""

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


def test_list_directory(executor: ActionExecutor, temp_dir: str) -> None:
    """Test listing a directory."""
    # Create some test files
    (Path(temp_dir) / "file1.txt").touch()
    (Path(temp_dir) / "file2.txt").touch()
    (Path(temp_dir) / "subdir").mkdir()

    # List the directory
    success, message, content = executor.execute(
        "list_directory", {"path": temp_dir, "recursive": False}
    )

    assert success is True
    assert "Successfully listed" in message
    assert "file1.txt" in content
    assert "file2.txt" in content
    assert "subdir/" in content


def test_list_directory_not_found(executor: ActionExecutor) -> None:
    """Test listing a non-existent directory."""
    success, message, content = executor.execute(
        "list_directory", {"path": "/nonexistent/directory", "recursive": False}
    )

    assert success is False
    assert "Directory not found" in message


def test_list_directory_action_is_auto_approved() -> None:
    """Test that the LIST_DIR action type is in the auto-approved set."""
    config = PermissionConfig()

    # The LIST_DIR action should be auto-approved
    assert ActionType.LIST_DIR in config.auto_approve
    assert config.can_auto_execute(ActionType.LIST_DIR) is True
