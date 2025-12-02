"""Global pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


@pytest.fixture
def permission_manager() -> PermissionManager:
    """Create a permission manager with default config."""
    return PermissionManager(PermissionConfig())


@pytest.fixture
def executor(permission_manager: PermissionManager) -> ActionExecutor:
    """Create an executor that allows writes to temp directories.

    This is needed because pytest's tmp_path fixture creates directories
    outside of CWD, which would be blocked by path validation.
    """
    # Get the system temp directory to allow test files
    temp_dir = Path(tempfile.gettempdir())
    return ActionExecutor(
        permission_manager=permission_manager,
        allowed_write_roots=[temp_dir],
    )
