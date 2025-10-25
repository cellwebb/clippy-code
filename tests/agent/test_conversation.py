"""Tests for agent conversation management utilities."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from clippy.agent.conversation import (
    check_and_auto_compact,
    compact_conversation,
    create_system_prompt,
    get_token_count,
)
from clippy.providers import LLMProvider


@pytest.fixture
def temp_agent_docs(tmp_path: Path) -> Path:
    """Create temporary directory for agent documentation files."""
    return tmp_path


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)
    provider.create_message.return_value = {
        "content": (
            "This is a summary of the conversation so far. The user requested X and Y was done."
        ),
        "role": "assistant",
        "finish_reason": "stop",
    }
    return provider


@pytest.fixture
def sample_conversation() -> list[dict[str, Any]]:
    """Create a sample conversation history."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, please help me with my project."},
        {"role": "assistant", "content": "Sure! I'd be happy to help. What do you need?"},
        {"role": "user", "content": "I need to create a Python function."},
        {"role": "assistant", "content": "I'll help you create that function."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "write_file"}}
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "File written successfully",
        },
        {"role": "user", "content": "Thanks! Now can you help with tests?"},
    ]


class TestCreateSystemPrompt:
    """Tests for create_system_prompt function."""

    def test_returns_base_prompt_when_no_docs_exist(self, tmp_path: Path) -> None:
        """Test that base system prompt is returned when no agent docs exist."""
        # Change to temp directory where no agent docs exist
        import os

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            prompt = create_system_prompt()

            # Should return the base prompt (from prompts.py)
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            # Should NOT contain project documentation marker
            assert "PROJECT_DOCUMENTATION:" not in prompt
        finally:
            os.chdir(original_dir)

    def test_finds_agents_md_uppercase(self, tmp_path: Path) -> None:
        """Test that AGENTS.md is found and appended."""
        import os

        # Create AGENTS.md
        agents_file = tmp_path / "AGENTS.md"
        agents_content = "# Agent Documentation\n\nThis is custom agent documentation."
        agents_file.write_text(agents_content, encoding="utf-8")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            prompt = create_system_prompt()

            assert "PROJECT_DOCUMENTATION:" in prompt
            assert agents_content in prompt
        finally:
            os.chdir(original_dir)

    def test_finds_agents_md_lowercase(self, tmp_path: Path) -> None:
        """Test that agents.md (lowercase) is found."""
        import os

        agents_file = tmp_path / "agents.md"
        agents_content = "# Lowercase agent docs"
        agents_file.write_text(agents_content, encoding="utf-8")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            prompt = create_system_prompt()

            assert "PROJECT_DOCUMENTATION:" in prompt
            assert agents_content in prompt
        finally:
            os.chdir(original_dir)

    def test_finds_agent_md(self, tmp_path: Path) -> None:
        """Test that agent.md (singular) is found."""
        import os

        agent_file = tmp_path / "agent.md"
        agent_content = "# Singular agent doc"
        agent_file.write_text(agent_content, encoding="utf-8")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            prompt = create_system_prompt()

            assert "PROJECT_DOCUMENTATION:" in prompt
            assert agent_content in prompt
        finally:
            os.chdir(original_dir)

    def test_prefers_uppercase_agents_md(self, tmp_path: Path) -> None:
        """Test that agent documentation is loaded when files exist."""
        import os

        # Create AGENTS.md file
        (tmp_path / "AGENTS.md").write_text("UPPERCASE DOCS", encoding="utf-8")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            prompt = create_system_prompt()

            # Should include project documentation
            assert "PROJECT_DOCUMENTATION:" in prompt
            assert "UPPERCASE DOCS" in prompt
        finally:
            os.chdir(original_dir)

    def test_handles_read_error_gracefully(self, tmp_path: Path) -> None:
        """Test that read errors are handled gracefully."""
        import os

        # Create a file we can't read (by mocking read_text to raise an error)
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("test", encoding="utf-8")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
                prompt = create_system_prompt()

                # Should fall back to base prompt
                assert "PROJECT_DOCUMENTATION:" not in prompt
        finally:
            os.chdir(original_dir)


class TestGetTokenCount:
    """Tests for get_token_count function."""

    def test_counts_empty_conversation(self) -> None:
        """Test token counting for empty conversation."""
        result = get_token_count([], model="gpt-4", base_url=None)

        assert result["total_tokens"] == 0
        assert result["message_count"] == 0
        assert result["model"] == "gpt-4"
        assert result["base_url"] is None

    def test_counts_simple_conversation(self) -> None:
        """Test token counting for simple conversation."""
        conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        assert result["total_tokens"] > 0
        assert result["message_count"] == 3
        assert result["system_messages"] == 1
        assert result["user_messages"] == 1
        assert result["assistant_messages"] == 1
        assert result["tool_messages"] == 0

    def test_counts_tool_messages(self) -> None:
        """Test that tool messages are counted correctly."""
        conversation = [
            {"role": "system", "content": "system"},
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "test"}}]},
            {"role": "tool", "tool_call_id": "123", "content": "result"},
        ]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        assert result["tool_messages"] == 1
        assert result["tool_tokens"] > 0

    def test_calculates_usage_percent(self) -> None:
        """Test that usage percentage is calculated."""
        conversation = [
            {"role": "user", "content": "test message"},
        ]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        assert "usage_percent" in result
        assert result["usage_percent"] >= 0
        assert result["usage_percent"] <= 100

    def test_handles_unknown_model(self) -> None:
        """Test that unknown models fall back to cl100k_base encoding."""
        conversation = [
            {"role": "user", "content": "test"},
        ]

        result = get_token_count(conversation, model="unknown-model-xyz", base_url=None)

        # Should still work with fallback encoding
        assert result["total_tokens"] > 0
        assert "error" not in result

    def test_handles_tool_calls_in_message(self) -> None:
        """Test token counting with tool_calls in messages."""
        conversation = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path": "test.py"}'},
                    }
                ],
            }
        ]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        # Should count both role and tool_calls
        assert result["total_tokens"] > 0
        assert result["assistant_messages"] == 1

    def test_handles_empty_content(self) -> None:
        """Test messages with empty or missing content."""
        conversation = [
            {"role": "assistant", "content": ""},
            {"role": "assistant"},  # No content field
        ]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        assert result["message_count"] == 2
        assert result["assistant_messages"] == 2
        # Should still count role tokens and overhead
        assert result["total_tokens"] > 0

    def test_returns_error_on_exception(self) -> None:
        """Test that errors are handled gracefully."""
        # Create invalid conversation that might cause issues
        conversation = [{"invalid": "structure"}]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        # Should return basic info even on error
        assert result["message_count"] == 1
        assert result["model"] == "gpt-4"

    def test_categorizes_all_roles(self) -> None:
        """Test that all message roles are categorized correctly."""
        conversation = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
            {"role": "assistant", "content": "assistant"},
            {"role": "tool", "tool_call_id": "123", "content": "tool"},
        ]

        result = get_token_count(conversation, model="gpt-4", base_url=None)

        assert result["system_messages"] == 1
        assert result["user_messages"] == 1
        assert result["assistant_messages"] == 1
        assert result["tool_messages"] == 1
        assert result["system_tokens"] > 0
        assert result["user_tokens"] > 0
        assert result["assistant_tokens"] > 0
        assert result["tool_tokens"] > 0


class TestCompactConversation:
    """Tests for compact_conversation function."""

    def test_refuses_to_compact_short_conversation(self, mock_provider: MagicMock) -> None:
        """Test that short conversations are not compacted."""
        short_conversation = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

        success, message, stats, new_history = compact_conversation(
            short_conversation, mock_provider, "gpt-4", keep_recent=4
        )

        assert success is False
        assert "too short" in message.lower()
        assert stats == {}
        assert new_history == []

    def test_compacts_long_conversation(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that long conversations are compacted successfully."""
        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is True
        assert "compacted" in message.lower()
        assert stats["messages_before"] == len(sample_conversation)
        assert stats["messages_after"] < len(sample_conversation)
        # Should have: system + summary + 2 recent messages = 4
        assert len(new_history) == 4

    def test_preserves_system_message(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that system message is preserved in compacted conversation."""
        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is True
        assert new_history[0]["role"] == "system"
        assert new_history[0]["content"] == sample_conversation[0]["content"]

    def test_preserves_recent_messages(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that recent messages are preserved."""
        keep_recent = 2
        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=keep_recent
        )

        assert success is True
        # Last N messages should be preserved exactly
        assert new_history[-keep_recent:] == sample_conversation[-keep_recent:]

    def test_creates_summary_message(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that a summary message is created."""
        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is True
        # Summary should be the second message (after system)
        summary_msg = new_history[1]
        assert summary_msg["role"] == "assistant"
        assert "[CONVERSATION SUMMARY]" in summary_msg["content"]
        assert "[END SUMMARY]" in summary_msg["content"]

    def test_calls_provider_with_correct_messages(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that provider is called with correct summarization request."""
        compact_conversation(sample_conversation, mock_provider, "gpt-4", keep_recent=2)

        # Verify provider was called
        assert mock_provider.create_message.called
        call_args = mock_provider.create_message.call_args

        # Check the messages parameter
        messages = call_args.kwargs["messages"]
        # Should include system + messages to summarize + summary request
        assert len(messages) > 2
        # Last message should be the summary request
        assert messages[-1]["role"] == "user"
        assert "summary" in messages[-1]["content"].lower()

    def test_calculates_token_reduction(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that token reduction statistics are calculated."""
        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is True
        assert "before_tokens" in stats
        assert "after_tokens" in stats
        assert "tokens_saved" in stats
        assert "reduction_percent" in stats
        assert stats["tokens_saved"] == stats["before_tokens"] - stats["after_tokens"]

    def test_handles_provider_error(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test handling of provider errors during summarization."""
        mock_provider.create_message.side_effect = Exception("API Error")

        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is False
        assert "error" in message.lower()
        assert stats == {}
        assert new_history == []

    def test_handles_empty_summary(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test handling when provider returns empty summary."""
        mock_provider.create_message.return_value = {
            "content": "",  # Empty content
            "role": "assistant",
        }

        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is False
        assert "failed" in message.lower()

    def test_respects_keep_recent_parameter(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that keep_recent parameter is respected."""
        # Try with different keep_recent values
        for keep_recent in [2, 3, 4]:
            success, message, stats, new_history = compact_conversation(
                sample_conversation.copy(), mock_provider, "gpt-4", keep_recent=keep_recent
            )

            if success:
                # Should have: system + summary + keep_recent messages
                expected_length = 2 + keep_recent
                assert len(new_history) == expected_length

    def test_no_messages_to_compact(self, mock_provider: MagicMock) -> None:
        """Test when there are no messages between system and recent."""
        conversation = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "recent 1"},
            {"role": "assistant", "content": "recent 2"},
        ]

        success, message, stats, new_history = compact_conversation(
            conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is False
        # Should fail because conversation is too short or no messages to compact
        assert "no messages" in message.lower() or "too short" in message.lower()

    def test_preserves_message_structure(
        self, mock_provider: MagicMock, sample_conversation: list[dict[str, Any]]
    ) -> None:
        """Test that message structure is preserved in compacted history."""
        success, message, stats, new_history = compact_conversation(
            sample_conversation, mock_provider, "gpt-4", keep_recent=2
        )

        assert success is True

        # All messages should have required fields
        for msg in new_history:
            assert "role" in msg
            assert "content" in msg

        # Recent messages should be identical to originals
        assert new_history[-2:] == sample_conversation[-2:]


class TestCheckAndAutoCompact:
    """Tests for check_and_auto_compact function."""

    def test_no_threshold_set(self, mock_provider: MagicMock) -> None:
        """Test that no compaction occurs when no threshold is set."""
        conversation = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

        # No threshold set for this model
        compacted, message, stats = check_and_auto_compact(
            conversation, "test-model", mock_provider
        )

        assert compacted is False
        assert "threshold" in message.lower()
        assert stats == {}

    @patch("clippy.agent.conversation.get_token_count")
    @patch("clippy.agent.conversation.get_model_compaction_threshold")
    def test_below_threshold(
        self,
        mock_get_model_threshold: MagicMock,
        mock_get_token_count: MagicMock,
        mock_provider: MagicMock,
    ) -> None:
        """Test that no compaction occurs when below threshold."""
        conversation = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

        # Set up mocks
        mock_get_model_threshold.return_value = 10000  # High threshold
        mock_get_token_count.return_value = {
            "total_tokens": 500,
            "message_count": 3,
            "model": "test-model",
        }  # Well below threshold

        compacted, message, stats = check_and_auto_compact(
            conversation, "test-model", mock_provider
        )

        assert compacted is False
        assert "below threshold" in message.lower()

    @patch("clippy.agent.conversation.compact_conversation")
    @patch("clippy.agent.conversation.get_token_count")
    @patch("clippy.agent.conversation.get_model_compaction_threshold")
    def test_compact_triggered(
        self,
        mock_get_model_threshold: MagicMock,
        mock_get_token_count: MagicMock,
        mock_compact_conversation: MagicMock,
        mock_provider: MagicMock,
    ) -> None:
        """Test that compaction is triggered when above threshold."""
        conversation = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

        # Set up mocks
        mock_get_model_threshold.return_value = 10  # Low threshold
        mock_get_token_count.return_value = {
            "total_tokens": 500,
            "message_count": 3,
            "model": "test-model",
        }  # Above threshold
        mock_compact_conversation.return_value = (
            True,
            "Conversation compacted: 500 → 200 tokens (60.0% reduction)",
            {"before_tokens": 500, "after_tokens": 200, "reduction_percent": 60.0},
            [
                {"role": "system", "content": "system prompt"},
                {"role": "assistant", "content": "summary"},
            ],
        )

        compacted, message, stats = check_and_auto_compact(
            conversation, "test-model", mock_provider
        )

        # Should have been compacted
        assert compacted is True
        assert "compacted" in message.lower()

    @patch("clippy.agent.conversation.compact_conversation")
    @patch("clippy.agent.conversation.get_token_count")
    @patch("clippy.agent.conversation.get_model_compaction_threshold")
    def test_compact_failure(
        self,
        mock_get_model_threshold: MagicMock,
        mock_get_token_count: MagicMock,
        mock_compact_conversation: MagicMock,
        mock_provider: MagicMock,
    ) -> None:
        """Test handling of compaction failure."""
        conversation = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
        ]

        # Set up mocks
        mock_get_model_threshold.return_value = 1  # Very low threshold to trigger compaction
        mock_get_token_count.return_value = {
            "total_tokens": 500,
            "message_count": 2,
            "model": "test-model",
        }  # Above threshold
        mock_compact_conversation.return_value = (
            False,
            "Conversation too short to compact (need >7 messages)",
            {},
            [],
        )

        compacted, message, stats = check_and_auto_compact(
            conversation, "test-model", mock_provider
        )

        # Should not compact due to conversation being too short
        assert compacted is False
        assert "too short" in message.lower()
