"""Tests for the SubAgent class."""

import time
from unittest.mock import MagicMock, patch

import pytest

from clippy.agent.core import ClippyAgent
from clippy.agent.subagent import SubAgent, SubAgentConfig, SubAgentResult, SubAgentStatus
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


class TestSubAgentConfig:
    """Test SubAgentConfig dataclass."""

    def test_subagent_config_creation(self):
        """Test creating a SubAgentConfig."""
        config = SubAgentConfig(
            name="test_subagent",
            task="Test task",
            subagent_type="general",
            timeout=300,
            max_iterations=25,
        )

        assert config.name == "test_subagent"
        assert config.task == "Test task"
        assert config.subagent_type == "general"
        assert config.timeout == 300
        assert config.max_iterations == 25
        assert config.context == {}
        assert config.allowed_tools is None
        assert config.system_prompt is None
        assert config.model is None

    def test_subagent_config_with_context(self):
        """Test SubAgentConfig with context."""
        context = {"project": "test", "focus": "security"}
        config = SubAgentConfig(
            name="test_subagent",
            task="Test task",
            subagent_type="code_review",
            context=context,
        )

        assert config.context == context


class TestSubAgent:
    """Test SubAgent class."""

    @pytest.fixture
    def mock_parent_agent(self):
        """Create a mock parent agent."""
        agent = MagicMock(spec=ClippyAgent)
        agent.api_key = "test_key"
        agent.base_url = "https://api.test.com"
        agent.model = "gpt-4-turbo"
        agent.provider_config = None
        agent.console = MagicMock()
        agent.mcp_manager = MagicMock()
        return agent

    @pytest.fixture
    def mock_permission_manager(self):
        """Create a mock permission manager."""
        return MagicMock(spec=PermissionManager)

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor."""
        return MagicMock(spec=ActionExecutor)

    @pytest.fixture
    def subagent_config(self):
        """Create a test subagent configuration."""
        return SubAgentConfig(
            name="test_subagent",
            task="Test task description",
            subagent_type="general",
            timeout=300,
            max_iterations=25,
        )

    @pytest.fixture
    def subagent(self, mock_parent_agent, mock_permission_manager, mock_executor, subagent_config):
        """Create a test subagent."""
        return SubAgent(
            config=subagent_config,
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

    def test_subagent_initialization(self, subagent, subagent_config):
        """Test subagent initialization."""
        assert subagent.config == subagent_config
        assert subagent.status == SubAgentStatus.PENDING
        assert subagent.result is None
        assert subagent.start_time is None
        assert subagent.end_time is None
        assert subagent.interrupted is False
        assert subagent.model == "gpt-4-turbo"  # Should inherit from parent

    def test_conversation_history_initialization(self, subagent):
        """Test conversation history is properly initialized."""
        assert len(subagent.conversation_history) == 1  # System prompt only
        assert subagent.conversation_history[0]["role"] == "system"
        assert "clippy" in subagent.conversation_history[0]["content"].lower()
        assert "helpful" in subagent.conversation_history[0]["content"].lower()

    def test_custom_system_prompt(self, mock_parent_agent, mock_permission_manager, mock_executor):
        """Test subagent with custom system prompt."""
        custom_prompt = "You are a specialized testing assistant."
        config = SubAgentConfig(
            name="test_subagent",
            task="Test task",
            subagent_type="general",
            system_prompt=custom_prompt,
        )

        subagent = SubAgent(
            config=config,
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        assert subagent.conversation_history[0]["content"] == custom_prompt

    def test_context_addition(self, mock_parent_agent, mock_permission_manager, mock_executor):
        """Test context is added to system prompt."""
        context = {"project": "test_project", "focus": "security"}
        config = SubAgentConfig(
            name="test_subagent",
            task="Test task",
            subagent_type="general",
            context=context,
        )

        subagent = SubAgent(
            config=config,
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        system_content = subagent.conversation_history[0]["content"]
        assert "Context:" in system_content
        assert "project: test_project" in system_content
        assert "focus: security" in system_content

    def test_get_status(self, subagent):
        """Test getting subagent status."""
        assert subagent.get_status() == SubAgentStatus.PENDING

    def test_interrupt(self, subagent):
        """Test interrupting subagent."""
        subagent.interrupt()
        assert subagent.interrupted is True
        assert subagent.get_status() == SubAgentStatus.INTERRUPTED

    def test_get_result_before_execution(self, subagent):
        """Test getting result before execution."""
        assert subagent.get_result() is None

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_successful_execution(self, mock_run_loop, subagent):
        """Test successful subagent execution."""
        # Mock successful run
        mock_response = "Task completed successfully"
        mock_run_loop.return_value = mock_response

        # Execute subagent
        result = subagent.run()

        # Verify result
        assert isinstance(result, SubAgentResult)
        assert result.success is True
        assert result.output == mock_response
        assert result.error is None
        assert result.execution_time > 0
        assert result.metadata["subagent_name"] == "test_subagent"
        assert result.metadata["subagent_type"] == "general"

        # Verify state changes
        assert subagent.status == SubAgentStatus.COMPLETED
        assert subagent.result == result
        assert subagent.start_time is not None
        assert subagent.end_time is not None

        # Verify task was added to conversation
        user_messages = [msg for msg in subagent.conversation_history if msg["role"] == "user"]
        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "Test task description"

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_execution_with_timeout(self, mock_run_loop, subagent):
        """Test subagent execution with timeout."""

        # Mock a long-running task that times out
        def slow_task(*args, **kwargs):
            time.sleep(2)  # Simulate slow task
            return "Should not reach here"

        mock_run_loop.side_effect = slow_task

        # Set very short timeout
        subagent.config.timeout = 0.1

        # Execute subagent (should timeout)
        result = subagent.run()

        # Verify timeout result
        assert isinstance(result, SubAgentResult)
        assert result.success is False
        assert "exceeded timeout limit" in result.error
        assert subagent.status == SubAgentStatus.TIMEOUT

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_execution_with_exception(self, mock_run_loop, subagent):
        """Test subagent execution with exception."""
        # Mock an exception
        mock_run_loop.side_effect = ValueError("Test error")

        # Execute subagent
        result = subagent.run()

        # Verify error result
        assert isinstance(result, SubAgentResult)
        assert result.success is False
        assert "Test error" in result.error
        assert result.metadata["failure_reason"] == "exception"
        assert result.metadata["exception_type"] == "ValueError"
        assert subagent.status == SubAgentStatus.FAILED

    def test_run_when_not_pending(self, subagent):
        """Test running subagent when not in PENDING state."""
        # Set status to completed
        subagent.status = SubAgentStatus.COMPLETED

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="not in PENDING state"):
            subagent.run()

    def test_iteration_count_estimation(self, subagent):
        """Test iteration count estimation."""
        # Add some assistant messages
        subagent.conversation_history.extend(
            [
                {"role": "assistant", "content": "Response 1"},
                {"role": "assistant", "content": "Response 2"},
                {"role": "assistant", "content": "Response 3"},
            ]
        )

        count = subagent._get_iteration_count()
        assert count == 3

    @patch("clippy.agent.subagent.get_token_count")
    def test_get_token_count(self, mock_get_token_count, subagent):
        """Test getting token count."""
        mock_tokens = {"prompt_tokens": 100, "completion_tokens": 50, "total": 150}
        mock_get_token_count.return_value = mock_tokens

        tokens = subagent.get_token_count()
        assert tokens == mock_tokens
        mock_get_token_count.assert_called_once_with(
            subagent.conversation_history, subagent.model, subagent.parent_agent.base_url
        )

    def test_different_subagent_types(
        self,
        mock_parent_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test subagent with different types."""
        types_and_prompts = [
            ("code_review", "code review specialist"),
            ("testing", "testing specialist"),
            ("refactor", "refactoring specialist"),
            ("documentation", "documentation specialist"),
        ]

        for subagent_type, expected_prompt in types_and_prompts:
            config = SubAgentConfig(
                name=f"test_{subagent_type}",
                task="Test task",
                subagent_type=subagent_type,
            )

            subagent = SubAgent(
                config=config,
                parent_agent=mock_parent_agent,
                permission_manager=mock_permission_manager,
                executor=mock_executor,
            )

            system_content = subagent.conversation_history[0]["content"]
            assert expected_prompt in system_content.lower()

    def test_model_override(self, mock_parent_agent, mock_permission_manager, mock_executor):
        """Test subagent with model override."""
        config = SubAgentConfig(
            name="test_subagent",
            task="Test task",
            subagent_type="general",
            model="claude-3-opus-20240229",
        )

        subagent = SubAgent(
            config=config,
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        assert subagent.model == "claude-3-opus-20240229"

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_max_iterations_override(
        self,
        mock_run_loop,
        mock_parent_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test max_iterations override."""
        config = SubAgentConfig(
            name="test_subagent",
            task="Test task",
            subagent_type="general",
            max_iterations=50,
        )

        subagent = SubAgent(
            config=config,
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        mock_run_loop.return_value = "Response"
        subagent.run()

        # Verify max_iterations was passed correctly
        mock_run_loop.assert_called_once()
        call_kwargs = mock_run_loop.call_args[1]
        assert call_kwargs["max_iterations"] == 50
