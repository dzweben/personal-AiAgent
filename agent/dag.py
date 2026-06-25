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


def layers(nodes: list[Node]) -> list[list[str]]:
    """group node keys into dependency layers: every node in a layer can run concurrently."""
    by_key = {n.key: n for n in nodes}
    topological_order(nodes)  # validates (cycles / unknown deps) before we layer
    depth: dict[str, int] = {}

    def node_depth(key: str) -> int:
        if key in depth:
            return depth[key]
        deps = by_key[key].deps
        depth[key] = 0 if not deps else 1 + max(node_depth(d) for d in deps)
        return depth[key]

    out: list[list[str]] = []
    for n in nodes:
        d = node_depth(n.key)
        while len(out) <= d:
            out.append([])
        out[d].append(n.key)
    return out


def run_dag(
    nodes: list[Node], *, on_error: str = "skip", parallel: bool = False, workers: int = 8
) -> DAGResult:
    """execute the graph in dependency order, feeding each node its dependencies' results.

    on_error="skip" records a node's failure (and skips anything that needed it); on_error="raise"
    propagates the exception. a node downstream of a failed/ skipped dependency is itself skipped.
    with parallel=True, independent nodes in the same dependency layer run concurrently.
    """
    by_key = {n.key: n for n in nodes}
    res = DAGResult(order=topological_order(nodes))

    def run_one(key: str):
        node = by_key[key]
        missing = [d for d in node.deps if d not in res.results]
        if missing:
            res.failed[key] = f"skipped: upstream {missing} unavailable"
            return
        dep_results = {d: res.results[d] for d in node.deps}
        try:
            res.results[key] = node.run(dep_results)
        except Exception as exc:  # noqa: BLE001 - behaviour is caller-selected
            if on_error == "raise":
                raise
            res.failed[key] = f"error: {exc}"

    if not parallel:
        for key in res.order:
            run_one(key)
        return res

    from agent.parallel import map_parallel

    for layer in layers(nodes):
        # within a layer there are no inter-dependencies, so it's safe to run them at once
        map_parallel(run_one, layer, workers=workers, on_error=on_error)
    return res
