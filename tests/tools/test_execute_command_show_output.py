"""Tests for execute_command show_output functionality."""

import pytest

from clippy.tools.execute_command import execute_command


class TestExecuteCommandShowOutput:
    """Test the show_output parameter of execute_command."""

    def test_show_output_true_displays_output(self) -> None:
        """Test that output is displayed when show_output=True."""
        success, message, result = execute_command("echo 'Hello World'", show_output=True)

        assert success is True
        assert "Command executed successfully" in message
        assert "Hello World" in result
        assert "[Output hidden by setting]" not in result

    def test_show_output_false_hides_output(self) -> None:
        """Test that output is hidden when show_output=False."""
        success, message, result = execute_command("echo 'Hello World'", show_output=False)

        assert success is True
        assert "Command executed successfully" in message
        assert result == "[Output hidden by setting]"
        assert "Hello World" not in result

    def test_show_output_false_with_command_failure(self) -> None:
        """Test that output is hidden even when command fails."""
        success, message, result = execute_command("sh -c 'exit 1'", show_output=False)

        assert success is False
        assert "Command failed with return code 1" in message
        assert result == "[Output hidden by setting]"

    def test_show_output_false_with_stderr_output(self) -> None:
        """Test that stderr output is also hidden when show_output=False."""
        success, message, result = execute_command(
            "sh -c \"echo 'Error message' >&2; exit 1\"",
            show_output=False,
        )

        assert success is False
        assert "Command failed with return code 1" in message
        assert result == "[Output hidden by setting]"
        assert "Error message" not in result

    def test_show_output_default_parameter(self) -> None:
        """Test that the default parameter value works correctly (now defaults to False)."""
        success, message, result = execute_command("echo 'Default test'")

        assert success is True
        assert "Command executed successfully" in message
        assert result == "[Output hidden by setting]"
        assert "Default test" not in result

    def test_show_output_multiline_output(self) -> None:
        """Test show_output with multiline command output."""
        cmd = "echo 'Line 1'; echo 'Line 2'; echo 'Line 3'"

        # Test with show_output=True
        success, message, result = execute_command(cmd, show_output=True)
        assert success is True
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

        # Test with show_output=False
        success, message, result = execute_command(cmd, show_output=False)
        assert success is True
        assert result == "[Output hidden by setting]"

    def test_show_output_with_timeout(self) -> None:
        """Test that show_output works together with timeout parameter."""
        success, message, result = execute_command(
            "echo 'Timeout test'", timeout=30, show_output=False
        )

        assert success is True
        assert result == "[Output hidden by setting]"
        assert "Timeout test" not in result

    def test_show_output_with_working_dir(self) -> None:
        """Test that show_output works together with working_dir parameter."""
        success, message, result = execute_command(
            "echo 'Working dir test'", working_dir="/tmp", show_output=False
        )

        assert success is True
        assert result == "[Output hidden by setting]"
        assert "Working dir test" not in result


class TestEnvironmentVariableShowOutput:
    """Test the CLIPPY_SHOW_COMMAND_OUTPUT environment variable."""

    def test_environment_variable_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variable is respected when set to true."""
        monkeypatch.setenv("CLIPPY_SHOW_COMMAND_OUTPUT", "true")

        # Reload settings to pick up the environment variable
        import importlib

        import clippy.settings

        importlib.reload(clippy.settings)

        settings = clippy.settings.get_settings()
        assert settings.show_command_output is True

    def test_environment_variable_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variable is respected when set to false."""
        monkeypatch.setenv("CLIPPY_SHOW_COMMAND_OUTPUT", "false")

        # Reload settings to pick up the environment variable
        import importlib

        import clippy.settings

        importlib.reload(clippy.settings)

        settings = clippy.settings.get_settings()
        assert settings.show_command_output is False

    def test_environment_various_true_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test various values that should be interpreted as true."""
        true_values = ["true", "1", "yes", "on", "enable", "TRUE", "Yes"]

        for value in true_values:
            monkeypatch.setenv("CLIPPY_SHOW_COMMAND_OUTPUT", value)

            # Reload settings to pick up the environment variable
            import importlib

            import clippy.settings

            importlib.reload(clippy.settings)

            settings = clippy.settings.get_settings()
            assert settings.show_command_output is True, f"Value '{value}' should be True"

    def test_environment_various_false_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test various values that should be interpreted as false."""
        false_values = ["false", "0", "no", "off", "disable", "FALSE", "No"]

        for value in false_values:
            monkeypatch.setenv("CLIPPY_SHOW_COMMAND_OUTPUT", value)

            # Reload settings to pick up the environment variable
            import importlib

            import clippy.settings

            importlib.reload(clippy.settings)

            settings = clippy.settings.get_settings()
            assert settings.show_command_output is False, f"Value '{value}' should be False"

    def test_environment_variable_invalid_defaults_to_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that invalid environment variable values default to false."""
        invalid_values = ["invalid", "maybe", "2", "-1", ""]

        for value in invalid_values:
            monkeypatch.setenv("CLIPPY_SHOW_COMMAND_OUTPUT", value)

            # Reload settings to pick up the environment variable
            import importlib

            import clippy.settings

            importlib.reload(clippy.settings)

            settings = clippy.settings.get_settings()
            assert settings.show_command_output is False, f"Value '{value}' should default to False"

    def test_environment_variable_unset_defaults_to_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that unset environment variable defaults to false."""
        monkeypatch.delenv("CLIPPY_SHOW_COMMAND_OUTPUT", raising=False)

        # Reload settings to pick up the environment variable
        import importlib

        import clippy.settings

        importlib.reload(clippy.settings)

        settings = clippy.settings.get_settings()
        assert settings.show_command_output is False
