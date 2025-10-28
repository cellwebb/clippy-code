"""Tests for conversation persistence functionality."""

import json
from unittest.mock import patch

import pytest

from clippy.agent import ClippyAgent
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


@pytest.fixture
def mock_agent_with_persistence(tmp_path) -> ClippyAgent:
    """Create a ClippyAgent with mocked dependencies and temp directory for conversations."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
        base_url=None,
    )

    # Override conversations directory to use temporary path
    agent.conversations_dir = tmp_path / "conversations"
    agent.conversations_dir.mkdir(exist_ok=True, parents=True)

    return agent


def test_save_conversation_creates_directory(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test that save_conversation creates the conversations directory if it doesn't exist."""
    agent = mock_agent_with_persistence

    # Change to a new directory path that doesn't exist yet
    agent.conversations_dir = agent.conversations_dir.parent / "new_subdir" / "conversations"

    # Should succeed and create directory (with parents=True in save_conversation)
    success, message = agent.save_conversation("test-conversation")

    assert success is True
    assert "test-conversation" in message
    assert agent.conversations_dir.exists()


def test_save_conversation_creates_file(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test that save_conversation creates a JSON file with correct structure."""
    agent = mock_agent_with_persistence

    # Add some conversation history
    agent.conversation_history = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    success, message = agent.save_conversation("test-save")

    assert success is True
    assert "test-save" in message

    # Check that file was created
    conversation_file = agent.conversations_dir / "test-save.json"
    assert conversation_file.exists()

    # Check file content
    with open(conversation_file) as f:
        data = json.load(f)

    assert "model" in data
    assert "base_url" in data
    assert "conversation_history" in data
    assert "timestamp" in data

    assert data["model"] == agent.model
    assert data["base_url"] == agent.base_url
    assert data["conversation_history"] == agent.conversation_history
    assert isinstance(data["timestamp"], (int, float))


def test_load_conversation_restores_state(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test that load_conversation restores agent state from file."""
    agent = mock_agent_with_persistence

    # Create a conversation file manually
    conversation_data = {
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1",
        "conversation_history": [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"},
        ],
        "timestamp": 1234567890.0,
    }

    conversation_file = agent.conversations_dir / "test-load.json"
    with open(conversation_file, "w") as f:
        json.dump(conversation_data, f, indent=2)

    # Load the conversation
    success, message = agent.load_conversation("test-load")

    assert success is True
    assert "test-load" in message

    # Check that state was restored
    assert agent.model == "gpt-4"
    assert agent.base_url == "https://api.openai.com/v1"
    assert agent.conversation_history == conversation_data["conversation_history"]


def test_load_conversation_returns_error_for_missing_file(
    mock_agent_with_persistence: ClippyAgent,
) -> None:
    """Test that load_conversation returns error for non-existent conversation."""
    agent = mock_agent_with_persistence

    success, message = agent.load_conversation("non-existent")

    assert success is False
    assert "non-existent" in message
    assert "No saved conversation found" in message


def test_list_saved_conversations_returns_names(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test that list_saved_conversations returns all saved conversation names."""
    agent = mock_agent_with_persistence

    # Create some conversation files
    names = ["conv1", "conv2", "conv3"]
    for name in names:
        conversation_file = agent.conversations_dir / f"{name}.json"
        conversation_file.touch()

    # List conversations
    saved_conversations = agent.list_saved_conversations()

    # Should contain all conversation names
    assert len(saved_conversations) == 3
    for name in names:
        assert name in saved_conversations


def test_list_saved_conversations_returns_empty_list_when_no_files(
    mock_agent_with_persistence: ClippyAgent,
) -> None:
    """Test that list_saved_conversations returns empty list when no conversations exist."""
    agent = mock_agent_with_persistence

    # Ensure no conversation files exist
    saved_conversations = agent.list_saved_conversations()

    assert saved_conversations == []


def test_delete_conversation_removes_file(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test that delete_conversation removes the conversation file."""
    agent = mock_agent_with_persistence

    # Create a conversation file
    conversation_file = agent.conversations_dir / "test-delete.json"
    conversation_file.touch()

    # Verify file exists
    assert conversation_file.exists()

    # Delete conversation
    success, message = agent.delete_conversation("test-delete")

    assert success is True
    assert "test-delete" in message
    assert "deleted" in message

    # Verify file no longer exists
    assert not conversation_file.exists()


def test_delete_conversation_returns_error_for_missing_file(
    mock_agent_with_persistence: ClippyAgent,
) -> None:
    """Test that delete_conversation returns error for non-existent conversation."""
    agent = mock_agent_with_persistence

    success, message = agent.delete_conversation("non-existent")

    assert success is False
    assert "non-existent" in message
    assert "No saved conversation found" in message


def test_save_and_load_roundtrip(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test saving and loading a conversation preserves all data."""
    agent = mock_agent_with_persistence

    # Set up conversation data
    original_history = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "2+2 equals 4"},
        {"role": "user", "content": "Thanks!"},
    ]

    agent.conversation_history = original_history
    agent.model = "claude-3-opus"
    agent.base_url = "https://api.anthropic.com/v1"

    # Save conversation
    save_success, save_message = agent.save_conversation("roundtrip-test")
    assert save_success is True

    # Reset agent state
    agent.conversation_history = []
    agent.model = "gpt-5"
    agent.base_url = None

    # Load conversation
    load_success, load_message = agent.load_conversation("roundtrip-test")
    assert load_success is True

    # Verify state was restored
    assert agent.model == "claude-3-opus"
    assert agent.base_url == "https://api.anthropic.com/v1"
    assert agent.conversation_history == original_history


def test_conversation_persistence_handles_exceptions_during_save() -> None:
    """Test that save_conversation handles exceptions gracefully."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
        base_url=None,
    )

    # Mock the json.dump to raise an exception
    with patch("clippy.agent.core.json.dump", side_effect=Exception("Mock error")):
        success, message = agent.save_conversation("test-error")

        assert success is False
        assert "Failed to save conversation" in message
        assert "Mock error" in message


def test_conversation_persistence_handles_exceptions_during_load() -> None:
    """Test that load_conversation handles exceptions gracefully."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
        base_url=None,
    )

    # Mock the json.load to raise an exception
    with patch("clippy.agent.core.json.load", side_effect=Exception("Mock error")):
        # Create a dummy file first
        conversation_file = agent.conversations_dir / "test-error.json"
        conversation_file.touch()

        success, message = agent.load_conversation("test-error")

        assert success is False
        assert "Failed to load conversation" in message
        assert "Mock error" in message


def test_default_conversation_name(mock_agent_with_persistence: ClippyAgent) -> None:
    """Test that save_conversation generates timestamp-based filename when no name provided."""
    agent = mock_agent_with_persistence

    # Add some conversation history
    agent.conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    success, message = agent.save_conversation()  # No name specified

    assert success is True

    # Should generate a timestamp-based filename
    assert "conversation-" in message
    assert "2025" in message  # Should contain the year from timestamp

    # Extract the generated filename from the message
    generated_filename = message.replace("Conversation saved as '", "").replace("'", "")

    # Check that file was created
    conversation_file = agent.conversations_dir / f"{generated_filename}.json"
    assert conversation_file.exists()
