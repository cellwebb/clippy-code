"""Tests for MCP configuration loading and utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clippy.mcp import config


def test_resolve_env_variables_nested(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.delenv("MISSING", raising=False)

    data = {
        "servers": [
            {"command": "${API_KEY}"},
            ["${MISSING}", 42],
        ],
        "count": 5,
    }

    resolved = config._resolve_env_variables(data)
    assert resolved["servers"][0]["command"] == "secret"
    assert resolved["servers"][1][0] == "${MISSING}"
    assert resolved["count"] == 5


def test_load_config_explicit_bad_json(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.json"
    cfg.write_text("{bad json}")

    with pytest.raises(json.JSONDecodeError):
        config.load_config(str(cfg))


def test_load_config_prefers_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    home_config_dir = home / ".clippy"
    project_config_dir = project / ".clippy"
    home_config_dir.mkdir()
    project_config_dir.mkdir()

    (project_config_dir / "mcp.json").write_text(
        json.dumps({"mcp_servers": {"project": {"command": "proj", "args": []}}})
    )

    (home_config_dir / "mcp.json").write_text(
        json.dumps({"mcp_servers": {"home": {"command": "home", "args": []}}})
    )

    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.chdir(project)

    cfg = config.load_config()
    assert cfg is not None
    assert "home" in cfg.mcp_servers
