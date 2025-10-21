"""Tests for running clippy as a module."""

import runpy


def test_clippy_module_entrypoint(monkeypatch):
    called = []
    monkeypatch.setattr("clippy.cli.main", lambda: called.append(True))

    runpy.run_module("clippy", run_name="__main__")

    assert called == [True]
