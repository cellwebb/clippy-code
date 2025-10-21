"""Tests for utilities in clippy.agent.utils."""

from __future__ import annotations

import builtins
import importlib
from pathlib import Path

import pytest

from clippy.agent import utils
from clippy.agent.utils import _detect_mcp_file_operations, _generate_mcp_diff_summary


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    """Return a temporary file path populated with sample content."""
    file_path = tmp_path / "example.txt"
    file_path.write_text("first line\nsecond line\n", encoding="utf-8")
    return file_path


def test_generate_preview_diff_write_existing_file(tmp_file: Path) -> None:
    diff = utils.generate_preview_diff(
        "write_file", {"path": str(tmp_file), "content": "first line\nupdated\n"}
    )

    assert diff is not None
    assert "-second line" in diff
    assert "+updated" in diff


def test_generate_preview_diff_write_new_file(tmp_path: Path) -> None:
    new_file = tmp_path / "new.txt"

    diff = utils.generate_preview_diff(
        "write_file", {"path": str(new_file), "content": "brand new\n"}
    )

    assert diff is not None
    assert "+brand new" in diff


def test_generate_preview_diff_handles_read_error(
    tmp_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_open = builtins.open

    def _boom(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if str(path) == str(tmp_file):
            raise OSError("read failure")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _boom)

    diff = utils.generate_preview_diff(
        "write_file", {"path": str(tmp_file), "content": "replacement\n"}
    )

    assert diff is not None
    assert "[Could not read existing file content]" in diff
    assert "+replacement" in diff


def test_generate_preview_diff_edit_file(tmp_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    edit_file_module = importlib.import_module("clippy.tools.edit_file")

    def _fake_apply(
        old_content: str,
        operation: str,
        content: str,
        pattern: str,
        inherit_indent: bool,
        start_pattern: str,
        end_pattern: str,
    ) -> tuple[bool, str, str]:
        return True, "", old_content.replace("second line", "edited")

    monkeypatch.setattr(edit_file_module, "apply_edit_operation", _fake_apply)

    diff = utils.generate_preview_diff(
        "edit_file",
        {
            "path": str(tmp_file),
            "operation": "replace",
            "content": "edited",
            "pattern": "second line",
        },
    )

    assert diff is not None
    assert "-second line" in diff
    assert "+edited" in diff


def test_generate_preview_diff_edit_missing_file_returns_none(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"

    diff = utils.generate_preview_diff(
        "edit_file",
        {
            "path": str(missing),
            "operation": "insert",
            "content": "data",
            "pattern": "unused",
        },
    )

    assert diff is None


def test_generate_preview_diff_edit_apply_failure_returns_none(
    tmp_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    edit_file_module = importlib.import_module("clippy.tools.edit_file")

    def _raise_apply(*args, **kwargs):
        raise RuntimeError("nope")

    monkeypatch.setattr(edit_file_module, "apply_edit_operation", _raise_apply)

    diff = utils.generate_preview_diff(
        "edit_file",
        {
            "path": str(tmp_file),
            "operation": "replace",
            "content": "irrelevant",
            "pattern": "second",
        },
    )

    assert diff is None


def test_generate_preview_diff_mcp_summary(tmp_path: Path) -> None:
    target = tmp_path / "doc.txt"
    target.write_text("origin\n", encoding="utf-8")

    summary = utils.generate_preview_diff(
        "mcp__write_text", {"targetPath": str(target), "content": "origin\nupdated\n"}
    )

    assert summary is not None
    assert "MCP Tool File Operation Summary" in summary
    assert "Tool: mcp__write_text" in summary
    assert "Size change" in summary


def test_generate_preview_diff_mcp_without_path_returns_none() -> None:
    assert utils.generate_preview_diff("mcp__noop", {"value": "content"}) is None


def test_detect_mcp_file_operations_happy_path() -> None:
    result = _detect_mcp_file_operations({"filePath": "/tmp/file.txt", "text": "content"})
    assert result == {"path": "/tmp/file.txt", "content": "content"}


def test_detect_mcp_file_operations_missing_path() -> None:
    assert _detect_mcp_file_operations({"content": "value"}) == {}


def test_generate_mcp_diff_summary_new_file(tmp_path: Path) -> None:
    summary = _generate_mcp_diff_summary(
        "mcp__create", {"path": str(tmp_path / "fresh.txt"), "content": "hello"}, {}
    )

    assert "Existing file: None (new file)" in summary
    assert "Content preview" in summary


def test_generate_mcp_diff_summary_existing_file(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("old\n", encoding="utf-8")

    summary = _generate_mcp_diff_summary(
        "mcp__update", {"path": str(file_path), "content": "new\n"}, {}
    )

    assert "Existing file: 4 characters" in summary
    assert "Operation: Write/Update content" in summary
    assert "Tool: mcp__update" in summary


def test_generate_preview_diff_returns_empty_for_no_changes(tmp_file: Path) -> None:
    unchanged = tmp_file.read_text(encoding="utf-8")

    diff = utils.generate_preview_diff("write_file", {"path": str(tmp_file), "content": unchanged})

    assert diff == ""


def test_generate_preview_diff_handles_diff_exception(
    tmp_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*args, **kwargs):
        raise RuntimeError("diff failure")

    monkeypatch.setattr("clippy.agent.utils.generate_diff", _boom)

    diff = utils.generate_preview_diff(
        "write_file", {"path": str(tmp_file), "content": "alternate\n"}
    )

    assert diff is None
