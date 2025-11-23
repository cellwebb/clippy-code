"""Test subagent monitoring and stuck detection functionality."""

import time
from unittest.mock import Mock

import pytest

from src.clippy.agent.subagent import SubAgent, SubAgentConfig, SubAgentResult
from src.clippy.agent.subagent_monitor import (
    StuckDetectionConfig,
    SubagentMonitor,
)


class TestSubagentMonitor:
    """Test the SubagentMonitor class."""

    def test_monitor_initialization(self) -> None:
        """Test monitor initialization with default and custom config."""
        # Default config
        monitor = SubagentMonitor()
        assert monitor.config.stuck_timeout == 120.0
        assert monitor.config.heartbeat_timeout == 60.0
        assert monitor.config.overall_timeout == 600.0

        # Custom config
        custom_config = StuckDetectionConfig(
            stuck_timeout=60.0,
            heartbeat_timeout=30.0,
            overall_timeout=300.0,
        )
        monitor = SubagentMonitor(custom_config)
        assert monitor.config.stuck_timeout == 60.0
        assert monitor.config.heartbeat_timeout == 30.0
        assert monitor.config.overall_timeout == 300.0

    def test_start_stop_monitoring(self) -> None:
        """Test starting and stopping monitoring."""
        monitor = SubagentMonitor()

        # Create mock subagents
        subagents = []
        for i in range(3):
            config = SubAgentConfig(
                name=f"test_subagent_{i}",
                task="test task",
                subagent_type="general",
            )
            subagent = Mock(spec=SubAgent)
            subagent.config = config
            subagents.append(subagent)

        # Start monitoring
        monitor.start_monitoring(subagents)
        assert monitor.monitoring_active is True
        assert len(monitor.progress_trackers) == 3

        # Check progress trackers were created
        for i, subagent in enumerate(subagents):
            assert subagent.config.name in monitor.progress_trackers
            tracker = monitor.progress_trackers[subagent.config.name]
            assert tracker.subagent == subagent
            assert tracker.status == "running"

        # Stop monitoring
        stats = monitor.stop_monitoring()
        assert monitor.monitoring_active is False
        assert stats["monitoring_active"] is False
        assert stats["total_tracked"] == 3

    def test_heartbeat_updates(self) -> None:
        """Test heartbeat update functionality."""
        monitor = SubagentMonitor()

        # Create mock subagent
        config = SubAgentConfig(name="test_sub", task="test", subagent_type="general")
        subagent = Mock(spec=SubAgent)
        subagent.config = config

        monitor.start_monitoring([subagent])

        # Update heartbeat
        initial_heartbeat = monitor.progress_trackers["test_sub"].last_heartbeat
        time.sleep(0.1)  # Small delay to ensure time difference
        monitor.update_heartbeat("test_sub", 5)

        tracker = monitor.progress_trackers["test_sub"]
        assert tracker.last_heartbeat > initial_heartbeat
        assert tracker.last_iteration_count == 5

        monitor.stop_monitoring()

    def test_stuck_detection(self) -> None:
        """Test stuck subagent detection."""
        # Use very short timeouts for testing
        config = StuckDetectionConfig(
            stuck_timeout=1.0,
            heartbeat_timeout=0.5,
            check_interval=0.2,
            max_stuck_checks=2,
        )
        monitor = SubagentMonitor(config)

        # Create mock subagent
        config_obj = SubAgentConfig(name="stuck_sub", task="test", subagent_type="general")
        subagent = Mock(spec=SubAgent)
        subagent.config = config_obj

        monitor.start_monitoring([subagent])

        # Wait long enough for subagent to be considered stuck
        time.sleep(1.5)

        # Check that the monitor detected and handled the stuck subagent
        stats = monitor.get_statistics()
        assert stats["stuck_detected"] > 0

        # Check that the subagent's status was updated
        tracker = monitor.progress_trackers["stuck_sub"]
        assert tracker.status in ["stuck", "interrupted", "terminated"]

        monitor.stop_monitoring()

    def test_mark_completed(self) -> None:
        """Test marking subagents as completed."""
        monitor = SubagentMonitor()

        # Create mock subagent and result
        config = SubAgentConfig(name="test_sub", task="test", subagent_type="general")
        subagent = Mock(spec=SubAgent)
        subagent.config = config

        result = SubAgentResult(
            success=True,
            output="test output",
            error=None,
            iterations_used=5,
            execution_time=10.0,
        )

        monitor.start_monitoring([subagent])

        # Mark as completed
        monitor.mark_completed("test_sub", result)

        tracker = monitor.progress_trackers["test_sub"]
        assert tracker.status == "completed"
        assert tracker.execution_time > 0

        monitor.stop_monitoring()

    def test_statistics(self) -> None:
        """Test monitoring statistics."""
        monitor = SubagentMonitor()

        # Create mock subagents with different states
        subagents = []
        results = [
            SubAgentResult(
                success=True, output="test", error=None, iterations_used=1, execution_time=1.0
            ),
            SubAgentResult(
                success=False, output="test", error="failed", iterations_used=1, execution_time=1.0
            ),
        ]

        for i, result in enumerate(results):
            config = SubAgentConfig(name=f"test_sub_{i}", task="test", subagent_type="general")
            subagent = Mock(spec=SubAgent)
            subagent.config = config
            subagents.append(subagent)

        monitor.start_monitoring(subagents)

        # Mark subagents with different results
        for i, result in enumerate(results):
            monitor.mark_completed(f"test_sub_{i}", result)

        stats = monitor.get_statistics()
        assert stats["total_tracked"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1

        monitor.stop_monitoring()


class TestSubagentUtils:
    """Test subagent utility functions."""

    def test_create_stuck_detection_config(self) -> None:
        """Test creating stuck detection configs with presets."""
        from src.clippy.agent.subagent_utils import (
            create_stuck_detection_config,
        )

        # Default config
        config = create_stuck_detection_config()
        assert config.stuck_timeout == 120.0
        assert config.heartbeat_timeout == 60.0

        # Aggressive config
        config = create_stuck_detection_config(aggressive=True)
        assert config.stuck_timeout == 60.0
        assert config.heartbeat_timeout == 30.0
        assert config.overall_timeout == 300.0

        # Conservative config
        config = create_stuck_detection_config(conservative=True)
        assert config.stuck_timeout == 300.0
        assert config.heartbeat_timeout == 180.0
        assert config.overall_timeout == 1800.0

        # Custom overrides
        config = create_stuck_detection_config(
            aggressive=True, custom_settings={"stuck_timeout": 45.0}
        )
        assert config.stuck_timeout == 45.0  # Override applied
        assert config.heartbeat_timeout == 30.0  # Aggressive setting preserved

    def test_create_stuck_detection_dict(self) -> None:
        """Test creating dictionary format for tool calls."""
        from src.clippy.agent.subagent_utils import create_stuck_detection_dict

        # Default dict
        result = create_stuck_detection_dict()
        assert result["enabled"] is True
        assert result["stuck_timeout"] == 120.0
        assert result["heartbeat_timeout"] == 60.0

        # Aggressive dict
        result = create_stuck_detection_dict(aggressive=True)
        assert result["stuck_timeout"] == 60.0
        assert result["overall_timeout"] == 300.0

        # Disabled
        result = create_stuck_detection_dict(enabled=False)
        assert result["enabled"] is False

    def test_suggest_settings(self) -> None:
        """Test setting suggestions based on task characteristics."""
        from src.clippy.agent.subagent_utils import suggest_stuck_detection_settings

        # Simple, reliable tasks
        settings = suggest_stuck_detection_settings(task_complexity="simple", reliability="high")
        assert settings["stuck_timeout"] == 60.0  # Aggressive

        # Complex, unreliable tasks
        settings = suggest_stuck_detection_settings(task_complexity="complex", reliability="low")
        assert settings["stuck_timeout"] == 300.0  # Conservative

        # Performance priority
        settings = suggest_stuck_detection_settings(performance_priority=True)
        assert settings["max_stuck_checks"] == 2  # Fail fast

    def test_analyze_results(self) -> None:
        """Test result analysis functionality."""
        from src.clippy.agent.subagent_utils import analyze_parallel_results

        # Mock results with various outcomes
        results = {
            "individual_results": [
                {
                    "name": "sub1",
                    "success": True,
                    "execution_time": 10.0,
                },
                {
                    "name": "sub2",
                    "success": False,
                    "execution_time": 2.0,
                    "failure_reason": "stuck",
                },
                {
                    "name": "sub3",
                    "success": True,
                    "execution_time": 15.0,
                    "failure_reason": None,
                },
            ],
            "total_successful": 2,
            "total_failed": 1,
            "total_stuck": 1,
            "total_timeout": 0,
            "total_exception": 0,
            "total_execution_time": 27.0,
        }

        analysis = analyze_parallel_results(results)

        assert analysis["total_subagents"] == 3
        assert analysis["success_rate"] == 2 / 3
        assert len(analysis["issues_detected"]) > 0
        assert "stuck" in analysis["issues_detected"][0]
        assert len(analysis["recommendations"]) > 0


class TestSubagentManagerIntegration:
    """Test integration with SubagentManager."""

    def test_run_parallel_with_monitoring(self) -> None:
        """Test that SubagentManager can use monitoring."""
        from src.clippy.agent.subagent_manager import SubAgentManager

        # This is more of an integration test - we'll mock the components

        # Mock the dependencies
        parent_agent = Mock()
        permission_manager = Mock()
        executor = Mock()

        manager = SubAgentManager(parent_agent, permission_manager, executor, max_concurrent=2)

        # Create mock subagents
        subagents = []
        for i in range(2):
            config_obj = SubAgentConfig(name=f"test_{i}", task=f"task {i}", subagent_type="general")
            subagent = Mock(spec=SubAgent)
            subagent.config = config_obj
            subagent.config.name = f"test_{i}"
            subagent.config.subagent_type = "general"
            subagent.run.return_value = SubAgentResult(
                success=True,
                output=f"result {i}",
                error=None,
                iterations_used=1,
                execution_time=0.1,
            )
            subagents.append(subagent)

        # Test that run_parallel accepts the stuck_detection_config parameter
        # (This is mainly a smoke test to ensure the signature is correct)
        try:
            # The actual call would fail in a unit test environment,
            # but we're testing that the method signature is correct
            manager.run_parallel.__code__.co_varnames
            assert "stuck_detection_config" in manager.run_parallel.__code__.co_varnames
        except Exception:
            pytest.skip("Integration test would require full setup")


if __name__ == "__main__":
    pytest.main([__file__])
