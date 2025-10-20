"""Tests for the SubAgentManager class."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from clippy.agent.core import ClippyAgent
from clippy.agent.subagent import SubAgent, SubAgentConfig, SubAgentResult
from clippy.agent.subagent_manager import SubAgentManager
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


class TestSubAgentManager:
    """Test SubAgentManager class."""

    @pytest.fixture
    def mock_parent_agent(self):
        """Create a mock parent agent."""
        agent = MagicMock(spec=ClippyAgent)
        agent.api_key = "test_key"
        agent.base_url = "https://api.test.com"
        agent.model = "gpt-4-turbo"
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
    def manager(self, mock_parent_agent, mock_permission_manager, mock_executor):
        """Create a SubAgentManager instance."""
        return SubAgentManager(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
            max_concurrent=3,
            enable_cache=False,
            enable_chaining=False,
        )

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

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.max_concurrent == 3
        assert manager.cache_enabled is False
        assert manager.enable_chaining is False
        assert len(manager.active_subagents) == 0
        assert len(manager.completed_subagents) == 0

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_create_subagent_success(self, mock_subagent_class, manager, subagent_config):
        """Test successful subagent creation."""
        # Mock SubAgent instance
        mock_subagent = MagicMock(spec=SubAgent)
        mock_subagent.config = subagent_config
        mock_subagent_class.return_value = mock_subagent

        # Create subagent
        result = manager.create_subagent(subagent_config)

        # Verify creation
        assert result == mock_subagent
        mock_subagent_class.assert_called_once_with(
            config=subagent_config,
            parent_agent=manager.parent_agent,
            permission_manager=manager.permission_manager,
            executor=manager.executor,
        )

        # Verify tracking
        assert subagent_config.name in manager.active_subagents
        assert manager.active_subagents[subagent_config.name] == mock_subagent

    def test_create_subagent_invalid_config(self, manager):
        """Test creating subagent with invalid configuration."""
        # Create invalid config (missing required fields)
        invalid_config = SubAgentConfig(
            name="",  # Empty name should be invalid
            task="Test task",
            subagent_type="general",
        )

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid subagent configuration"):
            manager.create_subagent(invalid_config)

    def test_create_subagent_invalid_type(self, manager):
        """Test creating subagent with invalid type."""
        # Create config with invalid type
        invalid_config = SubAgentConfig(
            name="test",
            task="Test task",
            subagent_type="invalid_type",
        )

        # Should raise ValueError (SubAgent won't be instantiated due to validation)
        with pytest.raises(ValueError, match="Invalid subagent configuration"):
            manager.create_subagent(invalid_config)

    def test_get_active_subagents_empty(self, manager):
        """Test getting active subagents when none exist."""
        active = manager.get_active_subagents()
        assert active == []

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_get_active_subagents(self, mock_subagent_class, manager, subagent_config):
        """Test getting active subagents."""
        # Create mock subagent
        mock_subagent = MagicMock(spec=SubAgent)
        mock_subagent.config = subagent_config
        mock_subagent_class.return_value = mock_subagent

        # Create subagent
        manager.create_subagent(subagent_config)

        # Get active subagents
        active = manager.get_active_subagents()
        assert len(active) == 1
        assert active[0] == mock_subagent

    def test_get_subagent_status_not_found(self, manager):
        """Test getting status of non-existent subagent."""
        status = manager.get_subagent_status("non_existent")
        assert status is None

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_get_subagent_status_active(self, mock_subagent_class, manager, subagent_config):
        """Test getting status of active subagent."""
        # Create mock subagent
        mock_subagent = MagicMock(spec=SubAgent)
        mock_subagent.config = subagent_config
        mock_subagent.get_status.return_value = "running"
        mock_subagent_class.return_value = mock_subagent

        # Create subagent
        manager.create_subagent(subagent_config)

        # Get status
        status = manager.get_subagent_status(subagent_config.name)
        assert status == "running"

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_get_subagent_status_completed(self, mock_subagent_class, manager, subagent_config):
        """Test getting status of completed subagent."""
        # Create mock subagent
        mock_subagent = MagicMock(spec=SubAgent)
        mock_subagent.config = subagent_config
        mock_subagent.get_status.return_value = "completed"
        mock_subagent_class.return_value = mock_subagent

        # Create and move to completed
        manager.create_subagent(subagent_config)
        del manager.active_subagents[subagent_config.name]
        manager.completed_subagents.append(mock_subagent)

        # Get status
        status = manager.get_subagent_status(subagent_config.name)
        assert status == "completed"

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_interrupt_subagent_success(self, mock_subagent_class, manager, subagent_config):
        """Test successfully interrupting a subagent."""
        # Create mock subagent
        mock_subagent = MagicMock(spec=SubAgent)
        mock_subagent.config = subagent_config
        mock_subagent.get_status.return_value = "running"
        mock_subagent_class.return_value = mock_subagent

        # Create subagent
        manager.create_subagent(subagent_config)

        # Interrupt
        result = manager.interrupt_subagent(subagent_config.name)

        # Verify interruption
        assert result is True
        mock_subagent.interrupt.assert_called_once()

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_interrupt_subagent_not_running(self, mock_subagent_class, manager, subagent_config):
        """Test interrupting subagent that's not running."""
        # Create mock subagent
        mock_subagent = MagicMock(spec=SubAgent)
        mock_subagent.config = subagent_config
        mock_subagent.get_status.return_value = "completed"
        mock_subagent_class.return_value = mock_subagent

        # Create subagent
        manager.create_subagent(subagent_config)

        # Try to interrupt
        result = manager.interrupt_subagent(subagent_config.name)

        # Verify no interruption
        assert result is False
        mock_subagent.interrupt.assert_not_called()

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_interrupt_subagent_not_found(self, mock_subagent_class, manager):
        """Test interrupting non-existent subagent."""
        result = manager.interrupt_subagent("non_existent")
        assert result is False

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_terminate_all(self, mock_subagent_class, manager):
        """Test terminating all active subagents."""
        # Create multiple mock subagents
        configs = [
            SubAgentConfig(name=f"test_{i}", task=f"Task {i}", subagent_type="general")
            for i in range(3)
        ]

        mock_subagents = []
        for config in configs:
            mock_subagent = MagicMock(spec=SubAgent)
            mock_subagent.config = config
            mock_subagent.get_status.return_value = "running"
            mock_subagent_class.return_value = mock_subagent
            manager.create_subagent(config)
            mock_subagents.append(mock_subagent)

        # Terminate all
        terminated_count = manager.terminate_all()

        # Verify all were terminated
        assert terminated_count == 3
        for mock_subagent in mock_subagents:
            mock_subagent.interrupt.assert_called_once()

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_terminate_all_partial(self, mock_subagent_class, manager):
        """Test terminating all with some not running."""
        # Create mock subagents
        configs = [
            SubAgentConfig(name="running", task="Running task", subagent_type="general"),
            SubAgentConfig(name="completed", task="Completed task", subagent_type="general"),
        ]

        for config in configs:
            mock_subagent = MagicMock(spec=SubAgent)
            mock_subagent.config = config
            mock_subagent.get_status.return_value = (
                "running" if config.name == "running" else "completed"
            )
            mock_subagent_class.return_value = mock_subagent
            manager.create_subagent(config)

        # Terminate all
        terminated_count = manager.terminate_all()

        # Verify only running one was terminated
        assert terminated_count == 1

    def test_get_statistics_empty(self, manager):
        """Test getting statistics with no subagents."""
        stats = manager.get_statistics()
        expected = {
            "active_count": 0,
            "completed_count": 0,
            "successful_count": 0,
            "failed_count": 0,
            "success_rate": 0,
            "avg_execution_time": 0,
            "total_iterations": 0,
            "max_concurrent": 3,
        }
        assert stats == expected

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_get_statistics_with_subagents(self, mock_subagent_class, manager, subagent_config):
        """Test getting statistics with subagents."""
        # Create mock subagents with results
        mock_results = [
            SubAgentResult(
                success=True,
                output="Success 1",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=False,
                output="",
                error="Error",
                iterations_used=3,
                execution_time=1.0,
            ),
            SubAgentResult(
                success=True,
                output="Success 2",
                error=None,
                iterations_used=7,
                execution_time=3.0,
            ),
        ]

        mock_subagents = []
        for i, result in enumerate(mock_results):
            mock_subagent = MagicMock(spec=SubAgent)
            mock_subagent.config = SubAgentConfig(
                name=f"test_{i}", task=f"Task {i}", subagent_type="general"
            )
            mock_subagent.result = result
            mock_subagent_class.return_value = mock_subagent
            manager.completed_subagents.append(mock_subagent)
            mock_subagents.append(mock_subagent)

        # Get statistics
        stats = manager.get_statistics()

        # Verify statistics
        assert stats["active_count"] == 0
        assert stats["completed_count"] == 3
        assert stats["successful_count"] == 2
        assert stats["failed_count"] == 1
        assert stats["success_rate"] == 2 / 3
        assert stats["avg_execution_time"] == 2.0  # (2.0 + 1.0 + 3.0) / 3
        assert stats["total_iterations"] == 15  # 5 + 3 + 7
        assert stats["max_concurrent"] == 3

    def test_clear_completed(self, manager):
        """Test clearing completed subagents."""
        # Add some completed subagents
        for i in range(3):
            mock_subagent = MagicMock(spec=SubAgent)
            manager.completed_subagents.append(mock_subagent)

        assert len(manager.completed_subagents) == 3

        # Clear
        manager.clear_completed()

        assert len(manager.completed_subagents) == 0

    def test_set_max_concurrent_valid(self, manager):
        """Test setting valid max concurrent."""
        manager.set_max_concurrent(5)
        assert manager.max_concurrent == 5

    def test_set_max_concurrent_invalid(self, manager):
        """Test setting invalid max concurrent."""
        with pytest.raises(ValueError, match="must be positive"):
            manager.set_max_concurrent(0)

        with pytest.raises(ValueError, match="must be positive"):
            manager.set_max_concurrent(-1)

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_run_sequential(self, mock_subagent_class, manager, subagent_config):
        """Test running subagents sequentially."""
        # Create mock subagents
        mock_results = [
            SubAgentResult(
                success=True,
                output="Result 1",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=True,
                output="Result 2",
                error=None,
                iterations_used=3,
                execution_time=1.0,
            ),
        ]

        mock_subagents = []
        for i, result in enumerate(mock_results):
            mock_subagent = MagicMock(spec=SubAgent)
            mock_subagent.config = SubAgentConfig(
                name=f"test_{i}", task=f"Task {i}", subagent_type="general"
            )
            mock_subagent.run.return_value = result
            mock_subagent_class.return_value = mock_subagent
            mock_subagents.append(mock_subagent)

        # Run sequentially
        results = manager.run_sequential(mock_subagents)

        # Verify results
        assert len(results) == 2
        assert results == mock_results

        # Verify subagents were called
        for mock_subagent in mock_subagents:
            mock_subagent.run.assert_called_once()

        # Verify completed tracking
        assert len(manager.completed_subagents) == 2
        assert len(manager.active_subagents) == 0

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_run_parallel(self, mock_subagent_class, manager, subagent_config):
        """Test running subagents in parallel."""
        # Create mock subagents
        mock_results = [
            SubAgentResult(
                success=True,
                output="Result 1",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=True,
                output="Result 2",
                error=None,
                iterations_used=3,
                execution_time=1.0,
            ),
        ]

        mock_subagents = []
        for i, result in enumerate(mock_results):
            mock_subagent = MagicMock(spec=SubAgent)
            mock_subagent.config = SubAgentConfig(
                name=f"test_{i}", task=f"Task {i}", subagent_type="general"
            )
            mock_subagent.run.return_value = result
            mock_subagent_class.return_value = mock_subagent
            mock_subagents.append(mock_subagent)

        # Run in parallel
        results = manager.run_parallel(mock_subagents, max_concurrent=2)

        # Verify results
        assert len(results) == 2
        assert results == mock_results

        # Verify subagents were called
        for mock_subagent in mock_subagents:
            mock_subagent.run.assert_called_once()

        # Verify completed tracking
        assert len(manager.completed_subagents) == 2
        assert len(manager.active_subagents) == 0

    def test_run_parallel_empty(self, manager):
        """Test running empty list in parallel."""
        results = manager.run_parallel([])
        assert results == []

    @patch("clippy.agent.subagent_manager.SubAgent")
    def test_run_parallel_with_exception(self, mock_subagent_class, manager, subagent_config):
        """Test running subagents in parallel with exception."""
        # Create mock subagents - one succeeds, one fails
        mock_success = MagicMock(spec=SubAgent)
        mock_success.config = SubAgentConfig(
            name="success",
            task="Success task",
            subagent_type="general",
        )
        mock_success.run.return_value = SubAgentResult(
            success=True,
            output="Success",
            error=None,
            iterations_used=5,
            execution_time=2.0,
        )

        mock_failure = MagicMock(spec=SubAgent)
        mock_failure.config = SubAgentConfig(
            name="failure",
            task="Failure task",
            subagent_type="general",
        )
        mock_failure.run.side_effect = Exception("Test error")

        mock_subagent_class.side_effect = [mock_success, mock_failure]

        # Create instances
        success_instance = mock_subagent_class()
        failure_instance = mock_subagent_class()

        # Run in parallel
        results = manager.run_parallel([success_instance, failure_instance])

        # Verify mixed results
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "Test error" in results[1].error

    @pytest.mark.asyncio
    async def test_run_parallel_async_success(self, manager):
        """Async execution should run subagents and track completion."""
        subagents = []
        expected_results = []
        for i in range(2):
            subagent = MagicMock(spec=SubAgent)
            subagent.config = SubAgentConfig(
                name=f"async_{i}", task=f"Async Task {i}", subagent_type="general"
            )
            result = SubAgentResult(
                success=True,
                output=f"Async result {i}",
                error=None,
                iterations_used=i + 1,
                execution_time=0.2,
            )
            subagent.run.return_value = result
            subagents.append(subagent)
            expected_results.append(result)
            manager.active_subagents[subagent.config.name] = subagent

        results = await manager.run_parallel_async(subagents, max_concurrent=2)

        assert results == expected_results
        assert len(manager.completed_subagents) == 2
        assert manager.active_subagents == {}

    @pytest.mark.asyncio
    async def test_run_parallel_async_exception(self, manager):
        """Async execution should convert exceptions to error results."""
        success_agent = MagicMock(spec=SubAgent)
        success_agent.config = SubAgentConfig(
            name="async_success", task="Task", subagent_type="general"
        )
        success_agent.run.return_value = SubAgentResult(
            success=True,
            output="ok",
            error=None,
            iterations_used=1,
            execution_time=0.1,
        )

        failing_agent = MagicMock(spec=SubAgent)
        failing_agent.config = SubAgentConfig(
            name="async_failure", task="Task", subagent_type="general"
        )
        failing_agent.run.side_effect = Exception("boom")

        manager.active_subagents.update(
            {
                success_agent.config.name: success_agent,
                failing_agent.config.name: failing_agent,
            }
        )

        results = await manager.run_parallel_async([success_agent, failing_agent], max_concurrent=2)

        assert results[0].success is True
        assert results[1].success is False
        assert "Async subagent execution failed: boom" in results[1].error
        assert manager.active_subagents == {}
        assert len(manager.completed_subagents) == 2

    def test_cache_operations(
        self,
        mock_parent_agent,
        mock_permission_manager,
        mock_executor,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Ensure cache helpers delegate to the cache implementation."""

        class FakeCache:
            def __init__(self) -> None:
                self.calls: list[tuple[str, tuple[Any, ...]]] = []
                self.enabled = True
                self.cleared = False

            def get(self, task, subagent_type, context):
                self.calls.append(("get", (task, subagent_type, context)))
                return {"cached": True}

            def put(self, task, subagent_type, data, context):
                self.calls.append(("put", (task, subagent_type, context, data)))

            def get_statistics(self):
                return {"enabled": self.enabled, "calls": len(self.calls)}

            def clear(self):
                self.cleared = True

            def enable(self):
                self.enabled = True

            def disable(self):
                self.enabled = False

        first_cache = FakeCache()
        second_cache = FakeCache()

        from clippy.agent import subagent_cache as cache_module

        cache_iter = iter([first_cache, second_cache])

        monkeypatch.setattr(cache_module, "get_global_cache", lambda: next(cache_iter))

        manager = SubAgentManager(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
            max_concurrent=2,
            enable_cache=True,
            enable_chaining=False,
        )

        cached = manager.check_cache("task", "general", {"k": "v"})
        assert cached == {"cached": True}

        manager.store_cache("task", "general", {"result": "data"}, {"k": "v"})
        stats = manager.get_cache_statistics()
        assert stats["enabled"] is True
        assert first_cache.cleared is False

        manager.clear_cache()
        assert first_cache.cleared is True

        manager.disable_cache()
        assert manager.cache_enabled is False
        assert first_cache.enabled is False

        manager._cache = None
        manager.enable_cache()
        assert manager.cache_enabled is True
        assert manager._cache is second_cache
        assert second_cache.enabled is True

    def test_chain_helpers(
        self,
        mock_parent_agent,
        mock_permission_manager,
        mock_executor,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Verify chain-related helpers delegate to the chainer."""

        class FakeChainer:
            def __init__(self) -> None:
                self.interrupted: list[str] = []
                self._active_chains = {"alpha": "node-alpha"}

            def get_chain_statistics(self):
                return {"enabled": True, "depth": 1}

            def get_active_chains(self):
                return {"alpha": {"depth": 0}}

            def interrupt_chain(self, name: str) -> bool:
                self.interrupted.append(name)
                return True

            def visualize_chain(self, node) -> str:
                return f"visual {node}"

        fake_chainer = FakeChainer()
        from clippy.agent import subagent_chainer as chainer_module

        monkeypatch.setattr(chainer_module, "get_global_chainer", lambda: fake_chainer)

        manager = SubAgentManager(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            executor=mock_executor,
            max_concurrent=2,
            enable_cache=False,
            enable_chaining=True,
        )

        assert manager.get_chain_statistics() == {"enabled": True, "depth": 1}
        assert manager.get_active_chains() == {"alpha": {"depth": 0}}
        assert manager.interrupt_chain("alpha") is True
        assert fake_chainer.interrupted == ["alpha"]
        assert manager.visualize_chain("alpha") == "visual node-alpha"
        assert manager.visualize_chain("missing").startswith("No active chain")
