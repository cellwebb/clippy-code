"""Tests for the create_directory tool."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig, PermissionManager
from clippy.tools.create_directory import create_directory


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


def test_create_directory_permission_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Permission errors should be reported with a friendly message."""

    def _raise_permission(
        self, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
    ) -> None:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "mkdir", _raise_permission)

    success, message, payload = create_directory("/protected/path")

    assert success is False
    assert "Permission denied" in message
    assert payload is None


def test_create_directory_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Other OS errors should surface their details."""

    def _raise_os_error(
        self, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
    ) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "mkdir", _raise_os_error)

    success, message, payload = create_directory("/full-disk/path")

    assert success is False
    assert "OS error" in message
    assert "disk full" in message
    assert payload is None


def test_create_directory_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unexpected exceptions should fall back to a generic failure message."""

    class CustomError(Exception):
        pass

    def _raise_custom_error(
        self, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
    ) -> None:
        raise CustomError("unexpected")

    monkeypatch.setattr(Path, "mkdir", _raise_custom_error)

    success, message, payload = create_directory("/unexpected/path")

    assert success is False
    assert message.startswith("Failed to create directory")
    assert "unexpected" in message
    assert payload is None
