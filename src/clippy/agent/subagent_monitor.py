"""Subagent monitoring system for detecting stuck subagents and automatic recovery."""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .subagent import SubAgent, SubAgentResult

logger = logging.getLogger(__name__)


@dataclass
class SubagentProgress:
    """Track progress of a subagent execution."""

    subagent: "SubAgent"
    start_time: float
    last_heartbeat: float
    last_iteration_count: int = 0
    last_progress_time: float = 0.0
    status: str = "running"
    warnings_sent: list[str] = field(default_factory=list)
    stuck_checks: int = 0
    execution_time: float = 0.0


@dataclass
class StuckDetectionConfig:
    """Configuration for stuck subagent detection."""

    # How long without any progress before considering stuck (seconds)
    stuck_timeout: float = 120.0

    # How long without heartbeat before considering stuck (seconds)
    heartbeat_timeout: float = 60.0

    # How many stuck checks before taking action
    max_stuck_checks: int = 3

    # Overall timeout for parallel execution (seconds)
    overall_timeout: float = 600.0

    # Whether to automatically retry stuck subagents
    auto_retry: bool = True

    # Maximum number of retry attempts
    max_retries: int = 2

    # Whether to terminate stuck subagents
    auto_terminate: bool = True

    # Progress check interval (seconds)
    check_interval: float = 10.0


class SubagentMonitor:
    """
    Monitor subagent execution and detect stuck subagents.

    Features:
    - Progress monitoring via heartbeats
    - Stuck subagent detection
    - Automatic recovery strategies
    - Partial result preservation
    """

    def __init__(self, config: StuckDetectionConfig | None = None) -> None:
        """
        Initialize the subagent monitor.

        Args:
            config: Configuration for stuck detection
        """
        self.config = config or StuckDetectionConfig()
        self.progress_trackers: dict[str, SubagentProgress] = {}
        self.monitoring_active = False
        self.monitor_thread: threading.Thread | None = None
        self.lock = threading.RLock()

        # Statistics
        self.total_detected_stuck = 0
        self.total_recovered = 0
        self.total_terminated = 0

    def start_monitoring(self, subagents: list["SubAgent"]) -> None:
        """
        Start monitoring a list of subagents.

        Args:
            subagents: List of subagents to monitor
        """
        with self.lock:
            if self.monitoring_active:
                logger.warning("Monitoring is already active")
                return

            # Initialize progress tracking for each subagent
            current_time = time.time()
            for subagent in subagents:
                self.progress_trackers[subagent.config.name] = SubagentProgress(
                    subagent=subagent,
                    start_time=current_time,
                    last_heartbeat=current_time,
                    last_progress_time=current_time,
                    status="running",
                )

            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info(f"Started monitoring {len(subagents)} subagents")

    def stop_monitoring(self) -> dict[str, Any]:
        """
        Stop monitoring and return final statistics.

        Returns:
            Dictionary with monitoring statistics
        """
        with self.lock:
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5.0)
                self.monitor_thread = None

            stats = self.get_statistics()
            logger.info("Stopped subagent monitoring")
            return stats

    def update_heartbeat(self, subagent_name: str, iteration_count: int = 0) -> None:
        """
        Update heartbeat for a subagent (called by subagent during execution).

        Args:
            subagent_name: Name of the subagent
            iteration_count: Current iteration count
        """
        with self.lock:
            if subagent_name in self.progress_trackers:
                tracker = self.progress_trackers[subagent_name]
                current_time = time.time()

                # Update heartbeat
                tracker.last_heartbeat = current_time

                # Check for progress (iteration count changed)
                if iteration_count > tracker.last_iteration_count:
                    tracker.last_iteration_count = iteration_count
                    tracker.last_progress_time = current_time
                    tracker.stuck_checks = 0  # Reset stuck checks on progress

                tracker.execution_time = current_time - tracker.start_time

    def mark_completed(self, subagent_name: str, result: "SubAgentResult") -> None:
        """
        Mark a subagent as completed.

        Args:
            subagent_name: Name of the subagent
            result: Final result from the subagent
        """
        with self.lock:
            if subagent_name in self.progress_trackers:
                tracker = self.progress_trackers[subagent_name]
                tracker.status = "completed" if result.success else "failed"
                tracker.execution_time = time.time() - tracker.start_time

    def get_stuck_subagents(self) -> list[str]:
        """
        Get list of currently detected stuck subagents.

        Returns:
            List of stuck subagent names
        """
        with self.lock:
            stuck = []
            current_time = time.time()

            for name, tracker in self.progress_trackers.items():
                if tracker.status == "running":
                    # Check heartbeat timeout
                    if current_time - tracker.last_heartbeat > self.config.heartbeat_timeout:
                        stuck.append(name)
                    # Check progress timeout
                    elif current_time - tracker.last_progress_time > self.config.stuck_timeout:
                        stuck.append(name)
                    # Check overall timeout
                    elif tracker.execution_time > self.config.overall_timeout:
                        stuck.append(name)

            return stuck

    def get_statistics(self) -> dict[str, Any]:
        """
        Get monitoring statistics.

        Returns:
            Dictionary with monitoring statistics
        """
        with self.lock:
            running = sum(1 for t in self.progress_trackers.values() if t.status == "running")
            completed = sum(1 for t in self.progress_trackers.values() if t.status == "completed")
            failed = sum(1 for t in self.progress_trackers.values() if t.status == "failed")

            return {
                "monitoring_active": self.monitoring_active,
                "total_tracked": len(self.progress_trackers),
                "running": running,
                "completed": completed,
                "failed": failed,
                "stuck_detected": self.total_detected_stuck,
                "recovered": self.total_recovered,
                "terminated": self.total_terminated,
                "stuck_subagents": self.get_stuck_subagents(),
            }

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Subagent monitoring loop started")

        while self.monitoring_active:
            try:
                self._check_progress()
                time.sleep(self.config.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.config.check_interval)

        logger.info("Subagent monitoring loop stopped")

    def _check_progress(self) -> None:
        """Check progress of all tracked subagents."""
        with self.lock:
            if not self.monitoring_active:
                return

            current_time = time.time()
            stuck_subagents = []

            for name, tracker in list(self.progress_trackers.items()):
                if tracker.status != "running":
                    continue

                # Check for stuck conditions
                is_stuck = False
                reason = ""

                # Check heartbeat timeout
                if current_time - tracker.last_heartbeat > self.config.heartbeat_timeout:
                    is_stuck = True
                    reason = f"heartbeat timeout ({self.config.heartbeat_timeout}s)"

                # Check progress timeout
                elif current_time - tracker.last_progress_time > self.config.stuck_timeout:
                    is_stuck = True
                    reason = f"no progress for {self.config.stuck_timeout}s"

                # Check overall timeout
                elif tracker.execution_time > self.config.overall_timeout:
                    is_stuck = True
                    reason = f"overall timeout ({self.config.overall_timeout}s)"

                if is_stuck:
                    tracker.stuck_checks += 1

                    # Log warning (only once per stuck check)
                    warning_key = f"stuck_{tracker.stuck_checks}"
                    if warning_key not in tracker.warnings_sent:
                        logger.warning(
                            f"Subagent '{name}' appears stuck ({reason}) - "
                            f"check {tracker.stuck_checks}/{self.config.max_stuck_checks}"
                        )
                        tracker.warnings_sent.append(warning_key)

                    # Take action if max stuck checks reached
                    if tracker.stuck_checks >= self.config.max_stuck_checks:
                        stuck_subagents.append((name, reason))
                        tracker.status = "stuck"
                        self.total_detected_stuck += 1

            # Handle stuck subagents
            for name, reason in stuck_subagents:
                self._handle_stuck_subagent(name, reason)

    def _handle_stuck_subagent(self, subagent_name: str, reason: str) -> None:
        """
        Handle a detected stuck subagent.

        Args:
            subagent_name: Name of the stuck subagent
            reason: Reason why it's considered stuck
        """
        logger.error(f"Taking action on stuck subagent '{subagent_name}': {reason}")

        with self.lock:
            tracker = self.progress_trackers.get(subagent_name)
            if not tracker:
                return

            subagent = tracker.subagent

            # Try to interrupt first
            try:
                logger.info(f"Interrupting stuck subagent '{subagent_name}'")
                subagent.interrupt()
                tracker.status = "interrupted"

                if self.config.auto_terminate:
                    logger.info(f"Terminating stuck subagent '{subagent_name}'")
                    # The interrupt should be sufficient, but let's mark it as terminated
                    tracker.status = "terminated"
                    self.total_terminated += 1

            except Exception as e:
                logger.error(f"Failed to interrupt stuck subagent '{subagent_name}': {e}")
                tracker.status = "failed"

            self.total_recovered += 1


class SubagentHeartbeatMixin:
    """
    Mixin for subagents to provide heartbeat functionality.

    This mixin should be added to SubAgent to enable progress monitoring.

    Note: This is a future enhancement placeholder. The current implementation
    uses monitoring without requiring modifications to the SubAgent class.
    """

    def set_monitor(self, monitor: SubagentMonitor) -> None:
        """
        Set the monitor for this subagent.

        Args:
            monitor: The monitor instance
        """
        self._monitor = monitor

    def _send_heartbeat(self) -> None:
        """Send heartbeat to monitor if available."""
        # Placeholder implementation - current monitoring doesn't require heartbeat
        # This would be used in a future enhancement to provide more detailed progress tracking
        pass
