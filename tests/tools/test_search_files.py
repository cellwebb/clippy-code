"""Tests for the search_files tool."""

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


def test_search_files(executor: ActionExecutor, temp_dir: str) -> None:
    """Test searching for files with a pattern."""
    # Create some test files
    (Path(temp_dir) / "test1.py").touch()
    (Path(temp_dir) / "test2.py").touch()
    (Path(temp_dir) / "test.txt").touch()
    (Path(temp_dir) / "subdir").mkdir()
    (Path(temp_dir) / "subdir" / "test3.py").touch()

    # Search for Python files (using ** pattern for recursive search)
    success, message, content = executor.execute(
        "search_files", {"pattern": "**/*.py", "path": temp_dir}
    )

    assert success is True
    assert "Found 3 matches" in message

    # Split content into lines for checking
    lines = content.split("\n") if content else []

    # Should include full paths to the Python files
    full_paths = [
        str(Path(temp_dir) / "test1.py"),
        str(Path(temp_dir) / "test2.py"),
        str(Path(temp_dir) / "subdir" / "test3.py"),
    ]

    for path in full_paths:
        assert path in lines


def test_search_files_non_recursive(executor: ActionExecutor, temp_dir: str) -> None:
    """Test searching for files non-recursively."""
    # Create some test files
    (Path(temp_dir) / "test1.py").touch()
    (Path(temp_dir) / "test2.py").touch()
    (Path(temp_dir) / "test.txt").touch()
    (Path(temp_dir) / "subdir").mkdir()
    (Path(temp_dir) / "subdir" / "test3.py").touch()

    # Search for Python files non-recursively (without ** pattern)
    success, message, content = executor.execute(
        "search_files", {"pattern": "*.py", "path": temp_dir}
    )

    assert success is True
    assert "Found 2 matches" in message

    # Split content into lines for checking
    lines = content.split("\n") if content else []

    # Should include full paths to the Python files in the top directory only
    top_level_paths = [str(Path(temp_dir) / "test1.py"), str(Path(temp_dir) / "test2.py")]
    nested_path = str(Path(temp_dir) / "subdir" / "test3.py")

    for path in top_level_paths:
        assert path in lines

    # Should NOT include the nested file
    assert nested_path not in lines


def test_search_files_not_found(executor: ActionExecutor, temp_dir: str) -> None:
    """Test searching for files with a pattern that matches nothing."""
    # Create a test file
    (Path(temp_dir) / "test.txt").touch()

    # Search for files that don't exist
    success, message, content = executor.execute(
        "search_files", {"pattern": "*.py", "path": temp_dir}
    )

    assert success is True
    assert "No matches found" in message
    assert content == ""


def test_search_files_action_is_auto_approved() -> None:
    """Test that the SEARCH_FILES action type is in the auto-approved set."""
    config = PermissionConfig()

    # The SEARCH_FILES action should be auto-approved
    assert ActionType.SEARCH_FILES in config.auto_approve
    assert config.can_auto_execute(ActionType.SEARCH_FILES) is True
