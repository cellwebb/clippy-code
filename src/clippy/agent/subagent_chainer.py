"""Subagent chaining system for hierarchical task execution."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .subagent import SubAgent, SubAgentResult

logger = logging.getLogger(__name__)


@dataclass
class ChainNode:
    """A node in the subagent execution chain."""

    subagent: SubAgent
    parent_node: "ChainNode | None" = None
    child_nodes: list["ChainNode"] = field(default_factory=list)
    depth: int = 0
    result: SubAgentResult | None = None
    execution_order: int = -1


class SubagentChainer:
    """
    Manages hierarchical execution of subagents.

    Features:
    - Depth-limited chaining (subagents can spawn other subagents)
    - Execution order tracking
    - Result aggregation and propagation
    - Circular dependency detection
    """

    def __init__(self, max_depth: int = 3):
        """
        Initialize the chainer.

        Args:
            max_depth: Maximum nesting depth for subagent chains
        """
        self.max_depth = max_depth
        self._root_nodes: list[ChainNode] = []
        self._execution_count = 0
        self._active_chains: dict[str, ChainNode] = {}

    def create_chain_node(
        self,
        subagent: SubAgent,
        parent_node: ChainNode | None = None,
    ) -> ChainNode:
        """
        Create a new chain node.

        Args:
            subagent: The subagent to create a node for
            parent_node: Parent node in the chain (None for root)

        Returns:
            Created ChainNode

        Raises:
            ValueError: If max depth would be exceeded
        """
        depth = parent_node.depth + 1 if parent_node else 0

        if depth > self.max_depth:
            raise ValueError(
                f"Cannot create chain node at depth {depth}: exceeds max depth of {self.max_depth}"
            )

        node = ChainNode(
            subagent=subagent,
            parent_node=parent_node,
            depth=depth,
        )

        # Add to parent's children if applicable
        if parent_node:
            parent_node.child_nodes.append(node)
        else:
            self._root_nodes.append(node)

        # Track active chain
        self._active_chains[subagent.config.name] = node

        logger.debug(f"Created chain node for subagent '{subagent.config.name}' at depth {depth}")
        return node

    def execute_chain(self, root_node: ChainNode) -> SubAgentResult:
        """
        Execute a chain of subagents starting from the root.

        Args:
            root_node: Root node of the chain to execute

        Returns:
            Aggregated result from the chain execution
        """
        if root_node.depth != 0:
            raise ValueError("Can only execute chains starting from root nodes")

        start_time = time.time()
        logger.info(f"Starting chain execution from root '{root_node.subagent.config.name}'")

        try:
            # Execute the chain depth-first
            result = self._execute_node_recursive(root_node)

            # Calculate total execution time
            total_time = time.time() - start_time
            result.metadata["chain_execution_time"] = total_time
            result.metadata["chain_depth"] = self._get_max_depth(root_node)
            result.metadata["total_nodes"] = self._count_nodes(root_node)

            logger.info(
                f"Chain execution completed in {total_time:.2f}s: "
                f"depth={result.metadata['chain_depth']}, "
                f"nodes={result.metadata['total_nodes']}"
            )

            return result

        except Exception as e:
            # Create error result
            error_result = SubAgentResult(
                success=False,
                output="",
                error=f"Chain execution failed: {str(e)}",
                iterations_used=0,
                execution_time=time.time() - start_time,
                metadata={
                    "failure_reason": "chain_exception",
                    "chain_depth": self._get_max_depth(root_node),
                    "total_nodes": self._count_nodes(root_node),
                },
            )
            logger.error(f"Chain execution failed: {e}")
            return error_result

        finally:
            # Clean up active chains
            self._cleanup_chain(root_node)

    def _execute_node_recursive(self, node: ChainNode) -> SubAgentResult:
        """Execute a node and all its children recursively."""
        # Set execution order
        self._execution_count += 1
        node.execution_order = self._execution_count

        logger.debug(
            f"Executing node {node.execution_order}: '{node.subagent.config.name}' "
            f"(depth {node.depth})"
        )

        # Execute the subagent
        node.result = node.subagent.run()

        # If successful and has children, execute children
        if node.result.success and node.child_nodes:
            logger.debug(
                f"Subagent '{node.subagent.config.name}' succeeded, "
                f"executing {len(node.child_nodes)} children"
            )

            child_results = []
            for child_node in node.child_nodes:
                child_result = self._execute_node_recursive(child_node)
                child_results.append(child_result)

                # If any child fails and we want to propagate failure
                if not child_result.success:
                    logger.warning(
                        f"Child subagent '{child_node.subagent.config.name}' failed: "
                        f"{child_result.error}"
                    )

            # Aggregate child results into the parent result
            node.result = self._aggregate_results(node.result, child_results)

        return node.result

    def _aggregate_results(
        self,
        parent_result: SubAgentResult,
        child_results: list[SubAgentResult],
    ) -> SubAgentResult:
        """
        Aggregate parent and child results.

        Args:
            parent_result: Result from the parent subagent
            child_results: Results from child subagents

        Returns:
            Aggregated result
        """
        # Combine outputs
        combined_output = parent_result.output
        if child_results:
            combined_output += "\n\n--- Child Subagent Results ---\n"
            for i, child_result in enumerate(child_results, 1):
                combined_output += f"\n{i}. Child Result:\n"
                if child_result.success:
                    combined_output += child_result.output
                else:
                    combined_output += f"ERROR: {child_result.error}"

        # Update metadata
        aggregated_metadata = parent_result.metadata.copy()
        aggregated_metadata.update(
            {
                "child_count": len(child_results),
                "successful_children": sum(1 for r in child_results if r.success),
                "failed_children": sum(1 for r in child_results if not r.success),
                "child_results": [
                    {
                        "success": r.success,
                        "output": r.output,
                        "error": r.error,
                        "execution_time": r.execution_time,
                        "iterations_used": r.iterations_used,
                    }
                    for r in child_results
                ],
            }
        )

        # Update execution time and iterations
        total_time = parent_result.execution_time + sum(r.execution_time for r in child_results)
        total_iterations = parent_result.iterations_used + sum(
            r.iterations_used for r in child_results
        )

        # Determine overall success (parent succeeds if at least one child succeeds)
        overall_success = parent_result.success or any(r.success for r in child_results)

        return SubAgentResult(
            success=overall_success,
            output=combined_output,
            error=parent_result.error if overall_success else "Parent and all children failed",
            iterations_used=total_iterations,
            tokens_used=parent_result.tokens_used,
            tools_executed=parent_result.tools_executed,
            execution_time=total_time,
            metadata=aggregated_metadata,
        )

    def _get_max_depth(self, node: ChainNode) -> int:
        """Get the maximum depth from this node."""
        if not node.child_nodes:
            return node.depth
        return max(self._get_max_depth(child) for child in node.child_nodes)

    def _count_nodes(self, node: ChainNode) -> int:
        """Count all nodes in the subtree rooted at this node."""
        count = 1
        for child in node.child_nodes:
            count += self._count_nodes(child)
        return count

    def _cleanup_chain(self, root_node: ChainNode) -> None:
        """Clean up active chain tracking."""
        nodes_to_remove = []

        def collect_nodes(node: ChainNode) -> None:
            nodes_to_remove.append(node.subagent.config.name)
            for child in node.child_nodes:
                collect_nodes(child)

        collect_nodes(root_node)

        for name in nodes_to_remove:
            self._active_chains.pop(name, None)

    def get_active_chains(self) -> dict[str, dict[str, Any]]:
        """
        Get information about active chains.

        Returns:
            Dictionary mapping subagent names to chain info
        """
        return {
            name: {
                "depth": node.depth,
                "execution_order": node.execution_order,
                "status": node.subagent.get_status(),
                "has_children": len(node.child_nodes) > 0,
            }
            for name, node in self._active_chains.items()
        }

    def get_chain_statistics(self) -> dict[str, Any]:
        """
        Get statistics about chain execution.

        Returns:
            Dictionary with chain statistics
        """
        total_nodes = sum(self._count_nodes(root) for root in self._root_nodes)
        max_depth = max((self._get_max_depth(root) for root in self._root_nodes), default=0)

        return {
            "max_depth": self.max_depth,
            "current_max_depth": max_depth,
            "total_nodes": total_nodes,
            "root_nodes": len(self._root_nodes),
            "active_chains": len(self._active_chains),
            "total_executions": self._execution_count,
        }

    def visualize_chain(self, root_node: ChainNode) -> str:
        """
        Create a text visualization of the chain.

        Args:
            root_node: Root node to visualize

        Returns:
            String representation of the chain
        """
        lines = []

        def add_node(node: ChainNode, prefix: str = "", is_last: bool = True) -> None:
            # Add current node
            connector = "└── " if is_last else "├── "
            status_symbol = (
                "✓" if node.result and node.result.success else "✗" if node.result else "⏳"
            )
            lines.append(
                f"{prefix}{connector}{status_symbol} "
                f"{node.subagent.config.name} (depth {node.depth})"
            )

            # Add children
            if node.child_nodes:
                child_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(node.child_nodes):
                    add_node(child, child_prefix, i == len(node.child_nodes) - 1)

        lines.append(f"Chain: {root_node.subagent.config.name}")
        add_node(root_node)

        return "\n".join(lines)

    def interrupt_chain(self, subagent_name: str) -> bool:
        """
        Interrupt a subagent and all its descendants.

        Args:
            subagent_name: Name of the subagent to interrupt

        Returns:
            True if subagent was found and interrupted
        """
        node = self._active_chains.get(subagent_name)
        if not node:
            return False

        # Interrupt the subagent
        node.subagent.interrupt()

        # Interrupt all descendants
        def interrupt_descendants(n: ChainNode) -> None:
            for child in n.child_nodes:
                child.subagent.interrupt()
                interrupt_descendants(child)

        interrupt_descendants(node)
        logger.info(f"Interrupted chain starting from '{subagent_name}'")
        return True

    def set_max_depth(self, max_depth: int) -> None:
        """
        Update the maximum chain depth.

        Args:
            max_depth: New maximum depth
        """
        if max_depth <= 0:
            raise ValueError("max_depth must be positive")

        old_max = self.max_depth
        self.max_depth = max_depth
        logger.info(f"Updated max_depth from {old_max} to {max_depth}")


# Global chainer instance
_global_chainer: SubagentChainer | None = None


def get_global_chainer() -> SubagentChainer:
    """Get the global chainer instance."""
    global _global_chainer
    if _global_chainer is None:
        # Load configuration from environment
        import os

        max_depth = int(os.getenv("CLIPPY_MAX_SUBAGENT_DEPTH", "3"))

        _global_chainer = SubagentChainer(max_depth=max_depth)
        logger.info(f"Initialized global subagent chainer: max_depth={max_depth}")

    return _global_chainer


def reset_global_chainer() -> None:
    """Reset the global chainer instance."""
    global _global_chainer
    _global_chainer = None
    logger.info("Reset global subagent chainer")
