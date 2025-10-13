"""Tests for the permission system."""

from clippy.permissions import (
    ActionType,
    PermissionConfig,
    PermissionLevel,
    PermissionManager,
)


def test_default_permissions() -> None:
    """Test default permission configuration."""
    config = PermissionConfig()

    # Auto-approved actions
    assert ActionType.READ_FILE in config.auto_approve
    assert ActionType.LIST_DIR in config.auto_approve
    assert ActionType.SEARCH_FILES in config.auto_approve
    assert ActionType.GET_FILE_INFO in config.auto_approve

    # Require approval actions
    assert ActionType.WRITE_FILE in config.require_approval
    assert ActionType.DELETE_FILE in config.require_approval
    assert ActionType.CREATE_DIR in config.require_approval
    assert ActionType.EXECUTE_COMMAND in config.require_approval


def test_permission_manager_check() -> None:
    """Test permission manager checks."""
    manager = PermissionManager()

    # Check auto-approved action
    level = manager.check_permission(ActionType.READ_FILE)
    assert level == PermissionLevel.AUTO_APPROVE

    # Check require-approval action
    level = manager.check_permission(ActionType.WRITE_FILE)
    assert level == PermissionLevel.REQUIRE_APPROVAL


def test_permission_update() -> None:
    """Test updating permissions."""
    manager = PermissionManager()

    # Initially requires approval
    assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.REQUIRE_APPROVAL

    # Update to auto-approve
    manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.AUTO_APPROVE)
    assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.AUTO_APPROVE

    # Update to deny
    manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.DENY)
    assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.DENY
    assert manager.config.is_denied(ActionType.WRITE_FILE)


def test_can_auto_execute() -> None:
    """Test can_auto_execute check."""
    config = PermissionConfig()

    assert config.can_auto_execute(ActionType.READ_FILE) is True
    assert config.can_auto_execute(ActionType.WRITE_FILE) is False


def test_is_denied() -> None:
    """Test is_denied check."""
    config = PermissionConfig()
    config.deny.add(ActionType.DELETE_FILE)

    assert config.is_denied(ActionType.DELETE_FILE) is True
    assert config.is_denied(ActionType.READ_FILE) is False
