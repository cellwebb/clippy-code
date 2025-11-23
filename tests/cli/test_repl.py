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
        self.width = 80  # Default console width for testing

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
    """Test double-ESC functionality by recreating the key binding logic."""
    # Import dependencies to test the logic directly

    # Mock time and test the ESC handler logic directly
    exit_calls: list[Any] = []
    time_values = iter([0.0, 0.4])  # 0.0 first, then 0.4 seconds later
    last_esc_time = {"time": -1000.0}  # Start with a very old timestamp
    esc_timeout = 0.5

    def mock_time():
        return next(time_values)

    def mock_event_app_exit(exception=None):
        exit_calls.append(exception)

    def esc_handler(event):
        """Duplicate of the ESC handler logic from repl.py"""
        current_time = mock_time()
        time_diff = current_time - last_esc_time["time"]

        if time_diff < esc_timeout:
            # Double-ESC detected - raise KeyboardInterrupt
            mock_event_app_exit(exception=KeyboardInterrupt())
        else:
            # First ESC - just record the time
            last_esc_time["time"] = current_time

    event = SimpleNamespace(app=SimpleNamespace(exit=mock_event_app_exit))

    # Test the double-ESC logic
    esc_handler(event)  # first ESC should just record time
    assert len(exit_calls) == 0  # No exit call yet

    esc_handler(event)  # second ESC should trigger exit (0.4 < 0.5 timeout)
    assert len(exit_calls) == 1
    assert isinstance(exit_calls[0], KeyboardInterrupt)

    # Also test that REPL setup works (simpler test)
    agent = StubAgent()
    console = DummyConsole()
    session = StubPromptSession(["/exit"])
    kb_stub = KeyBindingsStub()

    monkeypatch.setattr("clippy.cli.repl.KeyBindings", lambda: kb_stub)
    monkeypatch.setattr("clippy.cli.repl.PromptSession", lambda *args, **kwargs: session)
    monkeypatch.setattr("clippy.cli.repl.Console", lambda: console)
    monkeypatch.setattr("clippy.cli.repl.handle_command", lambda *_args, **_kwargs: "break")

    # Just test that REPL setup works and key bindings are created
    repl.run_interactive(agent, auto_approve=False)

    assert kb_stub.handler is not None
