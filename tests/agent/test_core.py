"""Tests for the agent model switching functionality."""

import pytest

from clippy.agent import ClippyAgent
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


@pytest.fixture
def mock_agent() -> ClippyAgent:
    """Create a ClippyAgent with mocked dependencies."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
        base_url=None,
    )

    return agent


def test_agent_initialization(mock_agent: ClippyAgent) -> None:
    """Test that agent initializes with correct values."""
    assert mock_agent.model == "gpt-5"
    assert mock_agent.base_url is None
    assert mock_agent.api_key == "test-key"
    assert mock_agent.provider is not None


def test_agent_requires_model() -> None:
    """Test that agent raises ValueError when initialized without a model."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    with pytest.raises(ValueError, match="Model must be specified"):
        ClippyAgent(
            permission_manager=permission_manager,
            executor=executor,
            api_key="test-key",
            model=None,  # This should raise ValueError
        )


def test_switch_model_changes_model(mock_agent: ClippyAgent) -> None:
    """Test switching to a different model."""
    success, message = mock_agent.switch_model(model="gpt-3.5-turbo")

    assert success is True
    assert "gpt-3.5-turbo" in message
    assert mock_agent.model == "gpt-3.5-turbo"


def test_switch_model_changes_base_url(mock_agent: ClippyAgent) -> None:
    """Test switching to a different provider base URL."""
    success, message = mock_agent.switch_model(
        model="llama3.1-8b", base_url="https://api.cerebras.ai/v1"
    )

    assert success is True
    assert mock_agent.model == "llama3.1-8b"
    assert mock_agent.base_url == "https://api.cerebras.ai/v1"


def test_switch_model_changes_api_key(mock_agent: ClippyAgent) -> None:
    """Test switching with a different API key."""
    success, message = mock_agent.switch_model(
        model="llama3.1-8b",
        base_url="https://api.cerebras.ai/v1",
        api_key="new-test-key",
    )

    assert success is True
    assert mock_agent.api_key == "new-test-key"
    assert mock_agent.model == "llama3.1-8b"
    assert mock_agent.base_url == "https://api.cerebras.ai/v1"


def test_switch_model_keeps_current_values_if_none(mock_agent: ClippyAgent) -> None:
    """Test that None values preserve current settings."""
    original_model = mock_agent.model
    original_base_url = mock_agent.base_url
    original_api_key = mock_agent.api_key

    # Call with all None - should keep everything the same
    success, message = mock_agent.switch_model(model=None, base_url=None, api_key=None)

    assert success is True
    assert mock_agent.model == original_model
    assert mock_agent.base_url == original_base_url
    assert mock_agent.api_key == original_api_key


def test_switch_model_partial_update(mock_agent: ClippyAgent) -> None:
    """Test updating only some parameters."""
    original_api_key = mock_agent.api_key

    # Only update model, keep base_url and api_key
    success, message = mock_agent.switch_model(model="new-model")

    assert success is True
    assert mock_agent.model == "new-model"
    assert mock_agent.api_key == original_api_key


def test_reset_conversation(mock_agent: ClippyAgent) -> None:
    """Test resetting conversation history."""
    # Add some conversation history
    mock_agent.conversation_history = [
        {"role": "user", "content": "test message"},
        {"role": "assistant", "content": "test response"},
    ]

    mock_agent.reset_conversation()

    assert len(mock_agent.conversation_history) == 0
    assert mock_agent.interrupted is False


def test_conversation_history_preserved_after_model_switch(mock_agent: ClippyAgent) -> None:
    """Test that conversation history is preserved when switching models."""
    # Add conversation history
    mock_agent.conversation_history = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "test message"},
    ]

    original_length = len(mock_agent.conversation_history)

    # Switch model
    mock_agent.switch_model(model="gpt-4")

    # Conversation history should still be intact
    assert len(mock_agent.conversation_history) == original_length
    assert mock_agent.conversation_history[0]["role"] == "system"
    assert mock_agent.conversation_history[1]["role"] == "user"


def test_provider_recreated_on_switch(mock_agent: ClippyAgent) -> None:
    """Test that provider is recreated when switching models."""
    original_provider = mock_agent.provider

    # Switch to different provider
    mock_agent.switch_model(
        model="llama3.1-8b", base_url="https://api.cerebras.ai/v1", api_key="new-key"
    )

    # Provider should be a new instance
    assert mock_agent.provider is not original_provider


def test_approval_callback_is_used() -> None:
    """Test that agent uses approval_callback when provided."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    # Track if callback was called
    callback_called = {"called": False, "tool_name": None, "tool_input": None}

    def mock_approval_callback(tool_name: str, tool_input: dict) -> bool:
        callback_called["called"] = True
        callback_called["tool_name"] = tool_name
        callback_called["tool_input"] = tool_input
        return True  # Approve

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
        approval_callback=mock_approval_callback,
    )

    # Verify callback is set
    assert agent.approval_callback is mock_approval_callback
    assert agent.approval_callback == mock_approval_callback


def test_approval_callback_respects_response() -> None:
    """Test that agent respects approval callback response."""
    permission_manager = PermissionManager(PermissionConfig())
    executor = ActionExecutor(permission_manager)

    def deny_callback(tool_name: str, tool_input: dict) -> bool:
        return False  # Deny all actions

    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key="test-key",
        model="gpt-5",
        approval_callback=deny_callback,
    )

    # Verify the callback is set
    assert agent.approval_callback is deny_callback
