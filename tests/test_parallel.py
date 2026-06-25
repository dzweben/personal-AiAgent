"""tests for the parallel execution primitive."""

from __future__ import annotations

import time

import pytest

from agent.parallel import gather, map_parallel


def test_preserves_order():
    assert map_parallel(lambda x: x * 10, [1, 2, 3, 4]) == [10, 20, 30, 40]


def test_empty_input():
    assert map_parallel(lambda x: x, []) == []


def test_error_isolation_default_none():
    out = map_parallel(lambda x: 1 // x, [1, 2, 0, 4])
    assert out == [1, 0, None, 0]  # the divide-by-zero became None


def test_error_raise_mode():
    with pytest.raises(ZeroDivisionError):
        map_parallel(lambda x: 1 // x, [1, 0], on_error="raise")


def test_actually_runs_concurrently():
    start = time.time()
    map_parallel(lambda x: time.sleep(0.1), range(8), workers=8)
    # 8 x 0.1s sequentially would be 0.8s; concurrently it should be well under 0.4s
    assert time.time() - start < 0.4


def test_gather_runs_thunks():
    assert gather(lambda: "a", lambda: "b", lambda: "c") == ["a", "b", "c"]
