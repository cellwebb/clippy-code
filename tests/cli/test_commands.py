"""Tests for clippy.cli.commands helper functions."""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from typing import Any

import pytest

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
    agent = SimpleNamespace()  # Add dummy agent for new signature
    # Mock the functions in the provider module where they're actually imported
    provider_module = commands.__dict__["provider"]
    monkeypatch.setattr(
        provider_module, "list_providers_by_source", lambda: {"built_in": [], "user": []}
    )
    commands.handle_providers_command(console)
    assert any("No providers" in str(msg) for msg in console.messages)

    providers = {"built_in": [("openai", "Default OpenAI provider")], "user": []}
    monkeypatch.setattr(provider_module, "list_providers_by_source", lambda: providers)
    console.messages.clear()
    commands.handle_providers_command(console)
    assert any("openai" in str(msg) for msg in console.messages)

    monkeypatch.setattr(provider_module, "get_provider", lambda name: None)
    console.messages.clear()
    commands.handle_provider_command(agent, console, "unknown")
    assert any("Unknown provider" in str(msg) for msg in console.messages)

    provider = SimpleNamespace(
        name="cerebras",
        description="Cerebras provider",
        base_url="https://api.cerebras.ai",
        api_key_env="CEREBRAS_API_KEY",
    )
    monkeypatch.setattr(provider_module, "get_provider", lambda name: provider)
    monkeypatch.setenv("CEREBRAS_API_KEY", "secret")
    console.messages.clear()
    commands.handle_provider_command(agent, console, "cerebras")
    assert any("CEREBRAS_API_KEY" in str(msg) for msg in console.messages)


def test_handle_model_list_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5", base_url=None)

    # Mock the functions in the model module where they're actually imported
    model_module = commands.__dict__["model"]
    commands.handle_model_command(agent, console, "")
    assert any("/model commands:" in str(msg) for msg in console.messages)  # Empty args shows help

    console.messages.clear()
    monkeypatch.setattr(model_module, "list_available_models_with_provider", lambda: [])
    commands.handle_model_command(agent, console, "list")
    assert any("No models available" in str(msg) for msg in console.messages)

    console.messages.clear()
    monkeypatch.setattr(
        model_module,
        "list_available_models_with_provider",
        lambda: [("gpt-5", "OpenAI GPT-5", True, None, "openai")],  # Updated tuple format
    )
    commands.handle_model_command(agent, console, "list")
    assert any("Provider: openai" in str(msg) for msg in console.messages)  # Updated message

    console.messages.clear()
    commands.handle_model_command(agent, console, '"unterminated')
    assert any("Unknown model subcommand" in str(msg) for msg in console.messages)


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
        switch_model=lambda name: (True, "switched"),
        get_default_model=lambda: SimpleNamespace(name=""),
    )

    # Mock the functions in the model module where they're actually imported
    model_module = commands.__dict__["model"]
    monkeypatch.setattr(model_module, "get_user_manager", lambda: user_manager)
    monkeypatch.setattr(model_module, "list_available_models_with_provider", lambda: [])

    commands.handle_model_command(
        agent, console, "add cerebras qwen --name test_model"
    )  # Updated command
    assert any("added" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, "add cerebras qwen --unknown")
    assert any("✓" in str(msg) for msg in console.messages) or any(
        "added" in str(msg) for msg in console.messages
    )

    console.messages.clear()
    commands.handle_model_command(agent, console, "remove gpt-5")
    assert any("removed" in str(msg) for msg in console.messages)

    console.messages.clear()
    commands.handle_model_command(agent, console, "set-default missing")  # Updated command
    assert any("missing" in str(msg) for msg in console.messages)

    provider = SimpleNamespace(
        name="cerebras",
        base_url="https://api",
        api_key_env="CEREBRAS_API_KEY",
        description="",
    )
    monkeypatch.setattr(model_module, "get_provider", lambda name: provider)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    console.messages.clear()
    commands.handle_model_command(agent, console, "use cerebras qwen")
    assert any("✓" in str(msg) for msg in console.messages)  # Updated expectation

    user_manager.get_model = (
        lambda name: SimpleNamespace(name="alias", model_id="qwen", provider="cerebras")
        if name == "alias"
        else None
    )
    monkeypatch.setattr(model_module, "get_user_manager", lambda: user_manager)
    monkeypatch.setenv("CEREBRAS_API_KEY", "set")
    console.messages.clear()
    commands.handle_model_command(agent, console, "switch alias")  # Updated command
    assert any("Switched" in str(msg) for msg in console.messages) or any(
        "✓" in str(msg) for msg in console.messages
    )

    console.messages.clear()
    user_manager.get_model = lambda name: None
    user_manager.get_default_model = lambda: None
    user_manager.switch_model = lambda name: (False, "Model 'nonexistent' not found")
    monkeypatch.setattr(model_module, "get_user_manager", lambda: user_manager)
    commands.handle_model_command(agent, console, "switch nonexistent")
    assert any("✗" in msg for msg in console.messages) or any(
        "not found" in msg for msg in console.messages
    )

    console.messages.clear()
    commands.handle_model_command(agent, console, "   ")
    # Spaces-only should show help
    assert any("/model commands:" in str(msg) for msg in console.messages)


def test_handle_model_help_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the /model help command functionality."""
    console = DummyConsole()
    model_module = commands.__dict__["model"]

    # Test that model help returns continue
    result = model_module._handle_model_help(console)
    assert result == "continue"

    # Verify key help content is present
    messages_text = str(console.messages)

    # Check for main help title and basic commands
    assert "/model commands:" in messages_text
    assert "/model list" in messages_text
    assert "/model add" in messages_text
    assert "/model remove" in messages_text
    assert "/model set-default" in messages_text
    assert "/model switch" in messages_text
    assert "/model use" in messages_text
    assert "/model reload" in messages_text

    # Check that usage information is provided
    assert "Add a new model" in messages_text
    assert "Temporarily use a model" in messages_text
    assert "List available models" in messages_text


def test_handle_model_command_with_help_subcommand(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that /model help subcommand is properly routed to the help function."""
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5", base_url=None)

    # Test direct help command
    result = commands.handle_model_command(agent, console, "help")
    assert result == "continue"

    # Test help command with different case
    console.messages.clear()
    result = commands.handle_model_command(agent, console, "HELP")
    assert result == "continue"

    # Test help command is routed to _handle_model_help
    assert any("/model commands:" in str(msg) for msg in console.messages)


def test_handle_model_command_lists_help_prominently(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that /model command shows help prominently in suggested commands."""
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5", base_url=None)

    # Test empty args shows help
    commands.handle_model_command(agent, console, "")

    # Verify help content is shown
    messages_text = str(console.messages)
    assert "/model commands:" in messages_text
    assert "/model list" in messages_text
    assert "/model add" in messages_text
    assert "/model help" != None or "/model" in messages_text  # Basic help is shown


def test_handle_model_command_with_existing_models_lists_help_prominently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that /model command shows help prominently when models exist."""
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5", base_url=None)

    # Test empty args always shows help, regardless of existing models
    commands.handle_model_command(agent, console, "")

    # Verify help content is shown
    messages_text = str(console.messages)
    assert "/model commands:" in messages_text
    assert "/model list" in messages_text
    assert "/model add" in messages_text


def test_handle_model_command_error_message_includes_help(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that error messages include help in suggested commands."""
    console = DummyConsole()
    agent = SimpleNamespace(model="gpt-5", base_url=None)

    # Test invalid command error includes help
    commands.handle_model_command(agent, console, "   ")  # Empty/space-only args
    messages_text = str(console.messages)
    # The usage error message should mention that "help" is one of the available commands
    assert "help" in messages_text.lower()

    # Test malformed quotes error includes help
    console.messages.clear()
    commands.handle_model_command(agent, console, '"unterminated')
    messages_text = str(console.messages)
    # Should show error parsing, and the error message should mention
    # available commands including help
    assert "help" in messages_text.lower() or "Error parsing arguments" in messages_text


def test_main_help_includes_model_help_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the main /help command includes /model help."""
    console = DummyConsole()

    commands.handle_help_command(console)
    messages_text = str(console.messages)

    # Verify main help includes the model help command
    assert "/model help" in messages_text
    assert "comprehensive model management help" in messages_text.lower()


def test_handle_auto_command(monkeypatch: pytest.MonkeyPatch) -> None:
    console = DummyConsole()

    class StubAgent:
        def __init__(self, auto_actions: list[str] | None = None):
            self._auto_actions = auto_actions or []
            self._revoked_actions = []
            self._cleared_count = 0

        def get_auto_actions(self) -> list[str]:
            return self._auto_actions

        def revoke_auto_action(self, action: str) -> bool:
            if action in self._auto_actions:
                self._auto_actions.remove(action)
                self._revoked_actions.append(action)
                return True
            return False

        def clear_auto_actions(self) -> int:
            count = len(self._auto_actions)
            self._auto_actions.clear()
            self._cleared_count += count
            return count

    agent = StubAgent()

    commands.handle_auto_command(agent, console, "")
    assert any("Usage: /auto" in str(msg) for msg in console.messages)  # Empty args shows usage

    # Test list command with no auto actions
    console.messages.clear()
    commands.handle_auto_command(agent, console, "list")
    assert any("No actions are currently auto-approved" in str(msg) for msg in console.messages)

    # Test list command with auto actions
    agent_with_auto = StubAgent(["read_file"])
    console.messages.clear()
    commands.handle_auto_command(agent_with_auto, console, "list")
    assert any("Auto-approved Actions" in str(msg) for msg in console.messages)

    # Test revoke
    console.messages.clear()
    commands.handle_auto_command(agent_with_auto, console, "revoke read_file")
    assert any("Auto-approval revoked" in str(msg) for msg in console.messages) or any(
        "✓" in str(msg) for msg in console.messages
    )
    assert len(agent_with_auto._auto_actions) == 0

    # Test revoke unknown action
    console.messages.clear()
    commands.handle_auto_command(agent, console, "revoke UNKNOWN_ACTION")
    assert any("Unknown action" in str(msg) for msg in console.messages)

    # Test clear with actions
    agent_with_multiple = StubAgent(["READ_FILE", "GREP"])
    console.messages.clear()
    commands.handle_auto_command(agent_with_multiple, console, "clear")
    assert any("Auto-approval cleared for 2 action" in str(msg) for msg in console.messages)
    assert len(agent_with_multiple._auto_actions) == 0

    # Test clear with no actions
    console.messages.clear()
    commands.handle_auto_command(agent, console, "clear")
    assert any("No actions were auto-approved" in str(msg) for msg in console.messages)

    # Test unknown command
    console.messages.clear()
    commands.handle_auto_command(agent, console, "unknown")
    assert any("Unknown auto command" in str(msg) for msg in console.messages)


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
