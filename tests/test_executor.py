"""Tests for the action executor."""

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


@pytest.fixture
def executor() -> ActionExecutor:
    """Create an executor instance."""
    manager = PermissionManager()
    return ActionExecutor(manager)


def test_execute_unknown_action(executor: ActionExecutor) -> None:
    """Test executing an unknown action."""
    success, message, content = executor.execute("unknown_action", {})

    assert success is False
    assert "Unknown tool" in message
