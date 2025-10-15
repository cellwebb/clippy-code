"""Tests for the execute_command tool."""

import tempfile
from collections.abc import Generator

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


def test_execute_command(executor: ActionExecutor) -> None:
    """Test executing a shell command."""
    # Execute a simple command
    success, message, content = executor.execute(
        "execute_command", {"command": "echo 'Hello from command'", "working_dir": "."}
    )

    assert success is True
    assert "Hello from command" in content


def test_execute_command_action_requires_approval() -> None:
    """Test that the EXECUTE_COMMAND action type requires approval."""
    config = PermissionConfig()

    # The EXECUTE_COMMAND action should require approval
    assert ActionType.EXECUTE_COMMAND in config.require_approval
    assert config.can_auto_execute(ActionType.EXECUTE_COMMAND) is False
