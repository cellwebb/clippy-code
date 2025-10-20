"""Tests for clippy.cli.setup utilities."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from clippy.cli.setup import _cleanup_old_logs, load_env, setup_logging


def test_cleanup_old_logs_keeps_newest(tmp_path: Path) -> None:
    log_dir = tmp_path
    created_files: list[Path] = []
    for i in range(5):
        file = log_dir / f"clippy-{i}.log"
        file.write_text(f"log {i}", encoding="utf-8")
        os.utime(file, (i, i))
        created_files.append(file)

    _cleanup_old_logs(log_dir, keep=2)

    remaining = sorted(log_dir.glob("clippy-*.log"))
    assert len(remaining) == 2
    assert {p.name for p in remaining} == {"clippy-4.log", "clippy-3.log"}


def test_load_env_prefers_project_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value", encoding="utf-8")

    loaded: list[Path] = []
    monkeypatch.setattr("clippy.cli.setup.load_dotenv", lambda path: loaded.append(Path(path)))

    load_env()

    assert len(loaded) == 1
    assert Path(loaded[0]).resolve() == env_file.resolve()


def test_load_env_falls_back_to_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    env_file = home_dir / ".clippy.env"
    env_file.write_text("KEY=value", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    loaded: list[Path] = []
    monkeypatch.setattr("clippy.cli.setup.load_dotenv", lambda path: loaded.append(Path(path)))

    load_env()

    assert len(loaded) == 1
    assert Path(loaded[0]).resolve() == env_file.resolve()


def test_setup_logging_creates_handlers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    new_handlers: list[logging.Handler] = []

    try:
        setup_logging(verbose=True)
        new_handlers = [
            handler for handler in root_logger.handlers if handler not in original_handlers
        ]

        assert len(new_handlers) == 2
        stream_handlers = [h for h in new_handlers if isinstance(h, logging.StreamHandler)]
        file_handlers = [h for h in new_handlers if isinstance(h, logging.FileHandler)]
        assert stream_handlers and file_handlers
        assert stream_handlers[0].level == logging.DEBUG

        log_dir = home_dir / ".clippy" / "logs"
        log_files = list(log_dir.glob("clippy-*.log"))
        assert len(log_files) == 1

        assert logging.getLogger("openai").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING
    finally:
        for handler in new_handlers:
            root_logger.removeHandler(handler)
            handler.close()
