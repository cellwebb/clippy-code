"""Tests for the interactive CLI REPL."""

from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

import pytest

from clippy.cli import repl


class DummyConsole:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, message: Any) -> None:
        self.messages.append(str(message))


class StubPromptSession:
    def __init__(self, responses: Iterable[Any]) -> None:
        self._responses = iter(responses)

    def prompt(self, _prompt: str = "") -> str:
        value = next(self._responses)
        if isinstance(value, BaseException):
            raise value
        return value


class KeyBindingsStub:
    def __init__(self) -> None:
        self.handler: Any = None

    def add(self, _key: str):
        def decorator(func: Any) -> Any:
            self.handler = func
            return func

        return decorator


class StubAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def run(self, message: str, auto_approve_all: bool) -> None:
        self.calls.append((message, auto_approve_all))

    def reset_conversation(self) -> None:
        pass

    model = "gpt-5"
    base_url: str | None = None


@pytest.fixture(autouse=True)
def _patch_prompt_toolkit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("clippy.cli.repl.FileHistory", lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr("clippy.cli.repl.AutoSuggestFromHistory", lambda *args, **kwargs: None)


def test_run_interactive_processes_command_and_input(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = StubAgent()
    console = DummyConsole()

    responses = ["/help", "write docs", EOFError()]
    session = StubPromptSession(responses)

    monkeypatch.setattr("clippy.cli.repl.PromptSession", lambda *args, **kwargs: session)
    monkeypatch.setattr("clippy.cli.repl.Console", lambda: console)

    handled: list[str] = []

    def fake_handle_command(user_input: str, *_args: Any, **_kwargs: Any) -> str | None:
        if user_input.startswith("/"):
            handled.append(user_input)
            return "continue"
        return None

    monkeypatch.setattr("clippy.cli.repl.handle_command", fake_handle_command)

    repl.run_interactive(agent, auto_approve=False)

    assert handled == ["/help"]
    assert agent.calls == [("write docs", False)]
    assert any("Goodbye" in msg for msg in console.messages)


def test_run_interactive_handles_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = StubAgent()
    console = DummyConsole()

    responses = [KeyboardInterrupt(), "final", EOFError()]
    session = StubPromptSession(responses)

    monkeypatch.setattr("clippy.cli.repl.PromptSession", lambda *args, **kwargs: session)
    monkeypatch.setattr("clippy.cli.repl.Console", lambda: console)

    def fake_handle_command(*_args: Any, **_kwargs: Any) -> str | None:
        return None

    monkeypatch.setattr("clippy.cli.repl.handle_command", fake_handle_command)

    repl.run_interactive(agent, auto_approve=True)

    # First prompt raises KeyboardInterrupt, which should cause a notification and continue
    assert any("Use /exit" in msg for msg in console.messages)
    assert agent.calls == [("final", True)]


def test_run_interactive_double_escape(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = StubAgent()
    console = DummyConsole()
    session = StubPromptSession(["/exit"])
    kb_stub = KeyBindingsStub()

    monkeypatch.setattr("clippy.cli.repl.KeyBindings", lambda: kb_stub)
    monkeypatch.setattr("clippy.cli.repl.PromptSession", lambda *args, **kwargs: session)
    monkeypatch.setattr("clippy.cli.repl.Console", lambda: console)
    monkeypatch.setattr("clippy.cli.repl.handle_command", lambda *_args, **_kwargs: "break")

    repl.run_interactive(agent, auto_approve=False)

    assert kb_stub.handler is not None

    exit_calls: list[Any] = []
    time_values = iter([0.0, 0.4])
    monkeypatch.setattr("clippy.cli.repl.time.time", lambda: next(time_values))

    event = SimpleNamespace(
        app=SimpleNamespace(exit=lambda exception=None: exit_calls.append(exception))
    )

    kb_stub.handler(event)  # first ESC
    kb_stub.handler(event)  # second ESC within timeout triggers exit

    assert isinstance(exit_calls[0], KeyboardInterrupt)
