"""Shared fixtures for tool tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


@pytest.fixture
def executor() -> ActionExecutor:
    """Create an executor instance that allows writes to temp directories."""
    manager = PermissionManager()
    temp_dir = Path(tempfile.gettempdir())
    return ActionExecutor(manager, allowed_write_roots=[temp_dir])


@pytest.fixture
def executor_direct() -> ActionExecutor:
    """Create an executor instance for direct method access."""
    config = PermissionConfig(
        auto_approve=set(),
        require_approval=set(),
        deny=set(),
    )
    manager = PermissionManager(config)
    temp_dir = Path(tempfile.gettempdir())
    return ActionExecutor(manager, allowed_write_roots=[temp_dir])


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
