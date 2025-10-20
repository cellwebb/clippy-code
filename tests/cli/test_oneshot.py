"""Tests for the one-shot CLI mode."""

from __future__ import annotations

import pytest

from clippy.agent import InterruptedExceptionError
from clippy.cli.oneshot import run_one_shot


class DummyConsole:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, message: str) -> None:
        self.messages.append(message)


def test_run_one_shot_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("clippy.cli.oneshot.Console", lambda: DummyConsole())

    run_calls: list[tuple[str, bool]] = []

    class StubAgent:
        def run(self, prompt: str, auto_approve_all: bool) -> None:
            run_calls.append((prompt, auto_approve_all))

    agent = StubAgent()
    run_one_shot(agent, "build project", True)

    assert run_calls == [("build project", True)]


@pytest.mark.parametrize(
    "error, message",
    [
        (InterruptedExceptionError(), "Execution interrupted"),
        (KeyboardInterrupt(), "Interrupted"),
        (RuntimeError("boom"), "Error"),
    ],
)
def test_run_one_shot_handles_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, message: str
) -> None:
    console = DummyConsole()
    monkeypatch.setattr("clippy.cli.oneshot.Console", lambda: console)

    class StubAgent:
        def run(self, prompt: str, auto_approve_all: bool) -> None:
            raise error

    agent = StubAgent()

    with pytest.raises(SystemExit) as exc:
        run_one_shot(agent, "task", False)

    assert exc.value.code == 1
    assert any(message in m for m in console.messages)
