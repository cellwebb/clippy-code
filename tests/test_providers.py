"""Tests for LLM providers."""

from __future__ import annotations

import sys
import time
import types
from types import SimpleNamespace
from typing import Any

import pytest

from clippy.providers import LLMProvider, Spinner


class TestSpinner:
    """Tests for Spinner class."""

    def test_spinner_initialization(self) -> None:
        """Test spinner initialization."""
        spinner = Spinner("Loading", enabled=True)

        assert spinner.message == "Loading"
        assert spinner.enabled is True
        assert spinner.running is False
        assert spinner.thread is None

    def test_spinner_disabled(self) -> None:
        """Test disabled spinner doesn't start."""
        spinner = Spinner("Loading", enabled=False)
        spinner.start()

        assert spinner.running is False
        assert spinner.thread is None

    def test_spinner_start_and_stop(self) -> None:
        """Test starting and stopping the spinner."""
        spinner = Spinner("Loading", enabled=True)
        spinner.start()

        assert spinner.running is True
        assert spinner.thread is not None
        assert spinner.thread.is_alive()

        # Give it a moment to run
        time.sleep(0.2)

        spinner.stop()

        assert spinner.running is False

    def test_spinner_does_not_start_twice(self) -> None:
        """Test that spinner doesn't start if already running."""
        spinner = Spinner("Loading", enabled=True)
        spinner.start()
        first_thread = spinner.thread

        # Try to start again
        spinner.start()

        # Should still be the same thread
        assert spinner.thread is first_thread

        spinner.stop()

    def test_spinner_custom_message(self) -> None:
        """Test spinner with custom message."""
        spinner = Spinner("Custom Message", enabled=True)
        assert spinner.message == "Custom Message"


class TestLLMProvider:
    """Tests for LLMProvider class."""

    @pytest.fixture(autouse=True)
    def _install_fake_openai(self, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
        """Install a minimal openai shim covering the provider's needs."""

        class FakeClient:
            def __init__(self, **kwargs: Any) -> None:
                self.kwargs = kwargs
                self.calls: list[dict[str, Any]] = []
                self.failures: list[Exception] = []
                self.next_stream: Any = []

                def _create(**create_kwargs: Any) -> Any:
                    self.calls.append(create_kwargs)
                    if self.failures:
                        raise self.failures.pop(0)
                    return self.next_stream

                self.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))

        fake_openai = types.ModuleType("openai")
        fake_openai.OpenAI = FakeClient

        # Define the exception hierarchy used in providers.py
        for name in [
            "APIConnectionError",
            "APITimeoutError",
            "AuthenticationError",
            "BadRequestError",
            "ConflictError",
            "InternalServerError",
            "NotFoundError",
            "PermissionDeniedError",
            "RateLimitError",
            "UnprocessableEntityError",
        ]:
            setattr(fake_openai, name, type(name, (Exception,), {}))

        monkeypatch.setitem(sys.modules, "openai", fake_openai)
        return fake_openai

    def test_provider_initialization_passes_kwargs(self) -> None:
        provider = LLMProvider(api_key="key", base_url="https://api.example.com", timeout=5)

        client = provider.client
        assert client.kwargs["api_key"] == "key"
        assert client.kwargs["base_url"] == "https://api.example.com"
        assert client.kwargs["timeout"] == 5

    def test_create_message_streaming_collects_content_and_tools(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        provider = LLMProvider(api_key="key")
        client = provider.client

        class DummySpinner:
            def __init__(self, message: str, enabled: bool) -> None:
                self.message = message
                self.enabled = enabled
                self.started = False
                self.stopped = False

            def start(self) -> None:
                self.started = True

            def stop(self) -> None:
                self.stopped = True

        monkeypatch.setattr("clippy.providers.Spinner", DummySpinner)
        monkeypatch.setattr("tenacity.nap.sleep", lambda seconds: None)

        tool_delta_initial = SimpleNamespace(
            index=0,
            id="call_0",
            type="function",
            function=SimpleNamespace(name="write_file", arguments='{"path": "a.txt"'),
        )
        tool_delta_append = SimpleNamespace(
            index=0,
            id=None,
            type=None,
            function=SimpleNamespace(name=None, arguments=', "content": "text"}'),
        )

        chunks = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            role="assistant",
                            content="Hello",
                            tool_calls=[tool_delta_initial],
                        ),
                        finish_reason=None,
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(
                            content=" world",
                            tool_calls=[tool_delta_append],
                        ),
                        finish_reason="stop",
                    )
                ]
            ),
        ]

        client.next_stream = chunks

        result = provider.create_message(messages=[{"role": "user", "content": "Hi"}], tools=[])

        captured = capsys.readouterr().out
        assert "Hello world" in captured

        assert result == {
            "role": "assistant",
            "content": "Hello world",
            "finish_reason": "stop",
            "tool_calls": [
                {
                    "id": "call_0",
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "arguments": '{"path": "a.txt", "content": "text"}',
                    },
                }
            ],
        }

        assert client.calls[0]["model"] == "gpt-5"
        assert client.calls[0]["stream"] is True

    def test_create_completion_retries_transient_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        provider = LLMProvider(api_key="key")
        client = provider.client

        monkeypatch.setattr("tenacity.nap.sleep", lambda seconds: None)

        fake_openai = sys.modules["openai"]
        client.failures = [fake_openai.RateLimitError("retry me")]
        sentinel_stream = ["chunk"]
        client.next_stream = sentinel_stream

        stream = provider._create_completion_with_retry(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
            tools=None,
            temperature=0.1,
        )

        assert stream is sentinel_stream
        assert len(client.calls) == 2

    def test_create_completion_surface_auth_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        provider = LLMProvider(api_key="key")
        client = provider.client

        monkeypatch.setattr("tenacity.nap.sleep", lambda seconds: None)

        fake_openai = sys.modules["openai"]
        client.failures = [fake_openai.AuthenticationError("bad key") for _ in range(3)]

        with pytest.raises(fake_openai.AuthenticationError):
            provider._create_completion_with_retry(
                model="gpt-4",
                messages=[],
                tools=None,
            )

        assert len(client.calls) == 3
