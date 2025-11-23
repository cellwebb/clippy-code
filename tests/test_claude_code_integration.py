"""Integration tests for Claude Code OAuth functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from clippy.models import get_provider
from clippy.oauth.claude_code import (
    authenticate_and_save,
    load_stored_token,
    perform_oauth_flow,
    save_token,
)


def test_claude_code_provider_integration():
    """Test that Claude Code provider is properly integrated."""
    provider = get_provider("claude-code")
    
    assert provider is not None
    assert provider.name == "claude-code"
    assert provider.api_key_env == "CLAUDE_CODE_ACCESS_TOKEN"
    assert provider.description == "Claude Code (OAuth)"
    assert provider.pydantic_system == "anthropic"


def test_claude_code_oauth_end_to_end():
    """Test end-to-end OAuth flow with mocked components."""
    
    # Mock the complete OAuth flow
    mock_tokens = {
        "access_token": "test_oauth_token_12345",
        "expires_in": 3600,
        "token_type": "Bearer"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".clippy" / ".env"
        
        with patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow, \
             patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path:
            
            mock_path.return_value = env_file
            mock_flow.return_value = mock_tokens
            
            # Test authentication flow
            success = authenticate_and_save(quiet=True)
            assert success is True
            
            # Verify token was saved
            assert env_file.exists()
            content = env_file.read_text()
            assert "CLAUDE_CODE_ACCESS_TOKEN" in content
            assert "test_oauth_token_12345" in content
            
            # Test token loading
            token = load_stored_token()
            assert token == "test_oauth_token_12345"


def test_claude_code_oauth_token_refresh():
    """Test token refresh scenario."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".clippy" / ".env"
        env_file.parent.mkdir(exist_ok=True)
        
        with patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path:
            mock_path.return_value = env_file
            
            # Save initial token
            save_token("old_token_123")
            
            # Mock new tokens for refresh
            new_tokens = {
                "access_token": "new_refreshed_token_456",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
            
            with patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow:
                mock_flow.return_value = new_tokens
                
                # Authenticate again (simulating refresh)
                success = authenticate_and_save(quiet=True)
                assert success is True
                
                # Verify new token replaced old one
                token = load_stored_token()
                assert token == "new_refreshed_token_456"
                
                content = env_file.read_text()
                assert "old_token_123" not in content
                assert "new_refreshed_token_456" in content


def test_claude_code_oauth_error_handling():
    """Test error handling in OAuth flow."""
    
    with patch("clippy.oauth.claude_code.perform_oauth_flow") as mock_flow:
        # Test authentication failure
        mock_flow.return_value = None
        
        success = authenticate_and_save(quiet=True)
        assert success is False
        
        # Test authentication with missing token
        mock_tokens = {"no_access_token": "value"}
        mock_flow.return_value = mock_tokens
        
        success = authenticate_and_save(quiet=True)
        assert success is False


def test_claude_code_provider_can_be_used_in_model_config():
    """Test that Claude Code provider can be used in model configurations."""
    from clippy.models import get_model_config, UserModelManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temporary model manager
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)
        
        # Add a Claude Code model
        success, message = manager.add_model(
            name="claude-sonnet",
            provider="claude-code", 
            model_id="claude-sonnet-4-5",
            is_default=False
        )
        
        assert success is True
        assert "Added model" in message
        
        # Verify model was added
        model = manager.get_model("claude-sonnet")
        assert model is not None
        assert model.name == "claude-sonnet"
        assert model.provider == "claude-code"
        assert model.model_id == "claude-sonnet-4-5"
        assert model.description == "claude-code/claude-sonnet-4-5"


def test_claude_code_oauth_environment_variable():
    """Test that OAuth token can be loaded from environment variable."""
    import os
    
    # Save original environment
    original_token = os.environ.get("CLAUDE_CODE_ACCESS_TOKEN")
    
    try:
        # Set environment variable
        os.environ["CLAUDE_CODE_ACCESS_TOKEN"] = "env_test_token_789"
        
        token = load_stored_token()
        # Should return environment token even if file doesn't exist
        assert token == "env_test_token_789"
        
    finally:
        # Restore original environment
        if original_token is not None:
            os.environ["CLAUDE_CODE_ACCESS_TOKEN"] = original_token
        elif "CLAUDE_CODE_ACCESS_TOKEN" in os.environ:
            del os.environ["CLAUDE_CODE_ACCESS_TOKEN"]


def test_claude_code_oauth_file_and_env_priority():
    """Test priority between file and environment variable for OAuth token."""
    import os
    
    # Save original environment
    original_token = os.environ.get("CLAUDE_CODE_ACCESS_TOKEN")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".clippy" / ".env"
            
            with patch("clippy.oauth.claude_code.get_token_storage_path") as mock_path:
                mock_path.return_value = env_file
                
                # Save token to file
                save_token("file_stored_token")
                
                # Set different token in environment
                os.environ["CLAUDE_CODE_ACCESS_TOKEN"] = "env_stored_token"
                
                # Test which token takes precedence
                token = load_stored_token()
                # Environment should take precedence (highest priority)
                assert token == "env_stored_token"
                
    finally:
        # Restore original environment
        if original_token is not None:
            os.environ["CLAUDE_CODE_ACCESS_TOKEN"] = original_token
        elif "CLAUDE_CODE_ACCESS_TOKEN" in os.environ:
            del os.environ["CLAUDE_CODE_ACCESS_TOKEN"]


def test_claude_code_oauth_config_validation():
    """Test OAuth configuration validation."""
    from clippy.oauth.claude_code import CLAUDE_CODE_CONFIG
    
    # Validate required configuration fields
    required_fields = [
        "auth_url",
        "token_url",
        "client_id", 
        "scope",
        "callback_port_range",
        "callback_timeout",
    ]
    
    for field in required_fields:
        assert field in CLAUDE_CODE_CONFIG
        assert CLAUDE_CODE_CONFIG[field] is not None
    
    # Validate specific values
    assert CLAUDE_CODE_CONFIG["auth_url"].startswith("https://")
    assert CLAUDE_CODE_CONFIG["token_url"].startswith("https://")
    assert isinstance(CLAUDE_CODE_CONFIG["callback_port_range"], tuple)
    assert CLAUDE_CODE_CONFIG["callback_timeout"] > 0
    assert CLAUDE_CODE_CONFIG["scope"]  # Should not be empty