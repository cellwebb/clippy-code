"""Tests for the subagent chaining system."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from clippy.agent.subagent import SubAgentResult
from clippy.agent.subagent_chainer import ChainNode, SubagentChainer


@dataclass
class DummyResultSpec:
    """Configuration describing the outcome of a dummy subagent."""

    success: bool = True
    output: str = "ok"
    error: str | None = None
    execution_time: float = 0.1
    iterations_used: int = 1
    metadata: dict[str, str] | None = None


class DummySubAgent:
    """Minimal subagent implementation for exercising the chainer."""

    def __init__(self, name: str, spec: DummyResultSpec | None = None) -> None:
        self.config = SimpleNamespace(name=name)
        self.status = "pending"
        self.interrupted = False
        self._run_calls = 0
        spec = spec or DummyResultSpec()
        self._result = SubAgentResult(
            success=spec.success,
            output=spec.output,
            error=spec.error,
            iterations_used=spec.iterations_used,
            execution_time=spec.execution_time,
            metadata=spec.metadata or {"origin": name},
        )

    def run(self) -> SubAgentResult:
        self._run_calls += 1
        if self.interrupted:
            self.status = "interrupted"
            return SubAgentResult(
                success=False,
                output="",
                error="Interrupted",
                iterations_used=0,
                execution_time=0.0,
                metadata={"origin": self.config.name},
            )

        self.status = "completed" if self._result.success else "failed"
        return self._result

    def get_status(self) -> str:
        return self.status

    def interrupt(self) -> None:
        self.interrupted = True
        self.status = "interrupted"


def _build_chain(chainer: SubagentChainer) -> tuple[ChainNode, DummySubAgent, DummySubAgent]:
    parent = DummySubAgent("root", DummyResultSpec(metadata={"level": "root"}))
    child = DummySubAgent("child", DummyResultSpec(metadata={"level": "child"}))
    root_node = chainer.create_chain_node(parent)
    chainer.create_chain_node(child, parent_node=root_node)
    return root_node, parent, child


def test_create_chain_respects_depth_limit() -> None:
    chainer = SubagentChainer(max_depth=1)
    root_node, _, _ = _build_chain(chainer)

    with pytest.raises(ValueError):
        chainer.create_chain_node(DummySubAgent("grandchild"), parent_node=root_node.child_nodes[0])


def test_execute_chain_aggregates_child_results() -> None:
    chainer = SubagentChainer(max_depth=3)
    root_node, parent, child = _build_chain(chainer)

    result = chainer.execute_chain(root_node)

    assert result.success is True
    assert "--- Child Subagent Results ---" in result.output
    assert result.metadata["child_count"] == 1
    assert result.metadata["successful_children"] == 1
    assert result.metadata["failed_children"] == 0
    assert result.metadata["child_results"][0]["success"] is True
    assert result.metadata["chain_depth"] == 1
    assert result.metadata["total_nodes"] == 2
    assert chainer.get_active_chains() == {}
    assert parent.status == "completed"
    assert child.status == "completed"


def test_execute_chain_failure_when_all_nodes_fail() -> None:
    chainer = SubagentChainer(max_depth=3)
    parent = DummySubAgent(
        "root",
        DummyResultSpec(success=False, error="boom", metadata={"level": "root"}),
    )
    child = DummySubAgent(
        "child",
        DummyResultSpec(success=False, error="child boom", metadata={"level": "child"}),
    )

    root_node = chainer.create_chain_node(parent)
    chainer.create_chain_node(child, parent_node=root_node)

    result = chainer.execute_chain(root_node)

    assert result.success is False
    assert result.error == "boom"
    assert child._run_calls == 0


def test_get_active_chains_before_execution() -> None:
    chainer = SubagentChainer(max_depth=2)
    root_node, parent, child = _build_chain(chainer)

    info = chainer.get_active_chains()
    assert set(info.keys()) == {"root", "child"}
    assert info["root"]["depth"] == 0
    assert info["child"]["depth"] == 1
    assert info["root"]["status"] == parent.get_status()
    assert info["child"]["has_children"] is False

    # execute to ensure cleanup reduces active chains
    chainer.execute_chain(root_node)
    assert chainer.get_active_chains() == {}


def test_interrupt_chain_propagates_to_descendants() -> None:
    chainer = SubagentChainer(max_depth=2)
    root_node, parent, child = _build_chain(chainer)

    interrupted = chainer.interrupt_chain("root")

    assert interrupted is True
    assert parent.interrupted is True
    assert child.interrupted is True
    assert parent.status == "interrupted"
    assert child.status == "interrupted"


def test_chain_statistics_reflect_structure() -> None:
    chainer = SubagentChainer(max_depth=5)
    root_node, _, _ = _build_chain(chainer)

    stats_before = chainer.get_chain_statistics()
    assert stats_before["max_depth"] == 5
    assert stats_before["current_max_depth"] == 1
    assert stats_before["total_nodes"] == 2
    assert stats_before["root_nodes"] == 1

    chainer.execute_chain(root_node)

    stats_after = chainer.get_chain_statistics()
    assert stats_after["total_executions"] >= 2  # parent + child


def test_set_max_depth_validates_input() -> None:
    chainer = SubagentChainer(max_depth=3)

    with pytest.raises(ValueError):
        chainer.set_max_depth(0)

    chainer.set_max_depth(4)
    assert chainer.max_depth == 4
