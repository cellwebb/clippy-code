"""Tests for clippy.cli.main."""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from typing import Any

import pytest

cli_main = import_module("clippy.cli.main")


def test_resolve_model_none() -> None:
    assert cli_main.resolve_model(None) == (None, None, None, None)


def test_resolve_model_with_saved_model(monkeypatch: pytest.MonkeyPatch) -> None:
    model = SimpleNamespace(model_id="model-1")
    provider = SimpleNamespace(
        base_url="https://api.example.com",
        api_key_env="API_KEY",
        pydantic_system="openai",
    )
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (model, provider))

    resolved = cli_main.resolve_model("my-model")

    assert resolved == ("model-1", "https://api.example.com", "API_KEY", provider)


def test_resolve_model_raw_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (None, None))

    resolved = cli_main.resolve_model("provider/model-x")

    assert resolved == ("provider/model-x", None, None, None)


def test_resolve_model_saved_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    model = SimpleNamespace(model_id="claude-sonnet")
    provider = SimpleNamespace(
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        pydantic_system="anthropic",
    )
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (model, provider))

    resolved = cli_main.resolve_model("my-anthropic")

    assert resolved == ("anthropic:claude-sonnet", None, "ANTHROPIC_API_KEY", provider)


def test_resolve_model_raw_prefixed_non_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (None, None))

    resolved = cli_main.resolve_model("anthropic:claude-sonnet")

    assert resolved == ("anthropic:claude-sonnet", None, None, None)


def test_resolve_model_raw_hf_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (None, None))

    resolved = cli_main.resolve_model("hf:zai-org/GLM-4.6")

    assert resolved == ("hf:zai-org/GLM-4.6", None, None, None)


def _make_args(**overrides: Any) -> SimpleNamespace:
    defaults = {
        "prompt": [],
        "yes": False,
        "yolo": False,
        "verbose": False,
        "model": None,
        "base_url": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_main_runs_interactive_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setattr(cli_main, "load_env", lambda: None)

    args = _make_args(verbose=True)
    monkeypatch.setattr(cli_main, "create_parser", lambda: SimpleNamespace(parse_args=lambda: args))

    logged: list[bool] = []
    monkeypatch.setattr(cli_main, "setup_logging", lambda verbose: logged.append(verbose))

    default_model = SimpleNamespace(model_id="gpt-5")
    default_provider = SimpleNamespace(
        base_url="https://default",
        api_key_env="OPENAI_API_KEY",
        pydantic_system="openai",
    )
    monkeypatch.setattr(
        cli_main,
        "get_default_model_config",
        lambda: (default_model, default_provider),
    )
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (None, None))
    monkeypatch.setattr(cli_main, "load_config", lambda: None)

    executors: list[Any] = []

    class StubExecutor:
        def __init__(self, permission_manager: Any) -> None:
            self.permission_manager = permission_manager
            self.mcp_manager = None
            executors.append(self)

        def set_mcp_manager(self, manager: Any) -> None:
            self.mcp_manager = manager

    monkeypatch.setattr(cli_main, "ActionExecutor", StubExecutor)
    monkeypatch.setattr(
        cli_main,
        "PermissionManager",
        lambda config: SimpleNamespace(config=config),
    )

    created_agents: list[Any] = []

    class StubAgent:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            created_agents.append(self)

    monkeypatch.setattr(cli_main, "ClippyAgent", StubAgent)

    run_calls: dict[str, Any] = {}
    monkeypatch.setattr(
        cli_main,
        "run_interactive",
        lambda agent, auto: run_calls.setdefault("values", (agent, auto)),
    )

    messages: list[str] = []

    class DummyConsole:
        def print(self, message: str) -> None:
            messages.append(message)

    monkeypatch.setattr(cli_main, "Console", lambda: DummyConsole())

    cli_main.main()

    assert logged == [True]
    assert created_agents[0].kwargs["api_key"] == "secret"
    assert created_agents[0].kwargs["model"] == "gpt-5"
    assert created_agents[0].kwargs["base_url"] == "https://default"
    assert created_agents[0].kwargs["provider_config"] is default_provider
    assert run_calls["values"][1] is False
    assert run_calls["values"][0] is created_agents[0]


def test_main_missing_api_key_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli_main, "load_env", lambda: None)

    args = _make_args(prompt=["do", "something"])
    monkeypatch.setattr(cli_main, "create_parser", lambda: SimpleNamespace(parse_args=lambda: args))

    default_model = SimpleNamespace(model_id="gpt-5")
    default_provider = SimpleNamespace(
        base_url="https://default",
        api_key_env="OPENAI_API_KEY",
        pydantic_system="openai",
    )
    monkeypatch.setattr(
        cli_main,
        "get_default_model_config",
        lambda: (default_model, default_provider),
    )
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (None, None))
    monkeypatch.setattr(cli_main, "load_config", lambda: None)
    monkeypatch.setattr(cli_main, "setup_logging", lambda verbose: None)

    class DummyConsole:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def print(self, message: str) -> None:
            self.messages.append(message)

    console = DummyConsole()
    monkeypatch.setattr(cli_main, "Console", lambda: console)

    with pytest.raises(SystemExit) as exc:
        cli_main.main()

    assert exc.value.code == 1
    assert any("OPENAI_API_KEY" in msg for msg in console.messages)


def test_main_handles_mcp_manager_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setattr(cli_main, "load_env", lambda: None)

    args = _make_args(prompt=["hello"])
    monkeypatch.setattr(cli_main, "create_parser", lambda: SimpleNamespace(parse_args=lambda: args))
    monkeypatch.setattr(cli_main, "setup_logging", lambda verbose: None)

    default_model = SimpleNamespace(model_id="gpt-5")
    default_provider = SimpleNamespace(
        base_url="https://default",
        api_key_env="OPENAI_API_KEY",
        pydantic_system="openai",
    )
    monkeypatch.setattr(
        cli_main,
        "get_default_model_config",
        lambda: (default_model, default_provider),
    )
    monkeypatch.setattr(cli_main, "get_model_config", lambda name: (None, None))

    monkeypatch.setattr(cli_main, "load_config", lambda: {"servers": []})

    class FailingManager:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def start(self) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(cli_main, "Manager", FailingManager)
    monkeypatch.setattr(
        cli_main,
        "ActionExecutor",
        lambda pm: SimpleNamespace(set_mcp_manager=lambda m: None),
    )
    monkeypatch.setattr(
        cli_main,
        "PermissionManager",
        lambda config: SimpleNamespace(config=config),
    )
    monkeypatch.setattr(cli_main, "ClippyAgent", lambda **kwargs: SimpleNamespace(kwargs=kwargs))

    run_calls: dict[str, Any] = {}
    monkeypatch.setattr(
        cli_main,
        "run_one_shot",
        lambda agent, prompt, auto: run_calls.setdefault("values", (agent, prompt, auto)),
    )

    messages: list[str] = []

    class DummyConsole:
        def print(self, message: str) -> None:
            messages.append(message)

    monkeypatch.setattr(cli_main, "Console", lambda: DummyConsole())

    cli_main.main()

    assert any("Failed to initialize MCP manager" in msg for msg in messages)
    assert run_calls["values"][1] == "hello"
