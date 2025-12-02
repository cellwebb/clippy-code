"""Permission system for controlling agent actions."""

import logging
from enum import Enum

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels for actions."""

    AUTO_APPROVE = "auto_approve"  # Execute without asking
    REQUIRE_APPROVAL = "require_approval"  # Ask user before executing
    DENY = "deny"  # Never allow


class ActionType(str, Enum):
    """Types of actions the agent can perform."""

    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    LIST_DIR = "list_dir"
    CREATE_DIR = "create_dir"
    EXECUTE_COMMAND = "execute_command"
    SEARCH_FILES = "search_files"
    GET_FILE_INFO = "get_file_info"
    GREP = "grep"
    EDIT_FILE = "edit_file"
    FIND_REPLACE = "find_replace"
    FETCH_WEBPAGE = "fetch_webpage"
    THINK = "think"
    DELEGATE_TO_SUBAGENT = "delegate_to_subagent"
    RUN_PARALLEL_SUBAGENTS = "run_parallel_subagents"

    # MCP Action Types
    MCP_LIST_TOOLS = "mcp_list_tools"
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_CONNECT = "mcp_connect"


class PermissionConfig(BaseModel):
    """Configuration for action permissions."""

    auto_approve: set[ActionType] = {
        ActionType.READ_FILE,
        ActionType.LIST_DIR,
        ActionType.SEARCH_FILES,
        ActionType.GET_FILE_INFO,
        ActionType.GREP,
        ActionType.THINK,  # Auto-approve thinking - it's just internal reasoning
        ActionType.MCP_LIST_TOOLS,  # Auto-approve MCP tool listing
    }
    require_approval: set[ActionType] = {
        ActionType.WRITE_FILE,
        ActionType.DELETE_FILE,
        ActionType.CREATE_DIR,
        ActionType.EXECUTE_COMMAND,
        ActionType.EDIT_FILE,
        ActionType.FETCH_WEBPAGE,  # Require approval for web requests
        ActionType.FIND_REPLACE,  # Multi-file changes require approval
        ActionType.DELEGATE_TO_SUBAGENT,  # Require approval for subagent delegation
        ActionType.RUN_PARALLEL_SUBAGENTS,  # Require approval for parallel subagent execution
        ActionType.MCP_TOOL_CALL,  # Require approval for MCP tool calls by default
        ActionType.MCP_CONNECT,  # Require approval for MCP server connections
    }
    deny: set[ActionType] = set()

    def get_permission_level(self, action_type: ActionType) -> PermissionLevel:
        """Get the permission level for an action type."""
        if action_type in self.deny:
            return PermissionLevel.DENY
        if action_type in self.auto_approve:
            return PermissionLevel.AUTO_APPROVE
        if action_type in self.require_approval:
            return PermissionLevel.REQUIRE_APPROVAL
        # Default to requiring approval for unknown actions
        return PermissionLevel.REQUIRE_APPROVAL

    def can_auto_execute(self, action_type: ActionType) -> bool:
        """Check if an action can be auto-executed."""
        return self.get_permission_level(action_type) == PermissionLevel.AUTO_APPROVE

    def is_denied(self, action_type: ActionType) -> bool:
        """Check if an action is explicitly denied."""
        return self.get_permission_level(action_type) == PermissionLevel.DENY


# Canonical mapping from tool names to ActionTypes
# This is the single source of truth - import this instead of duplicating
TOOL_ACTION_MAP: dict[str, ActionType] = {
    "read_file": ActionType.READ_FILE,
    "write_file": ActionType.WRITE_FILE,
    "delete_file": ActionType.DELETE_FILE,
    "list_directory": ActionType.LIST_DIR,
    "create_directory": ActionType.CREATE_DIR,
    "execute_command": ActionType.EXECUTE_COMMAND,
    "search_files": ActionType.SEARCH_FILES,
    "get_file_info": ActionType.GET_FILE_INFO,
    "read_files": ActionType.READ_FILE,  # Uses the same permission as read_file
    "read_lines": ActionType.READ_FILE,  # Uses the same permission as read_file
    "grep": ActionType.GREP,
    "edit_file": ActionType.EDIT_FILE,
    "fetch_webpage": ActionType.FETCH_WEBPAGE,
    "find_replace": ActionType.FIND_REPLACE,
    "think": ActionType.THINK,
    "delegate_to_subagent": ActionType.DELEGATE_TO_SUBAGENT,
    "run_parallel_subagents": ActionType.RUN_PARALLEL_SUBAGENTS,
}


class PermissionManager:
    """Manages permissions for agent actions."""

    def __init__(self, config: PermissionConfig | None = None):
        self.config = config or PermissionConfig()

    def check_permission(self, action_type: ActionType) -> PermissionLevel:
        """Check the permission level for an action."""
        level = self.config.get_permission_level(action_type)
        logger.debug(f"Permission check: {action_type} -> {level}")
        return level

    def update_permission(self, action_type: ActionType, level: PermissionLevel) -> None:
        """Update the permission level for an action type."""
        logger.info(f"Updating permission: {action_type} -> {level}")

        # Remove from all sets first
        self.config.auto_approve.discard(action_type)
        self.config.require_approval.discard(action_type)
        self.config.deny.discard(action_type)

        # Add to appropriate set
        if level == PermissionLevel.AUTO_APPROVE:
            self.config.auto_approve.add(action_type)
        elif level == PermissionLevel.REQUIRE_APPROVAL:
            self.config.require_approval.add(action_type)
        elif level == PermissionLevel.DENY:
            self.config.deny.add(action_type)
