"""Tests for the /truncate command functionality."""

from unittest.mock import Mock

from rich.console import Console

from clippy.cli.commands import handle_truncate_command


def test_truncate_command_with_count() -> None:
    """Test that /truncate command correctly truncates conversation history."""
    # Create a mock agent with conversation history
    agent = Mock()
    agent.conversation_history = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
        {"role": "user", "content": "Second message"},
        {"role": "assistant", "content": "Second response"},
        {"role": "user", "content": "Third message"},
        {"role": "assistant", "content": "Third response"},
    ]

    # Create a console mock
    console = Console(force_terminal=False)

    # Call the truncate command with count of 2
    result = handle_truncate_command(agent, console, "2")

    # Verify the result
    assert result == "continue"

    # Verify that the conversation history was truncated correctly
    # Should keep system message + last 2 messages
    assert len(agent.conversation_history) == 3  # system + 2 last messages
    assert agent.conversation_history[0]["role"] == "system"
    assert agent.conversation_history[1]["content"] == "Third message"
    assert agent.conversation_history[2]["content"] == "Third response"


def test_truncate_command_with_zero_count() -> None:
    """Test that /truncate command with 0 keeps only system message."""
    # Create a mock agent with conversation history
    agent = Mock()
    agent.conversation_history = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
    ]

    # Create a console mock
    console = Console(force_terminal=False)

    # Call the truncate command with count of 0
    result = handle_truncate_command(agent, console, "0")

    # Verify the result
    assert result == "continue"

    # Verify that only the system message remains
    assert len(agent.conversation_history) == 1
    assert agent.conversation_history[0]["role"] == "system"


def test_truncate_command_with_empty_history() -> None:
    """Test that /truncate command handles empty conversation history."""
    # Create a mock agent with empty conversation history
    agent = Mock()
    agent.conversation_history = []

    # Create a console mock
    console = Console(force_terminal=False)

    # Call the truncate command
    result = handle_truncate_command(agent, console, "2")

    # Verify the result
    assert result == "continue"


def test_truncate_command_without_system_message() -> None:
    """Test that /truncate command works when there's no system message."""
    # Create a mock agent with conversation history but no system message
    agent = Mock()
    agent.conversation_history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
        {"role": "user", "content": "Second message"},
        {"role": "assistant", "content": "Second response"},
    ]

    # Create a console mock
    console = Console(force_terminal=False)

    # Call the truncate command with count of 1
    result = handle_truncate_command(agent, console, "1")

    # Verify the result
    assert result == "continue"

    # Verify that only the last message remains
    assert len(agent.conversation_history) == 1
    assert agent.conversation_history[0]["content"] == "Second response"


def test_truncate_command_invalid_count() -> None:
    """Test that /truncate command handles invalid count parameters."""
    # Create a mock agent
    agent = Mock()
    agent.conversation_history = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "First message"},
    ]

    # Create a console mock
    console = Console(force_terminal=False)

    # Test with non-integer count
    result = handle_truncate_command(agent, console, "abc")
    assert result == "continue"

    # Test with negative count
    result = handle_truncate_command(agent, console, "-1")
    assert result == "continue"


def test_truncate_command_no_arguments() -> None:
    """Test that /truncate command shows usage when no arguments provided."""
    # Create a mock agent
    agent = Mock()
    agent.conversation_history = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "First message"},
    ]

    # Create a console mock
    console = Console(force_terminal=False)

    # Call truncate without arguments
    result = handle_truncate_command(agent, console, "")

    # Should show usage and continue
    assert result == "continue"
