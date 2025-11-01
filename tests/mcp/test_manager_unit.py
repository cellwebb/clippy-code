"""Unit tests for clippy.mcp.manager.Manager (non-I/O paths)."""

from __future__ import annotations

import asyncio
import os
import time
from types import SimpleNamespace
from typing import Any

import pytest

from clippy.mcp.config import Config, ServerConfig
from clippy.mcp.manager import Manager


@pytest.fixture
def manager_factory(monkeypatch: pytest.MonkeyPatch):
    """Create managers without spinning up real event loop threads."""

    def factory(config: Config | None = None) -> Manager:
        def fake_start_loop(self: Manager) -> None:  # pragma: no cover - helper
            self._loop_started.set()
            self._loop = SimpleNamespace(call_soon_threadsafe=lambda fn: fn(), stop=lambda: None)
            self._loop_thread = SimpleNamespace(join=lambda timeout: None)

        monkeypatch.setattr("clippy.mcp.manager.Manager._start_event_loop", fake_start_loop)
        return Manager(config=config or Config(mcp_servers={}), console=None)

    return factory


def test_manager_start_stop_wraps_coroutines(manager_factory, monkeypatch):
    manager = manager_factory()

    seen: list[str] = []

    def capture(coro: Any) -> None:
        seen.append(coro.cr_code.co_name)
        coro.close()

    monkeypatch.setattr(manager, "_run_in_loop", capture)

    manager.start()
    assert seen == ["_async_start"]

    manager.stop()
    assert seen == ["_async_start", "_async_stop"]


def test_manager_list_servers_and_tools(manager_factory):
    server_config = Config(
        mcp_servers={
            "alpha": ServerConfig(command="cmd", args=[], env=None, cwd=None),
            "beta": ServerConfig(command="cmd", args=[], env=None, cwd=None),
        }
    )
    manager = manager_factory(server_config)
    manager._sessions["alpha"] = object()
    manager._tools["alpha"] = [SimpleNamespace(name="tool", description="desc")]

    servers = manager.list_servers()
    assert servers == [
        {"server_id": "alpha", "connected": True, "enabled": True, "tools_count": 1},
        {"server_id": "beta", "connected": False, "enabled": True, "tools_count": 0},
    ]

    tools_all = manager.list_tools()
    assert tools_all == [{"server_id": "alpha", "name": "tool", "description": "desc"}]
    tools_alpha = manager.list_tools("alpha")
    assert tools_alpha == tools_all
    assert manager.list_tools("missing") == []


def test_manager_get_all_tools_openai_handles_mapping(manager_factory, monkeypatch):
    manager = manager_factory()
    tool = SimpleNamespace(name="alpha", description="desc")
    manager._tools["server"] = [tool, tool]

    monkeypatch.setattr(
        "clippy.mcp.manager.map_mcp_to_openai",
        lambda tool, server_id: {"server": server_id, "name": tool.name},
    )

    openai_tools = manager.get_all_tools_openai()
    assert openai_tools == [{"server": "server", "name": "alpha"}] * 2

    def raise_mapping(tool, server_id):
        raise RuntimeError("bad tool")

    monkeypatch.setattr("clippy.mcp.manager.map_mcp_to_openai", raise_mapping)
    manager._tools["server"] = [tool]

    openai_tools = manager.get_all_tools_openai()
    assert openai_tools == []


def test_manager_execute_success_and_errors(manager_factory, monkeypatch):
    config = Config(mcp_servers={"alpha": ServerConfig(command="cmd", args=[], env=None, cwd=None)})
    manager = manager_factory(config)

    # not connected
    success, message, result = manager.execute("alpha", "tool", {})
    assert success is False and "Not connected" in message

    # connect and trust
    class StubSession:
        async def call_tool(self, name: str, args: dict[str, Any]) -> Any:
            return {"name": name, "args": args}

    manager._sessions["alpha"] = StubSession()
    manager.set_trusted("alpha", True)

    def run_immediate(coro: Any):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    monkeypatch.setattr(manager, "_run_in_loop", run_immediate)

    success, message, result = manager.execute("alpha", "tool", {"arg": 1})
    assert success is True
    assert "Successfully executed" in message
    assert result["args"] == {"arg": 1}

    # trust check failure
    manager.set_trusted("alpha", False)
    success, message, _ = manager.execute("alpha", "tool", {})
    assert success is False and "not trusted" in message.lower()

    # unexpected exception path
    class FailingSession:
        async def call_tool(self, name: str, args: dict[str, Any]) -> Any:
            raise RuntimeError("boom")

    manager._sessions["alpha"] = FailingSession()
    manager.set_trusted("alpha", True)
    success, message, result = manager.execute("alpha", "tool", {})
    assert success is False and "Error executing" in message
    assert result is None

    # server not configured
    success, message, _ = manager.execute("missing", "tool", {})
    assert success is False and "not configured" in message.lower()


def test_manager_run_in_loop_requires_loop(manager_factory):
    manager = manager_factory()
    manager._loop = None

    async def sample() -> None:
        pass

    coro = sample()
    try:
        with pytest.raises(RuntimeError):
            manager._run_in_loop(coro)
    finally:
        coro.close()


def test_manager_start_stderr_logger(manager_factory):
    manager = manager_factory()
    read_fd, write_fd = os.pipe()
    try:
        manager._start_stderr_logger("server", read_fd)
        os.write(write_fd, b"line\n")
        os.close(write_fd)
        time.sleep(0.05)
        manager._stderr_stop_events["server"].set()
        manager._stderr_threads["server"].join(timeout=1.0)
        assert "server" in manager._stderr_threads
    finally:
        if write_fd:
            try:
                os.close(write_fd)
            except OSError:
                pass
