"""Integration tests for subagent workflow."""

from unittest.mock import MagicMock, patch

import pytest

from clippy.agent.core import ClippyAgent
from clippy.agent.subagent import SubAgentConfig, SubAgentResult
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


class TestSubagentWorkflowIntegration:
    """Integration tests for complete subagent workflows."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        provider = MagicMock()
        provider.stream_chat_completion.return_value = iter(["response"])
        return provider

    @pytest.fixture
    def mock_permission_manager(self):
        """Create a mock permission manager."""
        manager = MagicMock(spec=PermissionManager)
        manager.check_permission.return_value = (True, "Approved")
        return manager

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor."""
        executor = MagicMock(spec=ActionExecutor)
        return executor

    @pytest.fixture
    def mock_agent(self, mock_llm_provider, mock_permission_manager, mock_executor):
        """Create a mock ClippyAgent."""
        agent = MagicMock(spec=ClippyAgent)
        agent.api_key = "test_key"
        agent.base_url = "https://api.test.com"
        agent.model = "gpt-4-turbo"
        agent.provider_config = None
        agent.console = MagicMock()
        agent.mcp_manager = MagicMock()
        return agent

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_simple_delegation_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test simple subagent delegation workflow."""
        # Mock successful subagent execution
        mock_run_loop.return_value = "Task completed successfully"

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
            enable_cache=False,
            enable_chaining=False,
        )

        # Create and run subagent
        config = SubAgentConfig(
            name="test_subagent",
            task="Analyze this Python file for security issues",
            subagent_type="code_review",
        )

        subagent = manager.create_subagent(config)
        results = manager.run_sequential([subagent])
        result = results[0]

        # Verify workflow
        assert result.success is True
        assert "Task completed successfully" in result.output
        assert result.metadata["subagent_type"] == "code_review"

        # Verify state tracking
        assert len(manager.completed_subagents) == 1
        assert len(manager.active_subagents) == 0

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_parallel_execution_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test parallel subagent execution workflow."""

        # Mock responses based on conversation history to ensure correct mapping
        def mock_loop_response(**kwargs):
            # Extract task from conversation history
            history = kwargs.get("conversation_history", [])
            for msg in history:
                if msg["role"] == "user":
                    if "Review code" in msg["content"]:
                        return "Code review completed"
                    elif "Write tests" in msg["content"]:
                        return "Tests generated"
                    elif "Write docs" in msg["content"]:
                        return "Documentation written"
            return "Task completed"

        mock_run_loop.side_effect = mock_loop_response

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
            max_concurrent=2,
        )

        # Create multiple subagents
        configs = [
            SubAgentConfig(
                name="reviewer",
                task="Review code",
                subagent_type="code_review",
            ),
            SubAgentConfig(
                name="tester",
                task="Write tests",
                subagent_type="testing",
            ),
            SubAgentConfig(
                name="doc_writer",
                task="Write docs",
                subagent_type="documentation",
            ),
        ]

        subagents = [manager.create_subagent(config) for config in configs]

        # Run in parallel
        results = manager.run_parallel(subagents, max_concurrent=2)

        # Verify parallel execution
        assert len(results) == 3
        assert all(result.success for result in results)

        # Verify all expected outputs are present (order preserved by index)
        # The run_parallel method maintains order based on input list
        assert "Code review completed" in results[0].output
        assert "Tests generated" in results[1].output
        assert "Documentation written" in results[2].output

        # Verify statistics
        stats = manager.get_statistics()
        assert stats["completed_count"] == 3
        assert stats["successful_count"] == 3
        assert stats["failed_count"] == 0

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_sequential_execution_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test sequential subagent execution workflow."""
        # Mock responses
        mock_run_loop.side_effect = [
            "Step 1 completed",
            "Step 2 completed",
            "Step 3 completed",
        ]

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create dependent subagents
        configs = [
            SubAgentConfig(
                name="step1",
                task="Initial analysis",
                subagent_type="general",
            ),
            SubAgentConfig(
                name="step2",
                task="Refactoring",
                subagent_type="refactor",
            ),
            SubAgentConfig(
                name="step3",
                task="Testing",
                subagent_type="testing",
            ),
        ]

        subagents = [manager.create_subagent(config) for config in configs]

        # Run sequentially
        results = manager.run_sequential(subagents)

        # Verify sequential execution
        assert len(results) == 3
        assert all(result.success for result in results)
        assert "Step 1 completed" in results[0].output
        assert "Step 2 completed" in results[1].output
        assert "Step 3 completed" in results[2].output

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_error_handling_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test error handling in subagent workflow."""

        # Mock responses based on conversation history - fail the second task
        def mock_loop_response(**kwargs):
            history = kwargs.get("conversation_history", [])
            for msg in history:
                if msg["role"] == "user":
                    if "Task 1" in msg["content"]:
                        return "Success 1"
                    elif "Task 2" in msg["content"]:
                        raise RuntimeError("Subagent failed")
                    elif "Task 3" in msg["content"]:
                        return "Success 2"
            return "Task completed"

        mock_run_loop.side_effect = mock_loop_response

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create subagents
        configs = [
            SubAgentConfig(
                name="success1",
                task="Task 1",
                subagent_type="general",
            ),
            SubAgentConfig(
                name="failure",
                task="Task 2",
                subagent_type="general",
            ),
            SubAgentConfig(
                name="success2",
                task="Task 3",
                subagent_type="general",
            ),
        ]

        subagents = [manager.create_subagent(config) for config in configs]

        # Run in parallel to test error isolation
        results = manager.run_parallel(subagents)

        # Verify error handling
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert "Subagent failed" in results[1].error

        # Verify other subagents still succeeded
        stats = manager.get_statistics()
        assert stats["successful_count"] == 2
        assert stats["failed_count"] == 1

    def test_timeout_workflow(self, mock_agent, mock_permission_manager, mock_executor):
        """Test timeout handling in subagent workflow."""

        # Mock a slow-running task
        def slow_task(*args, **kwargs):
            import time

            time.sleep(2)  # Simulate slow task
            return "Should not reach here"

        with patch("clippy.agent.subagent.run_agent_loop", side_effect=slow_task):
            # Create subagent manager
            from clippy.agent.subagent_manager import SubAgentManager

            manager = SubAgentManager(
                parent_agent=mock_agent,
                permission_manager=mock_permission_manager,
                executor=mock_executor,
            )

            # Create subagent with short timeout
            config = SubAgentConfig(
                name="slow_subagent",
                task="Slow task",
                subagent_type="general",
                timeout=0.1,  # Very short timeout
            )

            subagent = manager.create_subagent(config)
            result = subagent.run()

            # Verify timeout handling
            assert result.success is False
            assert "exceeded timeout limit" in result.error
            assert result.metadata["failure_reason"] == "timeout"

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_tool_filtering_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test tool filtering in subagent workflow."""
        mock_run_loop.return_value = "Code reviewed successfully"

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create code review subagent (should have limited tools)
        config = SubAgentConfig(
            name="reviewer",
            task="Review this code",
            subagent_type="code_review",
        )

        manager.create_subagent(config)

        # Verify tool filtering was applied during initialization
        from clippy.agent.subagent_types import get_subagent_config

        type_config = get_subagent_config("code_review")
        allowed_tools = type_config["allowed_tools"]

        assert isinstance(allowed_tools, list)
        assert "read_file" in allowed_tools
        assert "write_file" not in allowed_tools  # Should be read-only

    def test_context_sharing_workflow(self, mock_agent, mock_permission_manager, mock_executor):
        """Test context sharing to subagents."""
        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create subagent with context
        context = {
            "project": "my_project",
            "focus": "security",
            "files": ["auth.py", "user.py"],
        }

        config = SubAgentConfig(
            name="context_subagent",
            task="Review authentication files",
            subagent_type="code_review",
            context=context,
        )

        subagent = manager.create_subagent(config)

        # Verify context was added to system prompt
        system_content = subagent.conversation_history[0]["content"]
        assert "Context:" in system_content
        assert "project: my_project" in system_content
        assert "focus: security" in system_content
        assert "files: ['auth.py', 'user.py']" in system_content

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_iteration_limit_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test iteration limit in subagent workflow."""
        mock_run_loop.return_value = "Task completed within limit"

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create subagent with custom iteration limit
        config = SubAgentConfig(
            name="limited_subagent",
            task="Task with iteration limit",
            subagent_type="general",
            max_iterations=50,
        )

        subagent = manager.create_subagent(config)

        # Mock the run_agent_loop call to verify iteration limit
        with patch("clippy.agent.subagent.run_agent_loop") as mock_loop:
            mock_loop.return_value = "Completed"
            subagent.run()

            # Verify iteration limit was passed
            call_kwargs = mock_loop.call_args[1]
            assert call_kwargs["max_iterations"] == 50

    @patch("clippy.agent.subagent.run_agent_loop")
    def test_model_override_workflow(
        self,
        mock_run_loop,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test model override in subagent workflow."""
        mock_run_loop.return_value = "Task completed with custom model"

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create subagent with model override
        config = SubAgentConfig(
            name="model_subagent",
            task="Task with custom model",
            subagent_type="general",
            model="claude-3-opus-20240229",
        )

        subagent = manager.create_subagent(config)

        # Verify model override
        assert subagent.model == "claude-3-opus-20240229"
        assert subagent.model != mock_agent.model  # Should be different from parent

    @pytest.mark.asyncio
    async def test_async_parallel_workflow(
        self,
        mock_agent,
        mock_permission_manager,
        mock_executor,
    ):
        """Test async parallel execution workflow."""
        from unittest.mock import MagicMock

        # Create subagent manager
        from clippy.agent.subagent_manager import SubAgentManager

        manager = SubAgentManager(
            parent_agent=mock_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
        )

        # Create subagents
        configs = [
            SubAgentConfig(
                name="async1",
                task="Async task 1",
                subagent_type="general",
            ),
            SubAgentConfig(
                name="async2",
                task="Async task 2",
                subagent_type="general",
            ),
        ]

        subagents = [manager.create_subagent(config) for config in configs]

        # Mock the run method to return a result (sync mock since run_in_executor expects sync)
        mock_result = SubAgentResult(
            success=True,
            output="Async result",
            error=None,
            iterations_used=5,
            execution_time=2.0,
        )
        for subagent in subagents:
            subagent.run = MagicMock(return_value=mock_result)

        # Run async parallel
        results = await manager.run_parallel_async(subagents, max_concurrent=2)

        # Verify async execution
        assert len(results) == 2
        assert all(result.success for result in results)
