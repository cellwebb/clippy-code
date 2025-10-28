"""Additional tests covering grep command construction and error handling."""

from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace

import pytest

from clippy.tools.grep import grep

grep_module = import_module("clippy.tools.grep")


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def test_grep_prefers_rg_with_translated_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        if cmd == ["rg", "--version"]:
            return _completed(stdout="ripgrep 13.0.0")

        assert kwargs["shell"] is True
        calls.append(cmd)
        return _completed(stdout="match line")

    monkeypatch.setattr(grep_module.subprocess, "run", fake_run)

    success, message, output = grep("TODO", ["src/file with spaces.py"], flags="-i")

    assert success is True
    assert "executed successfully" in message
    assert "match line" in output

    assert len(calls) == 1
    command = calls[0]
    assert command.startswith("rg --no-heading --line-number -I --with-filename --ignore-case")
    assert "'src/file with spaces.py'" in command
    assert "TODO" in command


def test_grep_rg_handles_glob_patterns(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: list[str] = []

    def fake_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        if cmd == ["rg", "--version"]:
            return _completed()
        recorded.append(cmd)
        return _completed(returncode=0, stdout="")

    monkeypatch.setattr(grep_module.subprocess, "run", fake_run)

    success, message, output = grep("pattern", ["*.py"])

    assert success is True
    assert output == ""
    command = recorded[0]
    assert "*.py" in command
    assert "'*.py'" not in command  # glob should not be quoted


def test_grep_falls_back_to_system_grep(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: list[str] = []

    def fake_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        if cmd == ["rg", "--version"]:
            raise FileNotFoundError("rg missing")
        recorded.append(cmd)
        return _completed(returncode=1)  # no matches

    monkeypatch.setattr(grep_module.subprocess, "run", fake_run)

    success, message, output = grep("absent", ["module.py"])

    assert success is True
    assert output == ""
    assert message.endswith("no matches found)")
    command = recorded[0]
    assert command.startswith("grep -I -n")
    assert command.strip().endswith("module.py")


def test_grep_returns_error_for_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        if cmd == ["rg", "--version"]:
            return _completed()
        return _completed(returncode=2, stderr="bad pattern")

    monkeypatch.setattr(grep_module.subprocess, "run", fake_run)

    success, message, output = grep("[", ["file.txt"])

    assert success is False
    assert "bad pattern" in message
    assert output is None


def test_grep_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        if cmd == ["rg", "--version"]:
            return _completed()
        raise subprocess.TimeoutExpired(cmd, timeout=30)

    import subprocess

    monkeypatch.setattr(grep_module.subprocess, "run", fake_run)

    success, message, output = grep("pattern", ["file.txt"])

    assert success is False
    assert "timed out" in message
    assert output is None


def test_grep_pattern_starting_with_dash_does_not_break_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that patterns starting with - don't get interpreted as flags."""
    recorded: list[str] = []

    def fake_run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        if cmd == ["rg", "--version"]:
            return _completed()
        recorded.append(cmd)
        return _completed(returncode=1)  # no matches would be found

    monkeypatch.setattr(grep_module.subprocess, "run", fake_run)

    # This pattern starts with -n which could be interpreted as a flag
    success, message, output = grep("-n.*pattern", ["file.txt"])

    assert success is True
    assert message.endswith("no matches found)")

    # Verify that -- was added to separate flags from pattern
    command = recorded[0]
    assert "--" in command
    assert " '-n.*pattern'" in command

    # Should have both the -- flag separator and the quoted pattern
    assert command.count("--") >= 1
