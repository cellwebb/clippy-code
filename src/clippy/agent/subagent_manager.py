"""Subagent manager for coordinating multiple subagents."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

from ..executor import ActionExecutor
from ..permissions import PermissionManager

if TYPE_CHECKING:
    from .core import ClippyAgent

# Import SubAgent at runtime for actual usage and test mocking
from .subagent import SubAgent, SubAgentResult

logger = logging.getLogger(__name__)

# Default maximum concurrent subagents
DEFAULT_MAX_CONCURRENT = 3


class SubAgentManager:
    """
    Manages lifecycle and coordination of subagents.

    Responsibilities:
        - Create and track subagent instances
        - Coordinate parallel execution
        - Aggregate results from multiple subagents
        - Handle subagent failures and retries
        - Manage resource limits (max concurrent subagents)
    """

    def __init__(
        self,
        parent_agent: "ClippyAgent",
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        enable_cache: bool = True,
        enable_chaining: bool = True,
    ) -> None:
        """
        Initialize the SubAgentManager.

        Args:
            parent_agent: Reference to the main agent
            permission_manager: Permission manager instance
            executor: Action executor instance
            max_concurrent: Maximum number of concurrent subagents
            enable_cache: Whether to enable result caching
            enable_chaining: Whether to enable subagent chaining
        """
        self.parent_agent = parent_agent
        self.permission_manager = permission_manager
        self.executor = executor
        self.max_concurrent = max_concurrent
        self.cache_enabled = enable_cache
        self.enable_chaining = enable_chaining

        # Track active subagents
        self.active_subagents: dict[str, SubAgent] = {}
        self.completed_subagents: list[SubAgent] = []

        # Initialize advanced features
        self._cache = None
        self._chainer = None

        if enable_cache:
            from .subagent_cache import get_global_cache

            self._cache = get_global_cache()

        if enable_chaining:
            from .subagent_chainer import get_global_chainer

            self._chainer = get_global_chainer()

    def create_subagent(self, config: Any) -> SubAgent:
        """
        Create a new subagent instance.

        Args:
            config: Configuration for the subagent

        Returns:
            Created SubAgent instance
        """
        # Check for model override from user configuration
        from .subagent_config_manager import get_subagent_config_manager
        from .subagent_types import validate_subagent_config

        config_manager = get_subagent_config_manager()
        model_override = config_manager.get_model_override(config.subagent_type)

        # Apply model override if configured and not already set in config
        if model_override and (not hasattr(config, "model") or config.model is None):
            config.model = model_override
            logger.debug(f"Applied model override for {config.subagent_type}: {model_override}")

        # Validate configuration
        config_dict = {
            "name": config.name,
            "task": config.task,
            "subagent_type": config.subagent_type,
        }

        # Only add optional fields if they exist
        if hasattr(config, "timeout") and config.timeout is not None:
            config_dict["timeout"] = config.timeout
        if hasattr(config, "max_iterations") and config.max_iterations is not None:
            config_dict["max_iterations"] = config.max_iterations
        if hasattr(config, "allowed_tools") and config.allowed_tools is not None:
            config_dict["allowed_tools"] = config.allowed_tools

        is_valid, error_msg = validate_subagent_config(config_dict)
        if not is_valid:
            raise ValueError(f"Invalid subagent configuration: {error_msg}")

        # Create subagent
        subagent = SubAgent(
            config=config,
            parent_agent=self.parent_agent,
            permission_manager=self.permission_manager,
            executor=self.executor,
        )

        # Track active subagent
        self.active_subagents[config.name] = subagent

        logger.info(f"Created subagent '{config.name}' of type '{config.subagent_type}'")
        return subagent

    def run_sequential(self, subagents: list[SubAgent]) -> list[Any]:
        """
        Run multiple subagents sequentially.

        Args:
            subagents: List of subagents to run

        Returns:
            List of results in the same order as input
        """
        logger.info(f"Running {len(subagents)} subagents sequentially")
        results = []

        for subagent in subagents:
            logger.info(f"Running subagent '{subagent.config.name}'")
            result = subagent.run()
            results.append(result)

            # Move from active to completed
            if subagent.config.name in self.active_subagents:
                del self.active_subagents[subagent.config.name]
            self.completed_subagents.append(subagent)

        return results

    def run_parallel(
        self, subagents: list[SubAgent], max_concurrent: int | None = None
    ) -> list[Any]:
        """
        Run multiple subagents in parallel.

        Args:
            subagents: List of subagents to run
            max_concurrent: Maximum concurrent subagents (overrides instance default)

        Returns:
            List of results in the same order as input
        """
        if not subagents:
            return []

        max_workers = max_concurrent or self.max_concurrent
        if len(subagents) < max_workers:
            max_workers = len(subagents)

        logger.info(
            f"Running {len(subagents)} subagents in parallel with max {max_workers} concurrent"
        )

        # Use ThreadPoolExecutor for parallel execution
        results: list[Any] = [None] * len(subagents)  # Pre-allocate results list

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all subagent tasks
            future_to_index = {}
            for i, subagent in enumerate(subagents):
                logger.info(f"Submitting subagent '{subagent.config.name}' for parallel execution")
                future = executor.submit(subagent.run)
                future_to_index[future] = i

            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                subagent = subagents[index]

                try:
                    result = future.result()
                    results[index] = result
                    logger.info(f"Subagent '{subagent.config.name}' completed: {result.success}")
                except Exception as e:
                    logger.error(f"Subagent '{subagent.config.name}' failed with exception: {e}")

                    results[index] = SubAgentResult(
                        success=False,
                        output="",
                        error=f"Subagent execution failed: {str(e)}",
                        iterations_used=0,
                        execution_time=0.0,
                        metadata={
                            "subagent_name": subagent.config.name,
                            "subagent_type": subagent.config.subagent_type,
                            "failure_reason": "exception",
                        },
                    )

                # Move from active to completed
                if subagent.config.name in self.active_subagents:
                    del self.active_subagents[subagent.config.name]
                self.completed_subagents.append(subagent)

        # Ensure all results are filled (should always be true)
        if any(result is None for result in results):
            raise RuntimeError("Some subagent results were not filled")

        return results

    def get_active_subagents(self) -> list[SubAgent]:
        """
        Get list of currently active subagents.

        Returns:
            List of active subagent instances
        """
        return list(self.active_subagents.values())

    def get_subagent_status(self, name: str) -> str | None:
        """
        Get status of a specific subagent.

        Args:
            name: Name of the subagent

        Returns:
            Status string or None if not found
        """
        subagent = self.active_subagents.get(name)
        if subagent:
            return subagent.get_status()

        # Check completed subagents
        for completed in self.completed_subagents:
            if completed.config.name == name:
                return completed.get_status()

        return None

    def interrupt_subagent(self, name: str) -> bool:
        """
        Interrupt a running subagent.

        Args:
            name: Name of the subagent to interrupt

        Returns:
            True if subagent was found and interrupted, False otherwise
        """
        subagent = self.active_subagents.get(name)
        if subagent and subagent.get_status() == "running":
            subagent.interrupt()
            logger.info(f"Interrupted subagent '{name}'")
            return True
        return False

    def terminate_all(self) -> int:
        """
        Terminate all active subagents.

        Returns:
            Number of subagents terminated
        """
        terminated_count = 0
        for name, subagent in list(self.active_subagents.items()):
            if subagent.get_status() == "running":
                subagent.interrupt()
                terminated_count += 1
                logger.info(f"Terminated subagent '{name}'")

        return terminated_count

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about subagent execution.

        Returns:
            Dictionary with execution statistics
        """
        total_completed = len(self.completed_subagents)
        successful = sum(1 for s in self.completed_subagents if s.result and s.result.success)
        failed = total_completed - successful

        # Calculate average execution time
        execution_times = [
            s.result.execution_time
            for s in self.completed_subagents
            if s.result and s.result.execution_time > 0
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        # Calculate total iterations
        total_iterations = sum(
            s.result.iterations_used for s in self.completed_subagents if s.result
        )

        return {
            "active_count": len(self.active_subagents),
            "completed_count": total_completed,
            "successful_count": successful,
            "failed_count": failed,
            "success_rate": successful / total_completed if total_completed > 0 else 0,
            "avg_execution_time": avg_execution_time,
            "total_iterations": total_iterations,
            "max_concurrent": self.max_concurrent,
        }

    def clear_completed(self) -> None:
        """Clear the list of completed subagents to free memory."""
        self.completed_subagents.clear()
        logger.info("Cleared completed subagents list")

    def set_max_concurrent(self, max_concurrent: int) -> None:
        """
        Update the maximum number of concurrent subagents.

        Args:
            max_concurrent: New maximum concurrent subagents
        """
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")

        old_max = self.max_concurrent
        self.max_concurrent = max_concurrent
        logger.info(f"Updated max_concurrent from {old_max} to {max_concurrent}")

    async def run_parallel_async(
        self, subagents: list[SubAgent], max_concurrent: int | None = None
    ) -> list[Any]:
        """
        Run multiple subagents in parallel using asyncio.

        This is an async version of run_parallel for better integration
        with async codebases.

        Args:
            subagents: List of subagents to run
            max_concurrent: Maximum concurrent subagents

        Returns:
            List of results in the same order as input
        """
        if not subagents:
            return []

        max_workers = max_concurrent or self.max_concurrent
        if len(subagents) < max_workers:
            max_workers = len(subagents)

        logger.info(
            f"Running {len(subagents)} subagents asynchronously with max {max_workers} concurrent"
        )

        # Use asyncio to run subagent tasks in parallel
        semaphore = asyncio.Semaphore(max_workers)

        async def run_single_subagent(subagent: SubAgent) -> Any:
            async with semaphore:
                # Run the synchronous subagent.run() in a thread pool
                loop = asyncio.get_event_loop()
                try:
                    result = await loop.run_in_executor(None, subagent.run)
                    return result
                except Exception as e:
                    logger.error(f"Async subagent '{subagent.config.name}' failed: {e}")

                    return SubAgentResult(
                        success=False,
                        output="",
                        error=f"Async subagent execution failed: {str(e)}",
                        iterations_used=0,
                        execution_time=0.0,
                        metadata={
                            "subagent_name": subagent.config.name,
                            "subagent_type": subagent.config.subagent_type,
                            "failure_reason": "exception",
                        },
                    )
                finally:
                    # Move from active to completed
                    if subagent.config.name in self.active_subagents:
                        del self.active_subagents[subagent.config.name]
                    self.completed_subagents.append(subagent)

        # Run all subagents concurrently
        tasks = [run_single_subagent(subagent) for subagent in subagents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert any exceptions to error results
        final_results: list[Any] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                subagent = subagents[i]

                final_results.append(
                    SubAgentResult(
                        success=False,
                        output="",
                        error=f"Subagent execution exception: {str(result)}",
                        iterations_used=0,
                        execution_time=0.0,
                        metadata={
                            "subagent_name": subagent.config.name,
                            "subagent_type": subagent.config.subagent_type,
                            "failure_reason": "exception",
                        },
                    )
                )
            else:
                final_results.append(result)

        return final_results

    # Advanced Features Integration

    def check_cache(
        self,
        task: str,
        subagent_type: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Check cache for existing result.

        Args:
            task: The task description
            subagent_type: Type of subagent
            context: Additional context (optional)

        Returns:
            Cached result data or None if not found
        """
        if self._cache:
            return self._cache.get(task, subagent_type, context)
        return None

    def store_cache(
        self,
        task: str,
        subagent_type: str,
        result_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Store result in cache.

        Args:
            task: The task description
            subagent_type: Type of subagent
            result_data: Result data to cache
            context: Additional context (optional)
        """
        if self._cache:
            self._cache.put(task, subagent_type, result_data, context)

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        if self._cache:
            return self._cache.get_statistics()
        return {"enabled": False}

    def clear_cache(self) -> None:
        """Clear the cache."""
        if self._cache:
            self._cache.clear()

    def enable_cache(self) -> None:
        """Enable caching."""
        if not self._cache:
            from .subagent_cache import get_global_cache

            self._cache = get_global_cache()
            self._cache.enable()
        self.cache_enabled = True

    def disable_cache(self) -> None:
        """Disable caching."""
        if self._cache:
            self._cache.disable()
        self.cache_enabled = False

    def get_chain_statistics(self) -> dict[str, Any]:
        """Get chain execution statistics."""
        if self._chainer:
            return self._chainer.get_chain_statistics()
        return {"enabled": False}

    def get_active_chains(self) -> dict[str, dict[str, Any]]:
        """Get information about active chains."""
        if self._chainer:
            return self._chainer.get_active_chains()
        return {}

    def interrupt_chain(self, subagent_name: str) -> bool:
        """Interrupt a subagent chain."""
        if self._chainer:
            return self._chainer.interrupt_chain(subagent_name)
        return False

    def visualize_chain(self, subagent_name: str) -> str:
        """Visualize a chain starting from a subagent."""
        if self._chainer:
            node = self._chainer._active_chains.get(subagent_name)
            if node:
                return self._chainer.visualize_chain(node)
        return f"No active chain found for subagent: {subagent_name}"
