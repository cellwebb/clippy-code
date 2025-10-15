"""Tests for the get_file_info tool."""

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


def test_get_file_info(executor: ActionExecutor, temp_dir: str) -> None:
    """Test getting file info."""
    # Create a test file
    test_file = Path(temp_dir) / "info_test.txt"
    test_file.write_text("Content")

    # Get file info
    success, message, content = executor.execute("get_file_info", {"path": str(test_file)})

    assert success is True
    assert "is_file: True" in content
    assert "size:" in content


def test_get_file_info_not_found(executor: ActionExecutor) -> None:
    """Test getting info for a non-existent file."""
    success, message, content = executor.execute("get_file_info", {"path": "/nonexistent/file.txt"})

    assert success is False
    assert "File not found" in message


def test_get_file_info_action_is_auto_approved() -> None:
    """Test that the GET_FILE_INFO action type is in the auto-approved set."""
    config = PermissionConfig()

    # The GET_FILE_INFO action should be auto-approved
    assert ActionType.GET_FILE_INFO in config.auto_approve
    assert config.can_auto_execute(ActionType.GET_FILE_INFO) is True
