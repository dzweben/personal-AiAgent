"""tests for the DAG executor."""

from __future__ import annotations

import pytest

from agent.dag import CycleError, Node, run_dag, topological_order


def test_topological_order_respects_deps():
    nodes = [
        Node("c", lambda d: None, deps=["a", "b"]),
        Node("a", lambda d: None),
        Node("b", lambda d: None, deps=["a"]),
    ]
    order = topological_order(nodes)
    assert order.index("a") < order.index("b") < order.index("c")


def test_run_dag_feeds_dependency_results():
    nodes = [
        Node("a", lambda d: 10),
        Node("b", lambda d: 5),
        Node("sum", lambda d: d["a"] + d["b"], deps=["a", "b"]),
    ]
    res = run_dag(nodes)
    assert res.results["sum"] == 15
    assert res.ok


def test_cycle_is_detected():
    nodes = [Node("x", lambda d: 1, deps=["y"]), Node("y", lambda d: 1, deps=["x"])]
    with pytest.raises(CycleError):
        run_dag(nodes)


def test_unknown_dependency_raises():
    with pytest.raises(ValueError):
        topological_order([Node("a", lambda d: 1, deps=["ghost"])])


def test_failure_skips_downstream_but_not_siblings():
    def boom(d):
        raise RuntimeError("kaboom")

    nodes = [
        Node("ok", lambda d: "fine"),
        Node("bad", boom),
        Node("needs_bad", lambda d: "never", deps=["bad"]),
        Node("needs_ok", lambda d: d["ok"].upper(), deps=["ok"]),
    ]
    res = run_dag(nodes, on_error="skip")
    assert res.results["ok"] == "fine"
    assert res.results["needs_ok"] == "FINE"
    assert "bad" in res.failed and "needs_bad" in res.failed
    assert not res.ok


def test_on_error_raise_propagates():
    def boom(d):
        raise RuntimeError("kaboom")

    with pytest.raises(RuntimeError):
        run_dag([Node("bad", boom)], on_error="raise")


def test_layers_groups_independent_nodes():
    nodes = [
        Node("a", lambda d: 1),
        Node("b", lambda d: 1),
        Node("c", lambda d: 1, deps=["a", "b"]),
    ]
    from agent.dag import layers

    lyrs = layers(nodes)
    assert set(lyrs[0]) == {"a", "b"}
    assert lyrs[1] == ["c"]


def test_parallel_run_matches_sequential():
    nodes = [
        Node("a", lambda d: 2),
        Node("b", lambda d: 3),
        Node("sum", lambda d: d["a"] + d["b"], deps=["a", "b"]),
    ]
    seq = run_dag(nodes, parallel=False)
    par = run_dag(nodes, parallel=True, workers=4)
    assert seq.results == par.results
    assert par.results["sum"] == 5


def test_parallel_is_faster_for_independent_work():
    import time

    nodes = [Node(f"s{i}", lambda d: time.sleep(0.1)) for i in range(6)]
    start = time.time()
    run_dag(nodes, parallel=True, workers=6)
    assert time.time() - start < 0.35  # 6 x 0.1s sequentially would be 0.6s
