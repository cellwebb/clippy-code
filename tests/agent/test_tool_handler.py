"""Focused tests for clippy.agent.tool_handler utilities."""

from __future__ import annotations

from typing import Any

import pytest

from clippy.agent.core import InterruptedExceptionError
from clippy.agent.tool_handler import (
    ask_approval,
    display_tool_request,
    handle_tool_use,
)
from clippy.permissions import ActionType, PermissionConfig, PermissionLevel, PermissionManager


class DummyConsole:
    """Lightweight console replacement capturing printed messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, message: Any) -> None:
        if hasattr(message, "renderable"):
            self.messages.append(str(message.renderable))
        else:
            self.messages.append(str(message))


class RecordingExecutor:
    """Executor stub that records input and returns configurable results."""

    def __init__(self, *, success: bool = True, message: str = "ok", result: Any = None) -> None:
        self.success = success
        self.message = message
        self.result = result
        self.calls: list[tuple[str, dict[str, Any], bool]] = []

    def execute(self, tool_name: str, tool_input: dict[str, Any], bypass_trust: bool):
        self.calls.append((tool_name, tool_input, bypass_trust))
        return self.success, self.message, self.result


@pytest.fixture(autouse=True)
def _suppress_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid diff generation noise in tests unless explicitly overridden."""
    monkeypatch.setattr("clippy.agent.tool_handler.generate_preview_diff", lambda *_: None)


@pytest.fixture
def console() -> DummyConsole:
    return DummyConsole()


def test_handle_tool_use_auto_approved_success(console: DummyConsole) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor(message="Read file", result="file contents")

    success = handle_tool_use(
        tool_name="read_file",
        tool_input={"path": "readme.md"},
        tool_use_id="tool-1",
        auto_approve_all=False,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
    )

    assert success is True
    assert executor.calls == [("read_file", {"path": "readme.md"}, False)]
    assert len(history) == 1
    assert history[0]["tool_call_id"] == "tool-1"
    assert "Read file" in history[0]["content"]
    assert "file contents" in history[0]["content"]


def test_handle_tool_use_requires_approval_rejected(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    def fake_approval(*_args: Any, **_kwargs: Any) -> bool:
        return False

    monkeypatch.setattr("clippy.agent.tool_handler.ask_approval", fake_approval)

    success = handle_tool_use(
        tool_name="write_file",
        tool_input={"path": "file.txt", "content": "hello"},
        tool_use_id="tool-2",
        auto_approve_all=False,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
    )

    assert success is False
    assert executor.calls == []  # Should not execute when approval fails
    assert len(history) == 1
    assert history[0]["content"] == "ERROR: Action rejected by user"
    assert any("Action rejected" in message for message in console.messages)


def test_handle_tool_use_allow_updates_permission(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    def approve_and_allow(
        tool_name: str,
        tool_input: dict[str, Any],
        diff: str | None,
        action_type: ActionType | None,
        perm_manager: PermissionManager,
        _console: DummyConsole,
        approval_callback=None,
        mcp_manager=None,
    ) -> bool:
        # Simulate choosing "allow"
        perm_manager.update_permission(action_type, PermissionLevel.AUTO_APPROVE)
        return True

    monkeypatch.setattr("clippy.agent.tool_handler.ask_approval", approve_and_allow)

    success = handle_tool_use(
        tool_name="write_file",
        tool_input={"path": "notes.py", "content": "print('hi')"},
        tool_use_id="tool-3",
        auto_approve_all=False,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
    )

    assert success is True
    assert executor.calls  # tool executed
    assert ActionType.WRITE_FILE in permission_manager.config.auto_approve


def test_handle_tool_use_denied_by_policy(console: DummyConsole) -> None:
    config = PermissionConfig()
    config.deny.add(ActionType.WRITE_FILE)
    permission_manager = PermissionManager(config)
    history: list[dict[str, Any]] = []
    executor = RecordingExecutor()

    success = handle_tool_use(
        tool_name="write_file",
        tool_input={"path": "blocked.txt", "content": "nope"},
        tool_use_id="tool-4",
        auto_approve_all=False,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
    )

    assert success is False
    assert executor.calls == []
    assert any("denied by policy" in msg for msg in console.messages)
    assert history[0]["content"] == "ERROR: Action denied by policy"


def test_handle_tool_use_trusted_mcp_bypasses_approval(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    class StubMCPManager:
        def is_trusted(self, server_id: str) -> bool:
            assert server_id == "server"
            return True

    # Ensure ask_approval would cause failure if invoked
    monkeypatch.setattr(
        "clippy.agent.tool_handler.ask_approval",
        lambda *args, **kwargs: pytest.fail("ask_approval should not be called"),
    )

    success = handle_tool_use(
        tool_name="mcp__server__tool",
        tool_input={"arg": 1},
        tool_use_id="tool-5",
        auto_approve_all=False,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        mcp_manager=StubMCPManager(),
    )

    assert success is True
    assert executor.calls == [("mcp__server__tool", {"arg": 1}, False)]
    assert history[0]["content"].startswith("ok")


def test_handle_tool_use_mcp_failure_messages(console: DummyConsole) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor(success=False, message="Server not connected")

    class StubMCP:
        def is_trusted(self, server_id: str) -> bool:
            return False

    success = handle_tool_use(
        tool_name="mcp__alpha__tool",
        tool_input={"arg": 1},
        tool_use_id="tool-mcp-fail",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        mcp_manager=StubMCP(),
    )

    assert success is False
    assert any("Not connected" in msg or "not connected" in msg for msg in console.messages)

    console.messages.clear()
    executor = RecordingExecutor(success=False, message="Timeout occurred")
    history.clear()
    success = handle_tool_use(
        tool_name="mcp__alpha__tool",
        tool_input={"arg": 1},
        tool_use_id="tool-mcp-timeout",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        mcp_manager=StubMCP(),
    )

    assert success is False
    assert any("Suggestion" in msg for msg in console.messages)

    console.messages.clear()
    executor = RecordingExecutor(success=False, message="MCP server not configured")
    success = handle_tool_use(
        tool_name="mcp__alpha__tool",
        tool_input={"arg": 1},
        tool_use_id="tool-mcp-config",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        mcp_manager=StubMCP(),
    )

    assert success is False
    assert any("not configured" in msg.lower() for msg in console.messages)

    console.messages.clear()
    executor = RecordingExecutor(success=False, message="Permission denied")
    success = handle_tool_use(
        tool_name="mcp__alpha__tool",
        tool_input={"arg": 1},
        tool_use_id="tool-mcp-permission",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        mcp_manager=StubMCP(),
    )

    assert success is False
    assert any("permissions" in msg.lower() for msg in console.messages)


def test_handle_tool_use_delegate_to_subagent(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    # Create a mock parent agent with save_conversation method
    class MockParentAgent:
        def save_conversation(self):
            return (True, "Conversation saved")

    parent_agent = MockParentAgent()

    called = {}

    def fake_delegate(parent_agent: Any, permission_manager: PermissionManager, **payload: Any):
        called["payload"] = payload
        if payload.get("should_fail"):
            return False, "failure", None
        return True, "delegated", {"summary": "done"}

    monkeypatch.setattr(
        "clippy.tools.delegate_to_subagent.create_subagent_and_execute",
        fake_delegate,
    )

    # Successful delegation
    success = handle_tool_use(
        tool_name="delegate_to_subagent",
        tool_input={"task": "analyze", "should_fail": False},
        tool_use_id="tool-delegate",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        parent_agent=parent_agent,
    )

    assert success is True
    assert called["payload"]["task"] == "analyze"
    assert history[-1]["content"].startswith("delegated")

    # Failure when parent agent missing
    success = handle_tool_use(
        tool_name="delegate_to_subagent",
        tool_input={"task": "analyze"},
        tool_use_id="tool-delegate-fail",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        parent_agent=None,
    )

    assert success is False
    assert "ERROR" in history[-1]["content"]


def test_handle_tool_use_run_parallel_subagents(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    # Create a mock parent agent with save_conversation method
    class MockParentAgent:
        def save_conversation(self):
            return (True, "Conversation saved")

    parent_agent = MockParentAgent()

    def fake_run(parent_agent: Any, permission_manager: PermissionManager, **payload: Any):
        return True, "parallel ok", {"count": 2}

    monkeypatch.setattr(
        "clippy.tools.run_parallel_subagents.create_parallel_subagents_and_execute",
        fake_run,
    )

    success = handle_tool_use(
        tool_name="run_parallel_subagents",
        tool_input={"tasks": []},
        tool_use_id="tool-run-parallel",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        parent_agent=parent_agent,
    )

    assert success is True
    assert history[-1]["content"].startswith("parallel ok")

    success = handle_tool_use(
        tool_name="run_parallel_subagents",
        tool_input={"tasks": []},
        tool_use_id="tool-run-parallel-fail",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
        parent_agent=None,
    )

    assert success is False
    assert "requires parent agent" in history[-1]["content"]


def test_handle_tool_use_shows_diff_preview(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    monkeypatch.setattr("clippy.agent.tool_handler.generate_preview_diff", lambda *_: "diff")
    monkeypatch.setattr(
        "clippy.agent.tool_handler.format_diff_for_display",
        lambda diff, max_lines=100: ("shown-diff", False),
    )

    handle_tool_use(
        tool_name="read_file",
        tool_input={"path": "file.txt"},
        tool_use_id="tool-diff",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
    )

    assert any("shown-diff" in msg for msg in console.messages)


def test_handle_tool_use_handles_empty_diff(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    executor = RecordingExecutor()

    monkeypatch.setattr("clippy.agent.tool_handler.generate_preview_diff", lambda *_: "")

    handle_tool_use(
        tool_name="write_file",
        tool_input={"path": "file.txt", "content": ""},
        tool_use_id="tool-empty-diff",
        auto_approve_all=True,
        permission_manager=permission_manager,
        executor=executor,
        console=console,
        conversation_history=history,
        approval_callback=None,
    )

    assert any("No changes" in msg for msg in console.messages)


def test_display_tool_request_handles_diff_variants(
    monkeypatch: pytest.MonkeyPatch, console: DummyConsole
) -> None:
    display_tool_request(console, "write_file", {"path": "file.txt"}, diff_content="")
    assert any("No changes" in msg for msg in console.messages)

    console.messages.clear()
    display_tool_request(console, "mcp__server__tool", {"arg": 1}, diff_content="diff text")
    assert any("MCP Tool File Changes" in msg for msg in console.messages)

    console.messages.clear()
    monkeypatch.setattr("clippy.agent.tool_handler.is_mcp_tool", lambda name: True)
    monkeypatch.setattr(
        "clippy.agent.tool_handler.parse_mcp_qualified_name",
        lambda name: (_ for _ in ()).throw(ValueError("bad name")),
    )
    display_tool_request(console, "mcp__broken", {"arg": 1}, diff_content=None)
    assert any("mcp__broken" in msg for msg in console.messages)


def test_ask_approval_responses(monkeypatch: pytest.MonkeyPatch, console: DummyConsole) -> None:
    perm_manager = PermissionManager(PermissionConfig())

    # Yes response
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    assert (
        ask_approval(
            "write_file", {"path": "file"}, None, ActionType.WRITE_FILE, perm_manager, console
        )
        is True
    )

    # Allow response updates permissions
    inputs = iter(["invalid", "a"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    assert (
        ask_approval(
            "write_file", {"path": "file"}, None, ActionType.WRITE_FILE, perm_manager, console
        )
        is True
    )
    assert ActionType.WRITE_FILE in perm_manager.config.auto_approve

    # MCP Allow trusts server
    perm_manager = PermissionManager(PermissionConfig())
    monkeypatch.setattr("builtins.input", lambda prompt="": "a")
    monkeypatch.setattr("clippy.agent.tool_handler.is_mcp_tool", lambda name: True)
    monkeypatch.setattr(
        "clippy.agent.tool_handler.parse_mcp_qualified_name",
        lambda name: ("alpha", "tool"),
    )
    trusted: list[tuple[str, bool]] = []

    class StubMCP:
        def set_trusted(self, server_id: str, trusted_flag: bool) -> None:
            trusted.append((server_id, trusted_flag))

    assert (
        ask_approval(
            "mcp__alpha__tool",
            {},
            None,
            ActionType.MCP_TOOL_CALL,
            perm_manager,
            console,
            mcp_manager=StubMCP(),
        )
        is True
    )
    assert trusted == [("alpha", True)]

    monkeypatch.setattr("builtins.input", lambda prompt="": "a")
    console.messages.clear()
    assert (
        ask_approval(
            "mcp__alpha__tool",
            {},
            None,
            ActionType.MCP_TOOL_CALL,
            perm_manager,
            console,
            mcp_manager=None,
        )
        is True
    )
    assert any("MCP manager not available" in msg for msg in console.messages)

    # Reject response raises
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    with pytest.raises(InterruptedExceptionError):
        ask_approval("write_file", {}, None, ActionType.WRITE_FILE, perm_manager, console)


def test_handle_tool_use_with_approval_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    history: list[dict[str, Any]] = []
    permission_manager = PermissionManager(PermissionConfig())
    permission_manager.config.auto_approve.discard(ActionType.READ_FILE)
    permission_manager.config.require_approval.add(ActionType.READ_FILE)
    executor = RecordingExecutor()
    display_calls: list[str] = []

    monkeypatch.setattr(
        "clippy.agent.tool_handler.display_tool_request",
        lambda *args, **kwargs: display_calls.append("shown"),
    )

    success = handle_tool_use(
        tool_name="read_file",
        tool_input={},
        tool_use_id="tool-approval-callback",
        auto_approve_all=False,
        permission_manager=permission_manager,
        executor=executor,
        console=DummyConsole(),
        conversation_history=history,
        approval_callback=lambda *_: True,
    )

    assert success is True
    assert display_calls == []  # skipped when approval callback handles display


def test_handle_tool_use_approval_callback_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    permission_manager = PermissionManager(PermissionConfig())
    permission_manager.config.auto_approve.discard(ActionType.READ_FILE)
    permission_manager.config.require_approval.add(ActionType.READ_FILE)

    with pytest.raises(InterruptedExceptionError):
        handle_tool_use(
            tool_name="read_file",
            tool_input={},
            tool_use_id="tool-interrupt",
            auto_approve_all=False,
            permission_manager=permission_manager,
            executor=RecordingExecutor(),
            console=DummyConsole(),
            conversation_history=[],
            approval_callback=lambda *_: (_ for _ in ()).throw(InterruptedExceptionError()),
        )
