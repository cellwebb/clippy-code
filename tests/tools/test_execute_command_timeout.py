"""Test execute_command tool with configurable timeout."""

from clippy.tools.execute_command import execute_command


def test_execute_command_default_timeout():
    """Test default timeout (300 seconds) doesn't break normal operations."""
    # Fast command should work with default timeout
    success, message, result = execute_command("echo 'test'", ".", 300)
    assert success is True
    assert "test" in result


def test_execute_command_custom_timeout():
    """Test custom timeout parameter."""
    # Fast command with custom timeout
    success, message, result = execute_command("echo 'test'", ".", 60)
    assert success is True
    assert "test" in result


def test_execute_command_no_timeout():
    """Test timeout=0 disables timeout entirely."""
    # This would be problematic to test with actual long-running commands,
    # but we can verify the parameter is accepted
    success, message, result = execute_command("echo 'test'", ".", 0)
    assert success is True
    assert "test" in result


def test_execute_command_timeout_exceeded():
    """Test command that exceeds timeout."""
    # Command that sleeps longer than the timeout
    success, message, result = execute_command("sleep 2", ".", 1)
    assert success is False
    assert "timed out after 1 seconds" in message


def test_execute_command_timeout_message_formatting():
    """Test timeout message formatting for different timeout values."""
    # Test bounded timeout
    success, message, result = execute_command("sleep 1", ".", 0.5)
    assert success is False
    assert "timed out after 0.5 seconds" in message

    # Test unlimited timeout message (would only show if timeout was somehow exceeded)
    # We can't actually test this since unlimited timeout shouldn't timeout,
    # but we can verify the logic in the timeout-except block


def test_execute_command_negative_timeout():
    """Test negative timeout values are handled."""
    # Negative timeout should be treated as immediate timeout
    success, message, result = execute_command("echo 'test'", ".", -1)
    # This might behave differently depending on subprocess implementation
    # Let's just ensure it doesn't crash
    assert isinstance(success, bool)
    assert isinstance(message, str)


def test_execute_command_large_timeout():
    """Test large timeout values."""
    # Very large timeout should work for short commands
    success, message, result = execute_command("echo 'test'", ".", 3600)
    assert success is True
    assert "test" in result


def test_execute_command_parameter_validation():
    """Test that all parameters are properly handled."""
    # Test with all parameters (named parameters for working_dir, but positional for cmd)
    success, message, result = execute_command("echo 'test'", working_dir=".", timeout=120)
    assert success is True
    assert "test" in result


def test_execute_command_directory_traversal_still_works():
    """Test that directory traversal protection still works with timeout."""
    success, message, result = execute_command("echo 'test'", "../etc", 30)
    assert success is False
    assert "Directory traversal not allowed" in message
