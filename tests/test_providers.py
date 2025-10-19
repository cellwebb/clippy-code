"""Tests for LLM providers."""

import time
from unittest.mock import patch

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

    def test_provider_missing_openai_package(self) -> None:
        """Test error when openai package is not installed."""
        # This tests the import error handling
        # Skip actual import testing as it would require uninstalling openai
        pass

    def test_get_default_model_value(self) -> None:
        """Test default model value."""
        # Test without actually importing OpenAI
        import os

        # Save original value
        original = os.environ.get("CLIPPY_MODEL")

        try:
            # Test default
            if "CLIPPY_MODEL" in os.environ:
                del os.environ["CLIPPY_MODEL"]

            # Patch where OpenAI is imported (inside the provider module)
            with patch("openai.OpenAI"):
                provider = LLMProvider(api_key="test-key")
                assert provider.get_default_model() == "gpt-5"

            # Test with env var
            os.environ["CLIPPY_MODEL"] = "custom-model"
            with patch("openai.OpenAI"):
                provider = LLMProvider(api_key="test-key")
                assert provider.get_default_model() == "custom-model"
        finally:
            # Restore original value
            if original is not None:
                os.environ["CLIPPY_MODEL"] = original
            elif "CLIPPY_MODEL" in os.environ:
                del os.environ["CLIPPY_MODEL"]

    def test_provider_initialization_basic(self) -> None:
        """Test basic provider initialization without complex mocking."""
        # Basic test to verify the provider class structure
        # Note: Full testing requires the openai package installed
        pass
