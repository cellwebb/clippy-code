"""Tests for the execute_command tool."""

import subprocess
import tempfile
from collections.abc import Generator
from importlib import import_module

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import ActionType, PermissionConfig, PermissionManager

EXECUTE_COMMAND_MODULE = import_module("clippy.tools.execute_command")


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


def test_execute_command(executor: ActionExecutor) -> None:
    """Test executing a shell command."""
    # Execute a simple command
    success, message, content = executor.execute(
        "execute_command", {"command": "echo 'Hello from command'", "working_dir": "."}
    )

    assert success is True
    assert "Hello from command" in content


def test_execute_command_failure(executor: ActionExecutor, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test execute_command handles non-zero return codes."""

    class FakeResult:
        def __init__(self) -> None:
            self.returncode = 5
            self.stdout = "out"
            self.stderr = "err"

    def fake_run(*_args: object, **_kwargs: object) -> FakeResult:
        return FakeResult()

    monkeypatch.setattr(EXECUTE_COMMAND_MODULE.subprocess, "run", fake_run)

    success, message, content = executor.execute(
        "execute_command", {"command": "false", "working_dir": "."}
    )

    assert success is False
    assert "return code 5" in message
    assert content == "outerr"


def test_execute_command_directory_traversal(executor: ActionExecutor) -> None:
    """Test execute_command rejects working directories with traversal attempts."""
    success, message, content = executor.execute(
        "execute_command", {"command": "echo test", "working_dir": "../outside"}
    )

    assert success is False
    assert "Directory traversal not allowed" in message
    assert content is None


def test_execute_command_timeout(executor: ActionExecutor, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test execute_command handles subprocess timeouts."""

    def raise_timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="sleep 40", timeout=30)

    monkeypatch.setattr(EXECUTE_COMMAND_MODULE.subprocess, "run", raise_timeout)

    success, message, content = executor.execute(
        "execute_command", {"command": "sleep 40", "working_dir": "."}
    )

    assert success is False
    assert "timed out" in message
    assert content is None


def test_execute_command_action_requires_approval() -> None:
    """Test that the EXECUTE_COMMAND action type requires approval."""
    config = PermissionConfig()

    # The EXECUTE_COMMAND action should require approval
    assert ActionType.EXECUTE_COMMAND in config.require_approval
    assert config.can_auto_execute(ActionType.EXECUTE_COMMAND) is False
