"""Integration tests for edit_file via agent handle_tool_use."""

from pathlib import Path
from typing import Any

import pytest

from clippy.agent import ClippyAgent, handle_tool_use
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


@pytest.fixture
def agent(tmp_path: Path) -> ClippyAgent:
    """Create a ClippyAgent wired with default permissions and executor."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)
    return ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
    )


def test_edit_file_integration_approved(agent: ClippyAgent, tmp_path: Path) -> None:
    """Edit a file end-to-end through handle_tool_use with approval granted."""
    # Prepare file
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Line 1\nLine 2\nLine 3\n")

    # Capture diff passed to approval callback
    captured: dict[str, Any] = {"diff": None, "called": False}

    def approval_callback(
        tool_name: str, tool_input: dict[str, Any], diff_content: str | None
    ) -> bool:
        captured["called"] = True
        captured["diff"] = diff_content
        # Approve the action
        return True

    # Execute edit_file via agent tool handler (requires approval by default)
    success = handle_tool_use(
        "edit_file",
        {
            "path": str(file_path),
            "operation": "replace",
            "pattern": "Line 2",
            "content": "Replaced line",
            "match_pattern_line": True,
        },
        tool_use_id="test-call-1",
        auto_approve_all=False,
        permission_manager=agent.permission_manager,
        executor=agent.executor,
        console=agent.console,
        conversation_history=agent.conversation_history,
        approval_callback=approval_callback,
    )

    # Assertions
    assert success is True
    assert captured["called"] is True
    assert captured["diff"] is not None
    assert "a/" in captured["diff"] and "b/" in captured["diff"]  # unified diff headers

    # File content updated
    expected = "Line 1\nReplaced line\nLine 3\n"
    assert file_path.read_text() == expected

    # Conversation history contains tool result
    assert len(agent.conversation_history) > 0
    last = agent.conversation_history[-1]
    assert last["role"] == "tool"
    assert "Successfully performed replace operation" in last["content"]


def test_edit_file_integration_rejected(agent: ClippyAgent, tmp_path: Path) -> None:
    """Verify rejecting approval prevents edits and records the outcome."""
    # Prepare file
    file_path = tmp_path / "sample.txt"
    original = "Line 1\nLine 2\nLine 3\n"
    file_path.write_text(original)

    def deny_callback(tool_name: str, tool_input: dict[str, Any], diff_content: str | None) -> bool:
        return False  # Deny

    success = handle_tool_use(
        "edit_file",
        {
            "path": str(file_path),
            "operation": "replace",
            "pattern": "Line 2",
            "content": "Replaced line",
            "match_pattern_line": True,
        },
        tool_use_id="test-call-2",
        auto_approve_all=False,
        permission_manager=agent.permission_manager,
        executor=agent.executor,
        console=agent.console,
        conversation_history=agent.conversation_history,
        approval_callback=deny_callback,
    )

    # Assertions
    assert success is False
    assert file_path.read_text() == original  # No change

    last = agent.conversation_history[-1]
    assert last["role"] == "tool"
    assert "ERROR: Action rejected by user" in last["content"]
