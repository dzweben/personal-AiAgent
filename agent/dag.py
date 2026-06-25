"""a dependency-aware task-graph executor.

the planner gives you nodes with dependencies; this runs them. it topologically sorts the
graph, executes each node once its dependencies are done (passing their results in), detects
cycles, and surfaces failures without bringing the whole graph down. it's the generic engine
the deep-research pipeline rides on -- and it's pure python, so it tests offline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class CycleError(ValueError):
    """raised when the task graph has a dependency cycle and can't be ordered."""


@dataclass
class Node:
    key: str
    run: Callable[[dict[str, Any]], Any]  # receives {dep_key: result} for its dependencies
    deps: list[str] = field(default_factory=list)


@dataclass
class DAGResult:
    results: dict[str, Any] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.failed


def topological_order(nodes: list[Node]) -> list[str]:
    """return node keys in dependency order. raises CycleError if that's impossible."""
    by_key = {n.key: n for n in nodes}
    state: dict[str, int] = {}  # 0=unseen, 1=visiting, 2=done
    order: list[str] = []

    def visit(key: str, trail: tuple[str, ...]):
        if state.get(key) == 2:
            return
        if state.get(key) == 1:
            raise CycleError(f"dependency cycle: {' -> '.join((*trail, key))}")
        state[key] = 1
        for dep in by_key[key].deps:
            if dep not in by_key:
                raise ValueError(f"node {key!r} depends on unknown node {dep!r}")
            visit(dep, (*trail, key))
        state[key] = 2
        order.append(key)

    for n in nodes:
        visit(n.key, ())
    return order


def run_dag(nodes: list[Node], *, on_error: str = "skip") -> DAGResult:
    """execute the graph in dependency order, feeding each node its dependencies' results.

    on_error="skip" records a node's failure (and skips anything that needed it); on_error="raise"
    propagates the exception. a node downstream of a failed/ skipped dependency is itself skipped.
    """
    order = topological_order(nodes)
    by_key = {n.key: n for n in nodes}
    res = DAGResult(order=order)

    for key in order:
        node = by_key[key]
        missing = [d for d in node.deps if d not in res.results]
        if missing:
            res.failed[key] = f"skipped: upstream {missing} unavailable"
            continue
        dep_results = {d: res.results[d] for d in node.deps}
        try:
            res.results[key] = node.run(dep_results)
        except Exception as exc:  # noqa: BLE001 - behaviour is caller-selected
            if on_error == "raise":
                raise
            res.failed[key] = f"error: {exc}"
    return res
