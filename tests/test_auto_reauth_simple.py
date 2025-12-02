"""Simplified tests for automatic re-authentication functionality."""

import time
from unittest.mock import patch

from clippy.oauth.claude_code import (
    ensure_valid_token,
    is_token_expired,
    load_stored_token,
    save_token,
)


class TestClaudeCodeAutoReauthSimple:
    """Simplified test suite for Claude Code automatic re-authentication."""

    def test_is_token_expired_with_valid_token(self):
        """Test token expiry detection with valid token."""
        with patch("clippy.oauth.claude_code.load_stored_token") as mock_load:
            # Mock a valid token
            mock_load.return_value = "valid_token"

            assert not is_token_expired()

    def test_is_token_expired_with_expired_token(self):
        """Test token expiry detection with expired token."""
        with patch("clippy.oauth.claude_code.load_stored_token") as mock_load:
            # Mock no valid token (expired case)
            mock_load.return_value = None

            assert is_token_expired()

    def test_ensure_valid_token_with_existing_valid_token(self):
        """Test ensure_valid_token when valid token already exists."""
        with patch("clippy.oauth.claude_code.load_stored_token") as mock_load:
            # Mock a valid token
            mock_load.return_value = "valid_token"

            assert ensure_valid_token()
            mock_load.assert_called_once_with(check_expiry=True)

    def test_ensure_valid_token_with_expired_token_success(self):
        """Test ensure_valid_token when token is expired and re-auth succeeds."""
        with (
            patch("clippy.oauth.claude_code.load_stored_token") as mock_load,
            patch("clippy.oauth.claude_code.authenticate_and_save") as mock_auth,
        ):
            # Mock no valid token (expired case)
            mock_load.return_value = None
            mock_auth.return_value = True

            assert ensure_valid_token()
            mock_auth.assert_called_once_with(quiet=False)

    def test_ensure_valid_token_with_expired_token_failure(self):
        """Test ensure_valid_token when token is expired and re-auth fails."""
        with (
            patch("clippy.oauth.claude_code.load_stored_token") as mock_load,
            patch("clippy.oauth.claude_code.authenticate_and_save") as mock_auth,
        ):
            # Mock no valid token (expired case)
            mock_load.return_value = None
            mock_auth.return_value = False

            assert not ensure_valid_token()
            mock_auth.assert_called_once_with(quiet=False)

    def test_ensure_valid_token_force_reauth(self):
        """Test ensure_valid_token with force_reauth=True."""
        with patch("clippy.oauth.claude_code.authenticate_and_save") as mock_auth:
            mock_auth.return_value = True

            assert ensure_valid_token(force_reauth=True)
            mock_auth.assert_called_once_with(quiet=False)

    def test_auth_error_detection(self):
        """Test that authentication errors are properly detected."""
        from clippy.providers import ClaudeCodeOAuthProvider

        provider = ClaudeCodeOAuthProvider(api_key="test_token")

        # Test various error types (lowercase to match implementation)
        auth_errors = [
            Exception("401 unauthorized"),
            Exception("403 forbidden"),
            Exception("authentication failed"),
            Exception("invalid token"),
            Exception("expired"),
            Exception("token"),
        ]

        for error in auth_errors:
            assert provider._is_auth_error(error)

        # Test non-auth errors
        non_auth_errors = [
            Exception("Rate limit exceeded"),
            Exception("Server error"),
            Exception("Bad request"),
        ]

        for error in non_auth_errors:
            assert not provider._is_auth_error(error)

    def test_token_loading_with_expiry_check_valid(self):
        """Test token loading with expiry validation for valid token."""

        with (
            patch("os.getenv", return_value=None),
            patch("dotenv.dotenv_values") as mock_dotenv,
            patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path,
            patch("time.time") as mock_time,
        ):
            # Setup mock data
            mock_path.return_value.exists.return_value = True
            current_time = 1000000.0
            expires_at = current_time + 300  # 5 minutes from now
            mock_time.return_value = current_time

            mock_dotenv.return_value = {
                "CLAUDE_CODE_ACCESS_TOKEN": "test_token",
                "CLAUDE_CODE_EXPIRES_AT": str(expires_at),
            }

            # Should return valid token (not expired yet, and within 5-minute buffer)
            token = load_stored_token(check_expiry=True)
            assert token == "test_token"

    def test_token_loading_with_expiry_check_expired(self):
        """Test token loading with expiry validation for expired token."""

        with (
            patch("os.getenv", return_value=None),
            patch("dotenv.dotenv_values") as mock_dotenv,
            patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path,
            patch("time.time") as mock_time,
        ):
            # Setup mock data
            mock_path.return_value.exists.return_value = True
            current_time = 1000000.0
            expires_at = current_time + 300  # 5 minutes from now
            mock_time.return_value = expires_at + 1  # Just past expiry

            mock_dotenv.return_value = {
                "CLAUDE_CODE_ACCESS_TOKEN": "test_token",
                "CLAUDE_CODE_EXPIRES_AT": str(expires_at),
            }

            # Should return None for expired token
            token = load_stored_token(check_expiry=True)
            assert token is None

    def test_token_saving_with_expiry(self):
        """Test that tokens are saved with expiry information."""
        with (
            patch("dotenv.set_key") as mock_set_key,
            patch("os.environ", {}) as mock_environ,
            patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path,
        ):
            mock_path.return_value.mkdir.return_value = None
            mock_path.return_value.__str__ = lambda x: "test_path"

            expires_at = time.time() + 3600
            result = save_token("test_token", expires_at)

            assert result is True
            mock_set_key.assert_any_call("test_path", "CLAUDE_CODE_ACCESS_TOKEN", "test_token")
            mock_set_key.assert_any_call("test_path", "CLAUDE_CODE_EXPIRES_AT", str(expires_at))
            assert mock_environ["CLAUDE_CODE_ACCESS_TOKEN"] == "test_token"


def test_ensure_valid_token_integration():
    """Integration test for ensure_valid_token function."""
    with (
        patch("clippy.oauth.claude_code.load_stored_token") as mock_load,
        patch("clippy.oauth.claude_code.authenticate_and_save") as mock_auth,
    ):
        # Test case 1: Valid token exists
        mock_load.return_value = "valid_token"
        assert ensure_valid_token()
        mock_auth.assert_not_called()

        # Reset mocks
        mock_load.reset_mock()
        mock_auth.reset_mock()

        # Test case 2: No valid token, auth succeeds
        mock_load.return_value = None
        mock_auth.return_value = True
        assert ensure_valid_token()
        mock_auth.assert_called_once_with(quiet=False)

        # Reset mocks
        mock_load.reset_mock()
        mock_auth.reset_mock()

        # Test case 3: No valid token, auth fails
        mock_load.return_value = None
        mock_auth.return_value = False
        assert not ensure_valid_token()
        mock_auth.assert_called_once_with(quiet=False)
