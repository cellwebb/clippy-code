"""Tests for clippy.cli.commands helper functions."""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from typing import Any

import pytest

from clippy.permissions import ActionType, PermissionLevel

commands = import_module("clippy.cli.commands")


class DummyConsole:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def print(self, message: Any) -> None:
        if hasattr(message, "renderable"):
            self.messages.append(str(message.renderable))
        else:
            self.messages.append(str(message))


def test_handle_exit_and_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    assert commands.handle_exit_command(console) == "break"
    assert any("Goodbye" in str(msg) for msg in console.messages)

    class StubAgent:
        def __init__(self) -> None:
            self.reset_called = False

        def reset_conversation(self) -> None:
            self.reset_called = True

    agent = StubAgent()
    console.messages.clear()
    result = commands.handle_reset_command(agent, console)
    assert result == "continue"
    assert agent.reset_called
    assert any("reset" in str(msg).lower() for msg in console.messages)


def test_handle_status_error_and_success() -> None:
    console = DummyConsole()

    class StubAgent:
        def __init__(self, status: dict[str, Any]) -> None:
            self._status = status

        def get_token_count(self) -> dict[str, Any]:
            return self._status

    error_status = {
        "error": "failure",
        "model": "gpt-5",
        "base_url": None,
        "message_count": 0,
    }
    commands.handle_status_command(StubAgent(error_status), console)
    assert any("Error counting tokens" in str(msg) for msg in console.messages)

    success_status = {
        "model": "gpt-5",
        "base_url": None,
        "message_count": 4,
        "usage_percent": 25.0,
        "total_tokens": 1024,
        "system_messages": 1,
        "system_tokens": 200,
        "user_messages": 1,
        "user_tokens": 300,
        "assistant_messages": 1,
        "assistant_tokens": 400,
        "tool_messages": 1,
        "tool_tokens": 124,
    }
    console.messages.clear()
    commands.handle_status_command(StubAgent(success_status), console)
    assert any("Token Usage" in str(msg) for msg in console.messages)


def test_handle_compact_command(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()

    class StubAgent:
        def __init__(self, response: tuple[bool, str, dict[str, Any]]) -> None:
            self._response = response

        def compact_conversation(self) -> tuple[bool, str, dict[str, Any]]:
            return self._response

    stats = {
        "before_tokens": 1000,
        "after_tokens": 600,
        "tokens_saved": 400,
        "reduction_percent": 40.0,
        "messages_before": 10,
        "messages_after": 6,
        "messages_summarized": 4,
    }
    result = commands.handle_compact_command(StubAgent((True, "done", stats)), console)
    assert result == "continue"
    assert any("Compacted" in str(msg) for msg in console.messages)

    console.messages.clear()
    result = commands.handle_compact_command(StubAgent((False, "cannot", {})), console)
    assert result == "continue"
    assert any("Cannot Compact" in str(msg) for msg in console.messages)


def test_handle_providers_and_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    monkeypatch.setattr(commands, "list_available_providers", lambda: [])
    commands.handle_providers_command(console)
    assert any("No providers" in str(msg) for msg in console.messages)

    providers = [("openai", "Default OpenAI provider")]
    monkeypatch.setattr(commands, "list_available_providers", lambda: providers)
    console.messages.clear()
    commands.handle_providers_command(console)
    assert any("openai" in str(msg) for msg in console.messages)

    monkeypatch.setattr(commands, "get_provider", lambda name: None)
    console.messages.clear()
    commands.handle_provider_command(console, "unknown")
    assert any("Unknown provider" in str(msg) for msg in console.messages)

    provider = SimpleNamespace(
        name="cerebras",
        description="Cerebras provider",
        base_url="https://api.cerebras.ai",
        api_key_env="CEREBRAS_API_KEY",
    )
    monkeypatch.setattr(commands, "get_provider", lambda name: provider)
    monkeypatch.setenv("CEREBRAS_API_KEY", "secret")
    console.messages.clear()
    commands.handle_provider_command(console, "cerebras")
    assert any("CEREBRAS_API_KEY" in str(msg) for msg in console.messages)


def test_handle_model_list_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5", base_url=None)

    monkeypatch.setattr(commands, "list_available_models", lambda: [])
    commands.handle_model_command(agent, console, "")
    assert any("No saved models" in str(msg) for msg in console.messages)

    console.messages.clear()
    monkeypatch.setattr(
        commands,
        "list_available_models",
        lambda: [("gpt-5", "OpenAI GPT-5", True)],
    )
    commands.handle_model_command(agent, console, "")
    assert any("Your Saved Models" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, '"unterminated')
    assert any("Error parsing arguments" in str(msg) for msg in console.messages)


def test_handle_model_add_remove_and_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    agent = SimpleNamespace(
        model="gpt-5",
        base_url=None,
        switch_model=lambda **kwargs: (True, "ok"),
    )

    user_manager = SimpleNamespace(
        add_model=lambda name, provider, model_id, is_default, compaction_threshold=None: (
            True,
            "added",
        ),
        remove_model=lambda name: (True, "removed"),
        set_default=lambda name: (False, "missing"),
        list_models=lambda: [],
    )
    monkeypatch.setattr(commands, "get_user_manager", lambda: user_manager)
    monkeypatch.setattr(commands, "list_available_models", lambda: [])

    commands.handle_model_command(agent, console, "add cerebras qwen --default")
    assert any("added" in str(msg) for msg in console.messages)
    assert any("Set as default" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, "add cerebras qwen --unknown")
    assert any("Unknown argument" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, "remove gpt-5")
    assert any("removed" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, "default missing")
    assert any("missing" in str(msg) for msg in console.messages)

    provider = SimpleNamespace(
        name="cerebras",
        base_url="https://api",
        api_key_env="CEREBRAS_API_KEY",
        description="",
    )
    monkeypatch.setattr(commands, "get_provider", lambda name: provider)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    console.messages.clear()
    commands.handle_model_command(agent, console, "use cerebras qwen")
    assert any("Warning" in str(msg) for msg in console.messages)

    user_manager = SimpleNamespace(
        get_model=lambda name: SimpleNamespace(name="alias", model_id="qwen", provider="cerebras")
        if name == "alias"
        else None,
        list_models=lambda: [],
    )
    monkeypatch.setattr(commands, "get_user_manager", lambda: user_manager)
    monkeypatch.setenv("CEREBRAS_API_KEY", "set")
    console.messages.clear()
    commands.handle_model_command(agent, console, "alias")
    assert any("Switched" in str(msg) for msg in console.messages)

    console.messages.clear()
    user_manager = SimpleNamespace(
        get_model=lambda name: None,
        list_models=lambda: [],
    )
    monkeypatch.setattr(commands, "get_user_manager", lambda: user_manager)
    commands.handle_model_command(agent, console, "nonexistent")
    assert any("not found" in msg for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, "   ")
    assert any("Usage: /model" in msg for msg in console.messages)


def test_handle_auto_command(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()

    class StubPermissionManager:
        def __init__(self, auto: set[ActionType]) -> None:
            self.config = SimpleNamespace(auto_approve=auto)
            self.updated: list[tuple[ActionType, PermissionLevel]] = []

        def update_permission(self, action: ActionType, level: PermissionLevel) -> None:
            self.config.auto_approve.discard(action)
            self.updated.append((action, level))

    manager = StubPermissionManager(set())
    agent = SimpleNamespace(permission_manager=manager)

    commands.handle_auto_command(agent, console, "")
    assert any("No Auto-approved" in str(msg) for msg in console.messages)

    manager = StubPermissionManager({ActionType.READ_FILE})
    agent = SimpleNamespace(permission_manager=manager)
    console.messages.clear()
    commands.handle_auto_command(agent, console, "")
    assert any("Auto-approved Actions" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_auto_command(agent, console, "revoke read_file")
    assert manager.updated == [(ActionType.READ_FILE, PermissionLevel.REQUIRE_APPROVAL)]

    console.messages.clear()
    commands.handle_auto_command(agent, console, "revoke unknown")
    assert any("Unknown action type" in str(msg) for msg in console.messages)

    manager = StubPermissionManager({ActionType.READ_FILE, ActionType.GREP})
    agent = SimpleNamespace(permission_manager=manager)
    console.messages.clear()
    commands.handle_auto_command(agent, console, "clear")
    assert len(manager.config.auto_approve) == 0
    assert any("Cleared auto-approvals" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_auto_command(agent, console, "clear")
    assert any("No auto-approvals" in msg for msg in console.messages)

    console.messages.clear()
    commands.handle_auto_command(agent, console, "unknown")
    assert any("Unknown /auto command" in msg for msg in console.messages)


def test_handle_mcp_command(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()

    class StubManager:
        def __init__(self) -> None:
            self.list_servers_calls = 0
            self.list_tools_calls = []
            self.allowed = []
            self.refreshed = False

        def list_servers(self):
            self.list_servers_calls += 1
            return [{"server_id": "alpha", "connected": True, "enabled": True, "tools_count": 3}]

        def list_tools(self, server: str | None = None):
            self.list_tools_calls.append(server)
            if server == "missing":
                return []
            return [
                {"server_id": "alpha", "name": "tool", "description": "desc"},
                {"server_id": "alpha", "name": "tool2", "description": "desc2"},
            ]

        def start(self):
            self.refreshed = True

        def stop(self):
            self.refreshed = True

        def set_trusted(self, server_id: str, trusted: bool) -> None:
            self.allowed.append((server_id, trusted))

        def set_enabled(self, server_id: str, enabled: bool) -> bool:
            return True if server_id == "alpha" else False

    manager = StubManager()
    agent = SimpleNamespace(mcp_manager=manager)

    commands.handle_mcp_command(agent, console, "")
    assert any("Usage: /mcp" in msg for msg in console.messages)

    console.messages.clear()
    commands.handle_mcp_command(SimpleNamespace(mcp_manager=None), console, "list")
    assert any("MCP functionality not available" in msg for msg in console.messages)

    console.messages.clear()
    commands.handle_mcp_command(agent, console, "list")
    assert manager.list_servers_calls == 1

    console.messages.clear()
    commands.handle_mcp_command(agent, console, "tools alpha")
    assert manager.list_tools_calls[-1] == "alpha"

    console.messages.clear()
    commands.handle_mcp_command(agent, console, "tools missing")
    assert any("No tools" in str(msg) for msg in console.messages[-1:])

    console.messages.clear()
    commands.handle_mcp_command(agent, console, "tools")
    assert manager.list_tools_calls[-1] is None
    console.messages.clear()
    commands.handle_mcp_command(agent, console, "refresh")
    assert any("Refreshing" in str(msg) for msg in console.messages)
    assert manager.refreshed is True

    console.messages.clear()
    commands.handle_mcp_command(agent, console, "allow alpha")
    commands.handle_mcp_command(agent, console, "revoke alpha")
    assert manager.allowed == [("alpha", True), ("alpha", False)]

    console.messages.clear()
    commands.handle_mcp_command(agent, console, "unknown")
    assert any("Unknown MCP command" in str(msg) for msg in console.messages)


def test_handle_subagent_command(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5")

    class StubConfigManager:
        def __init__(self) -> None:
            self.set_calls = []
            self.clear_calls = []
            self.reset_called = False

        def get_all_configurations(self):
            return {
                "general": {"model_override": None, "max_iterations": 5},
                "fast": {"model_override": "gpt-3.5", "max_iterations": 3},
            }

        def set_model_override(self, subagent_type: str, model: str) -> None:
            if subagent_type == "invalid":
                raise ValueError("bad type")
            self.set_calls.append((subagent_type, model))

        def clear_model_override(self, subagent_type: str) -> bool:
            self.clear_calls.append(subagent_type)
            return subagent_type == "fast"

        def clear_all_overrides(self) -> int:
            self.reset_called = True
            return 2

    config_manager = StubConfigManager()
    monkeypatch.setattr(commands, "get_subagent_config_manager", lambda: config_manager)
    monkeypatch.setattr(commands, "list_subagent_types", lambda: ["general", "fast"])

    commands.handle_subagent_command(agent, console, "")
    assert any("Subagent Type Configurations" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_subagent_command(agent, console, '"unterminated')
    assert any("Error parsing arguments" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_subagent_command(agent, console, "set fast gpt-4")
    assert config_manager.set_calls == [("fast", "gpt-4")]

    console.messages.clear()
    commands.handle_subagent_command(agent, console, "set invalid gpt-4")
    assert any("bad type" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_subagent_command(agent, console, "clear fast")
    assert config_manager.clear_calls[-1] == "fast"
    assert any("Cleared model override" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_subagent_command(agent, console, "clear missing")
    assert any(
        "No model override" in str(msg) or "No model overrides" in str(msg)
        for msg in console.messages
    )

    console.messages.clear()
    commands.handle_subagent_command(agent, console, "reset")
    assert config_manager.reset_called
    assert any("Cleared 2 model override" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_subagent_command(agent, console, "unknown")
    assert any("Unknown subcommand" in str(msg) for msg in console.messages)


def test_handle_command_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    agent = SimpleNamespace()

    monkeypatch.setattr(commands, "handle_exit_command", lambda c: "break")
    assert commands.handle_command("/exit", agent, console) == "break"

    monkeypatch.setattr(commands, "handle_reset_command", lambda a, c: "continue")
    assert commands.handle_command("/reset", agent, console) == "continue"

    monkeypatch.setattr(commands, "handle_help_command", lambda c: "continue")
    assert commands.handle_command("/help", agent, console) == "continue"

    monkeypatch.setattr(commands, "handle_status_command", lambda a, c: "continue")
    assert commands.handle_command("/status", agent, console) == "continue"

    monkeypatch.setattr(commands, "handle_auto_command", lambda a, c, args: "continue")
    assert commands.handle_command("/auto list", agent, console) == "continue"

    monkeypatch.setattr(commands, "handle_mcp_command", lambda a, c, args: "continue")
    assert commands.handle_command("/mcp list", agent, console) == "continue"

    monkeypatch.setattr(commands, "handle_subagent_command", lambda a, c, args: "continue")
    assert commands.handle_command("/subagent list", agent, console) == "continue"

    monkeypatch.setattr(commands, "handle_resume_command", lambda a, c, args: "continue")
    assert commands.handle_command("/resume", agent, console) == "continue"
    assert commands.handle_command("/resume project1", agent, console) == "continue"

    assert commands.handle_command("normal text", agent, console) is None


def test_handle_resume_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the /resume command functionality."""
    console = DummyConsole()

    class StubAgent:
        def __init__(self) -> None:
            self.conversation_history = []
            self.conversations_dir = None

        def load_conversation(self, name: str) -> tuple[bool, str]:
            return (True, f"Conversation '{name}' loaded successfully")

    # Test with specific conversation name (this should work without needing interactive input)
    agent = StubAgent()
    result = commands.handle_resume_command(agent, console, "conversation-20251027-153000")

    # Verify the function completed successfully and produced expected output
    assert result == "continue"
    assert any("loaded successfully" in str(msg) for msg in console.messages)


def test_handle_resume_command_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that /resume command handles errors gracefully."""
    console = DummyConsole()

    class StubAgent:
        def __init__(self) -> None:
            pass

        def load_conversation(self, name: str) -> tuple[bool, str]:
            return (False, f"No saved conversation found with name '{name}'")

    # Mock the conversation discovery function to return some conversations
    def mock_get_conversations(agent):
        return [
            {
                "name": "conversation-20251027-143000",
                "timestamp": 1234567890,
                "model": "gpt-5",
                "message_count": 5,
            },
            {
                "name": "conversation-20251027-153000",
                "timestamp": 1234567900,
                "model": "gpt-5",
                "message_count": 3,
            },
        ]

    monkeypatch.setattr(
        "clippy.cli.commands._get_all_conversations_with_timestamps", mock_get_conversations
    )

    agent = StubAgent()
    commands.handle_resume_command(agent, console, "nonexistent")
    # Check for the error message substring that should be present
    assert any("No saved conversation found with name" in str(msg) for msg in console.messages)
    assert any("Available conversations" in str(msg) for msg in console.messages)


def test_handle_resume_command_no_saved_conversations(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that /resume command handles case with no saved conversations."""
    console = DummyConsole()

    class StubAgent:
        def __init__(self) -> None:
            pass

        def load_conversation(self, name: str) -> tuple[bool, str]:
            return (False, "No saved conversation found with name 'default'")

    # Mock the conversation discovery function to return empty list
    def mock_get_conversations(agent):
        return []

    monkeypatch.setattr(
        "clippy.cli.commands._get_all_conversations_with_timestamps", mock_get_conversations
    )

    agent = StubAgent()
    commands.handle_resume_command(agent, console, "")
    # Check for the proper error message for no conversations
    assert any("No saved conversations found" in str(msg) for msg in console.messages)
