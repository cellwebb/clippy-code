"""Tests for the get_file_info tool."""

import tempfile
from collections.abc import Generator
from importlib import import_module
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig, PermissionManager

GET_FILE_INFO_MODULE = import_module("clippy.tools.get_file_info")


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


def test_get_file_info_permission_error(
    executor: ActionExecutor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test get_file_info handles PermissionError from os.stat."""

    def raise_permission_error(_path: str) -> None:
        raise PermissionError("denied")

    monkeypatch.setattr(GET_FILE_INFO_MODULE.os, "stat", raise_permission_error)

    success, message, content = executor.execute("get_file_info", {"path": "restricted.txt"})

    assert success is False
    assert "Permission denied" in message
    assert content is None


def test_get_file_info_unexpected_error(
    executor: ActionExecutor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test get_file_info handles unexpected exceptions."""

    def raise_runtime_error(_path: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(GET_FILE_INFO_MODULE.os, "stat", raise_runtime_error)

    success, message, content = executor.execute("get_file_info", {"path": "broken.txt"})

    assert success is False
    assert "Failed to get file info" in message
    assert content is None


def test_get_file_info_action_is_auto_approved() -> None:
    """Test that the GET_FILE_INFO action type is in the auto-approved set."""
    config = PermissionConfig()

    # The GET_FILE_INFO action should be auto-approved
    assert ActionType.GET_FILE_INFO in config.auto_approve
    assert config.can_auto_execute(ActionType.GET_FILE_INFO) is True
