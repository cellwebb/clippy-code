"""Tests for the grep tool."""

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


def test_grep(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep functionality."""
    # Create test files
    test_file = Path(temp_dir) / "grep_test.txt"
    test_file.write_text("Hello World\nThis is a test\nAnother line")

    # Search for pattern in file
    success, message, content = executor.execute(
        "grep", {"pattern": "test", "paths": [str(test_file)], "flags": "-i"}
    )

    # grep returns 0 when matches are found
    assert success is True
    assert "search executed successfully" in message or "search completed" in message
    assert "This is a test" in content


def test_grep_no_matches(executor: ActionExecutor, temp_dir: str) -> None:
    """Test grep with no matches."""
    # Create test file
    test_file = Path(temp_dir) / "grep_test.txt"
    test_file.write_text("Hello World\nThis is a test\nAnother line")

    # Search for pattern that doesn't exist
    success, message, content = executor.execute(
        "grep", {"pattern": "nonexistent", "paths": [str(test_file)], "flags": ""}
    )

    # grep returns 1 when no matches found, which we treat as success
    assert success is True
    assert "no matches found" in message


def test_grep_action_is_auto_approved() -> None:
    """Test that the GREP action type is in the auto-approved set."""
    config = PermissionConfig()

    # The GREP action should be auto-approved
    assert ActionType.GREP in config.auto_approve
    assert config.can_auto_execute(ActionType.GREP) is True
