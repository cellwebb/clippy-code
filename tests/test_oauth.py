"""Tests for Claude Code OAuth functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from clippy.oauth.claude_code import (
    CLAUDE_CODE_CONFIG,
    authenticate_and_save,
    exchange_code_for_tokens,
    load_stored_token,
    perform_oauth_flow,
    prepare_oauth_context,
    save_token,
)


def test_oauth_config() -> None:
    """Test that OAuth configuration has required fields."""
    required_fields = [
        "auth_url",
        "token_url",
        "api_base_url",
        "client_id",
        "scope",
        "redirect_host",
        "redirect_path",
        "callback_port_range",
        "callback_timeout",
        "anthropic_version",
    ]

    for field in required_fields:
        assert field in CLAUDE_CODE_CONFIG
        assert CLAUDE_CODE_CONFIG[field] is not None


def test_prepare_oauth_context() -> None:
    """Test OAuth context preparation."""
    context = prepare_oauth_context()

    assert context.state is not None
    assert len(context.state) > 20  # Should be a reasonable length
    assert context.code_verifier is not None
    assert context.code_challenge is not None
    assert context.created_at > 0
    assert context.redirect_uri is None  # Not assigned yet

    # Verify PKCE relationship
    import base64
    import hashlib

    # Re-encode code verifier to match code challenge format
    digest = hashlib.sha256(context.code_verifier.encode("utf-8")).digest()
    expected_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    assert context.code_challenge == expected_challenge


def test_token_storage_path() -> None:
    """Test token storage path generation."""
    from clippy.oauth.claude_code import get_token_storage_path

    path = get_token_storage_path()
    assert isinstance(path, Path)
    assert path.name == ".env"
    assert path.parent.name == ".clippy"


def test_load_stored_token_missing_file() -> None:
    """Test loading token when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the storage path to use temp directory
        with (
            patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path,
            patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": ""}, clear=True),
        ):
            mock_path.return_value = Path(tmpdir) / ".env"

            token = load_stored_token()
            assert token is None


def test_load_stored_token_empty_file() -> None:
    """Test loading token from empty .env file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        env_file.write_text("")

        with (
            patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path,
            patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": ""}, clear=True),
        ):
            mock_path.return_value = env_file

            token = load_stored_token()
            assert token is None


def test_load_stored_token_valid_token() -> None:
    """Test loading a valid token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        env_file.write_text("CLAUDE_CODE_ACCESS_TOKEN=test_token_123\nOTHER_VAR=value\n")

        with (
            patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path,
            patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": ""}, clear=True),
        ):
            mock_path.return_value = env_file

            token = load_stored_token()
            assert token == "test_token_123"


def test_save_token() -> None:
    """Test saving a token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"

        with patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path:
            mock_path.return_value = env_file

            result = save_token("test_token_456")
            assert result is True

            # Verify token was saved (dotenv might add quotes)
            content = env_file.read_text()
            assert "CLAUDE_CODE_ACCESS_TOKEN" in content and "test_token_456" in content

            # Verify environment variable was set
            assert os.getenv("CLAUDE_CODE_ACCESS_TOKEN") == "test_token_456"


def test_exchange_code_for_tokens() -> None:
    """Test token exchange with mock HTTP response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "oauth_token_789",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    context = prepare_oauth_context()
    context.redirect_uri = "http://localhost:8765/callback"

    with patch("httpx.post") as mock_post:
        mock_post.return_value = mock_response

        tokens = exchange_code_for_tokens("auth_code_123", context)

        assert tokens is not None
        assert tokens["access_token"] == "oauth_token_789"
        assert "expires_at" in tokens  # Should be added by our code

        # Verify HTTP call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[1]["json"]["grant_type"] == "authorization_code"
        assert call_args[1]["json"]["code"] == "auth_code_123"
        assert call_args[1]["json"]["client_id"] == CLAUDE_CODE_CONFIG["client_id"]
        assert "anthropic-beta" in call_args[1]["headers"]


def test_exchange_code_for_tokens_error() -> None:
    """Test token exchange with error response."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Invalid authorization code"

    context = prepare_oauth_context()
    context.redirect_uri = "http://localhost:8765/callback"

    with patch("httpx.post") as mock_post:
        mock_post.return_value = mock_response

        tokens = exchange_code_for_tokens("invalid_code", context)

        assert tokens is None


def test_authenticate_and_save_success() -> None:
    """Test full authentication flow success."""
    mock_tokens = {
        "access_token": "final_token_abc",
        "expires_in": 3600,
    }

    with (
        patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow,
        patch("clippy.oauth.claude_code.save_token") as mock_save,
    ):
        mock_flow.return_value = mock_tokens
        mock_save.return_value = True

        result = authenticate_and_save(quiet=True)

        assert result is True
        mock_flow.assert_called_once_with(quiet=True)
        mock_save.assert_called_once_with("final_token_abc")


def test_authenticate_and_save_failure() -> None:
    """Test authentication flow failure."""
    with patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow:
        mock_flow.return_value = None

        result = authenticate_and_save(quiet=True)

        assert result is False


def test_authenticate_and_save_no_token() -> None:
    """Test authentication when no token is returned."""
    mock_tokens = {"no_access_token": "value"}  # Missing access_token key

    with patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow:
        mock_flow.return_value = mock_tokens

        result = authenticate_and_save(quiet=True)

        assert result is False


def test_authenticate_and_save_save_failure() -> None:
    """Test authentication when token saving fails."""
    mock_tokens = {
        "access_token": "token_that_fails_to_save",
        "expires_in": 3600,
    }

    with (
        patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow,
        patch("clippy.oauth.claude_code.save_token") as mock_save,
    ):
        mock_flow.return_value = mock_tokens
        mock_save.return_value = False

        result = authenticate_and_save(quiet=True)

        assert result is False


def test_perform_oauth_flow_interrupted() -> None:
    """Test OAuth flow when user doesn't complete it."""
    # Mock the server startup and browser, but no callback occurs
    mock_server = Mock()
    mock_result = Mock()
    mock_result.code = None
    mock_result.state = None
    mock_result.error = None

    with patch("clippy.oauth.claude_code._start_callback_server") as mock_start:
        mock_start.return_value = (mock_server, mock_result, Mock())

        with patch("threading.Event") as mock_event_class:
            mock_event = Mock()
            mock_event_class.return_value = mock_event
            mock_event.wait.return_value = False  # Timeout

            with patch("clippy.oauth.claude_code._CallbackHandler"):
                with patch("webbrowser.open"):
                    result = perform_oauth_flow(quiet=True)

                    assert result is None


@patch("clippy.oauth.claude_code.webbrowser")
@patch("clippy.oauth.claude_code._start_callback_server")
def test_perform_oauth_flow_browser_error(mock_start_server, mock_browser):
    """Test OAuth flow handles browser opening errors gracefully."""
    mock_server = Mock()
    mock_result = Mock()
    mock_result.code = None
    mock_result.state = None
    mock_result.error = None

    mock_start_server.return_value = (mock_server, mock_result, Mock())
    mock_browser.open.side_effect = Exception("Browser failed")

    with patch("threading.Event") as mock_event_class:
        mock_event = Mock()
        mock_event_class.return_value = mock_event
        mock_event.wait.return_value = False  # Timeout

        with patch("clippy.oauth.claude_code._CallbackHandler"):
            result = perform_oauth_flow(quiet=True)

            # Should still work even if browser fails
            assert result is None  # Returns None due to timeout, not browser error


def test_claude_code_provider_configuration() -> None:
    """Test that Claude Code provider is correctly configured."""
    from clippy.models import get_provider

    provider = get_provider("claude-code")

    assert provider is not None
    assert provider.name == "claude-code"
    assert provider.base_url is None  # Uses default Anthropic URL
    assert provider.api_key_env == "CLAUDE_CODE_ACCESS_TOKEN"
    assert provider.description == "Claude Code (OAuth)"
    assert provider.pydantic_system == "anthropic"


def test_claude_code_oauth_in_providers_yaml() -> None:
    """Test that claude-code provider exists in providers.yaml."""
    import yaml

    yaml_path = Path(__file__).parent.parent / "src" / "clippy" / "providers.yaml"

    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    assert "claude-code" in config["providers"]

    provider = config["providers"]["claude-code"]
    assert provider["api_key_env"] == "CLAUDE_CODE_ACCESS_TOKEN"
    assert provider["description"] == "Claude Code (OAuth)"
    assert provider["pydantic_system"] == "anthropic"
    assert provider["base_url"] is None
