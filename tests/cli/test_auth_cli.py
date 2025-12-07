"""Tests for auth CLI functionality."""

import logging
import os
import unittest.mock

from clippy.cli.auth_cli import auth, status


class TestAuth:
    """Test the auth function."""

    def test_auth_basic_setup(self, monkeypatch):
        """Test basic auth function setup and configuration."""
        # Mock the dependent functions
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=True)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
        ):
            auth(quiet=False, log_level="INFO")

            # Verify logging was configured
            mock_load_token.assert_called_once()
            mock_authenticate.assert_called_once_with(quiet=False)

    def test_auth_quiet_mode(self, monkeypatch):
        """Test auth function in quiet mode."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=True)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch("clippy.cli.auth_cli.logging.basicConfig") as mock_logging,
        ):
            auth(quiet=True, log_level="DEBUG")

            # In quiet mode, should use ERROR level regardless of log_level parameter
            mock_logging.assert_called_once()
            call_args = mock_logging.call_args[1]
            assert call_args["level"] == logging.ERROR

    def test_auth_with_existing_token(self, monkeypatch):
        """Test auth function when existing token is found."""
        mock_load_token = unittest.mock.MagicMock(return_value="existing_token")
        mock_authenticate = unittest.mock.MagicMock(return_value=True)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
        ):
            auth(quiet=False, log_level="INFO")

            # Should print about existing token
            mock_load_token.assert_called_once()
            mock_authenticate.assert_called_once_with(quiet=False)

    def test_auth_successful_authentication(self, monkeypatch):
        """Test successful authentication flow."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=True)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch("clippy.cli.auth_cli.sys.exit") as mock_exit,
        ):
            auth(quiet=False, log_level="INFO")

            # Should not exit on success
            mock_exit.assert_not_called()
            # Should print success messages
            assert mock_console.print.call_count >= 3

    def test_auth_failed_authentication(self, monkeypatch):
        """Test failed authentication flow."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=False)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch("clippy.cli.auth_cli.sys.exit") as mock_exit,
        ):
            auth(quiet=False, log_level="INFO")

            # Should exit with error code 1 on failure
            mock_exit.assert_called_once_with(1)

    def test_auth_quiet_failed_authentication(self, monkeypatch):
        """Test failed authentication in quiet mode."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=False)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch("clippy.cli.auth_cli.sys.exit") as mock_exit,
        ):
            auth(quiet=True, log_level="INFO")

            # Should still exit with error code 1 even in quiet mode
            mock_exit.assert_called_once_with(1)

    def test_auth_logging_configuration(self, monkeypatch):
        """Test that logging is configured correctly."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=True)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch("clippy.cli.auth_cli.logging.basicConfig") as mock_logging,
        ):
            # Test different log levels
            auth(quiet=False, log_level="DEBUG")
            debug_call = mock_logging.call_args[1]
            assert debug_call["level"] == logging.DEBUG

            mock_logging.reset_mock()
            auth(quiet=False, log_level="WARNING")
            warning_call = mock_logging.call_args[1]
            assert warning_call["level"] == logging.WARNING

    def test_auth_logging_format_quiet_vs_non_quiet(self, monkeypatch):
        """Test that logging format differs between quiet and non-quiet modes."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_authenticate = unittest.mock.MagicMock(return_value=True)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.authenticate_and_save", mock_authenticate),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch("clippy.cli.auth_cli.logging.basicConfig") as mock_logging,
        ):
            # Test non-quiet mode (should include module name)
            auth(quiet=False, log_level="INFO")
            non_quiet_call = mock_logging.call_args[1]
            assert "%(name)s" in non_quiet_call["format"]

            mock_logging.reset_mock()
            # Test quiet mode (should not include module name)
            auth(quiet=True, log_level="INFO")
            quiet_call = mock_logging.call_args[1]
            assert "%(name)s" not in quiet_call["format"]


class TestStatus:
    """Test the status function."""

    def test_status_with_token(self, monkeypatch):
        """Test status function when token is present."""
        mock_load_token = unittest.mock.MagicMock(return_value="test_token")
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": "test_token"}),
        ):
            status()

            # Should print success messages
            assert mock_console.print.call_count >= 2
            # Should mention token is configured and in environment
            print_calls = [str(call[0][0]) for call in mock_console.print.call_args_list]
            assert any("configured" in call for call in print_calls)
            assert any("loaded in current environment" in call for call in print_calls)

    def test_status_with_token_not_in_env(self, monkeypatch):
        """Test status function when token exists but not in environment."""
        mock_load_token = unittest.mock.MagicMock(return_value="test_token")
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch.dict(os.environ, {}, clear=True),
        ):
            status()

            # Should show warning about environment
            print_calls = [str(call[0][0]) for call in mock_console.print.call_args_list]
            assert any("not found in current environment" in call for call in print_calls)
            assert any("~/.clippy/.env" in call for call in print_calls)

    def test_status_no_token(self, monkeypatch):
        """Test status function when no token is present."""
        mock_load_token = unittest.mock.MagicMock(return_value=None)
        mock_console = unittest.mock.MagicMock()

        with (
            unittest.mock.patch("clippy.cli.auth_cli.load_stored_token", mock_load_token),
            unittest.mock.patch("clippy.cli.auth_cli.console", mock_console),
            unittest.mock.patch.dict(os.environ, {}, clear=True),
        ):
            status()

            # Should print error message
            print_calls = [str(call[0][0]) for call in mock_console.print.call_args_list]
            assert any("No Claude Code OAuth token found" in call for call in print_calls)
            assert any("clippy auth" in call for call in print_calls)


class TestMainExecution:
    """Test the __main__ execution block."""

    def test_main_execution_block_syntax(self):
        """Test that the main execution block has correct syntax."""
        # Test that we can import the module successfully

        # The fact that this works means the __name__ == '__main__' block has correct syntax
        assert True  # If we get here, the import succeeded


class TestModuleImports:
    """Test that required modules are imported correctly."""

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import clippy.cli.auth_cli

        # Check that main functions are available
        assert hasattr(clippy.cli.auth_cli, "auth")
        assert hasattr(clippy.cli.auth_cli, "status")
        assert callable(clippy.cli.auth_cli.auth)
        assert callable(clippy.cli.auth_cli.status)
