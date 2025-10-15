"""Tests for the create_directory tool."""

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


def test_create_directory(executor: ActionExecutor, temp_dir: str) -> None:
    """Test creating a directory."""
    new_dir = Path(temp_dir) / "new_directory"

    # Create the directory
    success, message, content = executor.execute("create_directory", {"path": str(new_dir)})

    assert success is True
    assert "Successfully created" in message
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_create_directory_action_requires_approval() -> None:
    """Test that the CREATE_DIR action type requires approval."""
    config = PermissionConfig()

    # The CREATE_DIR action should require approval
    assert ActionType.CREATE_DIR in config.require_approval
    assert config.can_auto_execute(ActionType.CREATE_DIR) is False
