"""run independent work concurrently.

most of what makes the agent slow is waiting -- on the network, on the model. that's exactly
what threads are good for. this is a tiny, order-preserving parallel map over a bounded thread
pool, with per-item error isolation so one failure doesn't sink the batch. the deep-research
pipeline uses it to fetch pages and answer independent sub-questions at the same time.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def map_parallel(
    fn: Callable[[Any], Any],
    items: Iterable[Any],
    workers: int = 8,
    on_error: str = "none",
) -> list[Any]:
    """apply `fn` to every item concurrently and return results in the original order.

    on_error="none" turns a failing item into None; on_error="raise" re-raises the first error.
    workers is capped to the number of items so we don't spin up idle threads.
    """
    items = list(items)
    if not items:
        return []
    n_workers = max(1, min(workers, len(items)))
    results: list[Any] = [None] * len(items)
    errors: dict[int, Exception] = {}

    def _run(i_item):
        i, item = i_item
        try:
            return i, fn(item), None
        except Exception as exc:  # noqa: BLE001 - isolation is the whole point
            return i, None, exc

    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        for i, value, exc in pool.map(_run, enumerate(items)):
            if exc is not None:
                errors[i] = exc
            else:
                results[i] = value

    if errors and on_error == "raise":
        first = sorted(errors)[0]
        raise errors[first]
    return results


def gather(*thunks: Callable[[], Any], workers: int = 8, on_error: str = "none") -> list[Any]:
    """run a handful of zero-arg callables concurrently. like asyncio.gather, but threads."""
    return map_parallel(lambda t: t(), thunks, workers=workers, on_error=on_error)
