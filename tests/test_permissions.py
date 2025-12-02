"""Tests for the permission system."""

from clippy.permissions import (
    TOOL_ACTION_MAP,
    ActionType,
    PermissionConfig,
    PermissionLevel,
    PermissionManager,
)


class TestPermissionConfig:
    """Tests for PermissionConfig class."""

    def test_default_auto_approve_actions(self) -> None:
        """Test default auto-approved actions."""
        config = PermissionConfig()

        expected_auto_approve = {
            ActionType.READ_FILE,
            ActionType.LIST_DIR,
            ActionType.SEARCH_FILES,
            ActionType.GET_FILE_INFO,
            ActionType.GREP,
            ActionType.THINK,
            ActionType.MCP_LIST_TOOLS,
        }

        for action in expected_auto_approve:
            assert action in config.auto_approve, f"{action} should be auto-approved"

    def test_default_require_approval_actions(self) -> None:
        """Test default require-approval actions."""
        config = PermissionConfig()

        expected_require_approval = {
            ActionType.WRITE_FILE,
            ActionType.DELETE_FILE,
            ActionType.CREATE_DIR,
            ActionType.EXECUTE_COMMAND,
            ActionType.EDIT_FILE,
            ActionType.FETCH_WEBPAGE,
            ActionType.FIND_REPLACE,
            ActionType.DELEGATE_TO_SUBAGENT,
            ActionType.RUN_PARALLEL_SUBAGENTS,
            ActionType.MCP_TOOL_CALL,
            ActionType.MCP_CONNECT,
        }

        for action in expected_require_approval:
            assert action in config.require_approval, f"{action} should require approval"

    def test_default_deny_set_is_empty(self) -> None:
        """Test that deny set is empty by default."""
        config = PermissionConfig()
        assert len(config.deny) == 0

    def test_no_action_in_multiple_sets(self) -> None:
        """Test that no action appears in multiple permission sets."""
        config = PermissionConfig()

        for action in ActionType:
            in_sets = []
            if action in config.auto_approve:
                in_sets.append("auto_approve")
            if action in config.require_approval:
                in_sets.append("require_approval")
            if action in config.deny:
                in_sets.append("deny")

            assert len(in_sets) <= 1, f"{action} appears in multiple sets: {in_sets}"

    def test_get_permission_level_auto_approve(self) -> None:
        """Test get_permission_level returns AUTO_APPROVE for auto-approved actions."""
        config = PermissionConfig()
        assert config.get_permission_level(ActionType.READ_FILE) == PermissionLevel.AUTO_APPROVE

    def test_get_permission_level_require_approval(self) -> None:
        """Test get_permission_level returns REQUIRE_APPROVAL."""
        config = PermissionConfig()
        assert (
            config.get_permission_level(ActionType.WRITE_FILE) == PermissionLevel.REQUIRE_APPROVAL
        )

    def test_get_permission_level_deny(self) -> None:
        """Test get_permission_level returns DENY for denied actions."""
        config = PermissionConfig()
        config.deny.add(ActionType.DELETE_FILE)
        assert config.get_permission_level(ActionType.DELETE_FILE) == PermissionLevel.DENY

    def test_deny_takes_precedence_over_auto_approve(self) -> None:
        """Test that deny takes precedence over auto_approve."""
        config = PermissionConfig()
        # READ_FILE is auto-approved by default
        assert config.get_permission_level(ActionType.READ_FILE) == PermissionLevel.AUTO_APPROVE

        # Add to deny set
        config.deny.add(ActionType.READ_FILE)
        assert config.get_permission_level(ActionType.READ_FILE) == PermissionLevel.DENY

    def test_deny_takes_precedence_over_require_approval(self) -> None:
        """Test that deny takes precedence over require_approval."""
        config = PermissionConfig()
        config.deny.add(ActionType.WRITE_FILE)
        assert config.get_permission_level(ActionType.WRITE_FILE) == PermissionLevel.DENY

    def test_can_auto_execute_true(self) -> None:
        """Test can_auto_execute returns True for auto-approved actions."""
        config = PermissionConfig()
        assert config.can_auto_execute(ActionType.READ_FILE) is True
        assert config.can_auto_execute(ActionType.GREP) is True
        assert config.can_auto_execute(ActionType.THINK) is True

    def test_can_auto_execute_false_for_require_approval(self) -> None:
        """Test can_auto_execute returns False for require-approval actions."""
        config = PermissionConfig()
        assert config.can_auto_execute(ActionType.WRITE_FILE) is False
        assert config.can_auto_execute(ActionType.EXECUTE_COMMAND) is False

    def test_can_auto_execute_false_for_denied(self) -> None:
        """Test can_auto_execute returns False for denied actions."""
        config = PermissionConfig()
        config.deny.add(ActionType.READ_FILE)
        assert config.can_auto_execute(ActionType.READ_FILE) is False

    def test_is_denied_true(self) -> None:
        """Test is_denied returns True for denied actions."""
        config = PermissionConfig()
        config.deny.add(ActionType.DELETE_FILE)
        assert config.is_denied(ActionType.DELETE_FILE) is True

    def test_is_denied_false(self) -> None:
        """Test is_denied returns False for non-denied actions."""
        config = PermissionConfig()
        assert config.is_denied(ActionType.READ_FILE) is False
        assert config.is_denied(ActionType.WRITE_FILE) is False


class TestPermissionManager:
    """Tests for PermissionManager class."""

    def test_init_with_default_config(self) -> None:
        """Test manager initializes with default config."""
        manager = PermissionManager()
        assert manager.config is not None
        assert isinstance(manager.config, PermissionConfig)

    def test_init_with_custom_config(self) -> None:
        """Test manager initializes with custom config."""
        config = PermissionConfig()
        config.auto_approve.add(ActionType.WRITE_FILE)
        manager = PermissionManager(config)

        assert ActionType.WRITE_FILE in manager.config.auto_approve

    def test_check_permission_auto_approve(self) -> None:
        """Test check_permission for auto-approved actions."""
        manager = PermissionManager()
        level = manager.check_permission(ActionType.READ_FILE)
        assert level == PermissionLevel.AUTO_APPROVE

    def test_check_permission_require_approval(self) -> None:
        """Test check_permission for require-approval actions."""
        manager = PermissionManager()
        level = manager.check_permission(ActionType.WRITE_FILE)
        assert level == PermissionLevel.REQUIRE_APPROVAL

    def test_check_permission_deny(self) -> None:
        """Test check_permission for denied actions."""
        config = PermissionConfig()
        config.deny.add(ActionType.DELETE_FILE)
        manager = PermissionManager(config)

        level = manager.check_permission(ActionType.DELETE_FILE)
        assert level == PermissionLevel.DENY

    def test_update_permission_to_auto_approve(self) -> None:
        """Test updating permission to AUTO_APPROVE."""
        manager = PermissionManager()

        # WRITE_FILE initially requires approval
        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.REQUIRE_APPROVAL

        # Update to auto-approve
        manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.AUTO_APPROVE)

        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.AUTO_APPROVE
        assert ActionType.WRITE_FILE in manager.config.auto_approve
        assert ActionType.WRITE_FILE not in manager.config.require_approval
        assert ActionType.WRITE_FILE not in manager.config.deny

    def test_update_permission_to_require_approval(self) -> None:
        """Test updating permission to REQUIRE_APPROVAL."""
        manager = PermissionManager()

        # READ_FILE is initially auto-approved
        assert manager.check_permission(ActionType.READ_FILE) == PermissionLevel.AUTO_APPROVE

        # Update to require approval
        manager.update_permission(ActionType.READ_FILE, PermissionLevel.REQUIRE_APPROVAL)

        assert manager.check_permission(ActionType.READ_FILE) == PermissionLevel.REQUIRE_APPROVAL
        assert ActionType.READ_FILE in manager.config.require_approval
        assert ActionType.READ_FILE not in manager.config.auto_approve
        assert ActionType.READ_FILE not in manager.config.deny

    def test_update_permission_to_deny(self) -> None:
        """Test updating permission to DENY."""
        manager = PermissionManager()

        manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.DENY)

        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.DENY
        assert manager.config.is_denied(ActionType.WRITE_FILE)
        assert ActionType.WRITE_FILE in manager.config.deny
        assert ActionType.WRITE_FILE not in manager.config.auto_approve
        assert ActionType.WRITE_FILE not in manager.config.require_approval

    def test_multiple_permission_updates(self) -> None:
        """Test multiple permission updates on same action."""
        manager = PermissionManager()

        # Start with require approval
        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.REQUIRE_APPROVAL

        # Update to auto-approve
        manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.AUTO_APPROVE)
        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.AUTO_APPROVE

        # Update to deny
        manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.DENY)
        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.DENY

        # Back to require approval
        manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.REQUIRE_APPROVAL)
        assert manager.check_permission(ActionType.WRITE_FILE) == PermissionLevel.REQUIRE_APPROVAL

    def test_update_removes_from_all_sets(self) -> None:
        """Test that update_permission removes action from all sets before adding."""
        manager = PermissionManager()

        # Force action into multiple sets (shouldn't happen in practice)
        manager.config.auto_approve.add(ActionType.WRITE_FILE)
        manager.config.require_approval.add(ActionType.WRITE_FILE)

        # Update should clean up
        manager.update_permission(ActionType.WRITE_FILE, PermissionLevel.DENY)

        assert ActionType.WRITE_FILE in manager.config.deny
        assert ActionType.WRITE_FILE not in manager.config.auto_approve
        assert ActionType.WRITE_FILE not in manager.config.require_approval


class TestToolActionMap:
    """Tests for TOOL_ACTION_MAP."""

    def test_tool_action_map_contains_all_tools(self) -> None:
        """Test that TOOL_ACTION_MAP contains mappings for all expected tools."""
        expected_tools = {
            "read_file",
            "write_file",
            "delete_file",
            "list_directory",
            "create_directory",
            "execute_command",
            "search_files",
            "get_file_info",
            "read_files",
            "read_lines",
            "grep",
            "edit_file",
            "fetch_webpage",
            "find_replace",
            "think",
            "delegate_to_subagent",
            "run_parallel_subagents",
        }

        for tool in expected_tools:
            assert tool in TOOL_ACTION_MAP, f"Tool '{tool}' missing from TOOL_ACTION_MAP"

    def test_tool_action_map_values_are_action_types(self) -> None:
        """Test that all values in TOOL_ACTION_MAP are ActionType enum members."""
        for tool, action_type in TOOL_ACTION_MAP.items():
            assert isinstance(action_type, ActionType), (
                f"Tool '{tool}' maps to {action_type} which is not an ActionType"
            )

    def test_read_tools_map_to_read_file_action(self) -> None:
        """Test that read-related tools map to READ_FILE action."""
        assert TOOL_ACTION_MAP["read_file"] == ActionType.READ_FILE
        assert TOOL_ACTION_MAP["read_files"] == ActionType.READ_FILE
        assert TOOL_ACTION_MAP["read_lines"] == ActionType.READ_FILE

    def test_tool_action_map_consistency(self) -> None:
        """Test that TOOL_ACTION_MAP mappings are consistent with permission defaults."""
        config = PermissionConfig()

        # All tools should map to ActionTypes that have a permission level
        for tool, action_type in TOOL_ACTION_MAP.items():
            level = config.get_permission_level(action_type)
            assert level in [
                PermissionLevel.AUTO_APPROVE,
                PermissionLevel.REQUIRE_APPROVAL,
                PermissionLevel.DENY,
            ], f"Tool '{tool}' maps to {action_type} with unexpected level {level}"


class TestActionTypeEnumCompleteness:
    """Tests for ActionType enum completeness."""

    def test_all_action_types_have_permission_level(self) -> None:
        """Test that all ActionTypes are handled by PermissionConfig."""
        config = PermissionConfig()

        for action in ActionType:
            # Should not raise, should return a valid level
            level = config.get_permission_level(action)
            assert level in [
                PermissionLevel.AUTO_APPROVE,
                PermissionLevel.REQUIRE_APPROVAL,
                PermissionLevel.DENY,
            ], f"{action} returned invalid permission level: {level}"

    def test_action_types_are_strings(self) -> None:
        """Test that ActionType values are strings (for serialization)."""
        for action in ActionType:
            assert isinstance(action.value, str)


class TestPermissionLevelEnum:
    """Tests for PermissionLevel enum."""

    def test_permission_level_values(self) -> None:
        """Test PermissionLevel enum has expected values."""
        assert PermissionLevel.AUTO_APPROVE.value == "auto_approve"
        assert PermissionLevel.REQUIRE_APPROVAL.value == "require_approval"
        assert PermissionLevel.DENY.value == "deny"

    def test_permission_levels_are_strings(self) -> None:
        """Test that PermissionLevel values are strings."""
        for level in PermissionLevel:
            assert isinstance(level.value, str)
