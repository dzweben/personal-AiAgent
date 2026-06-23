"""a small evaluation harness.

nothing academic, just a way to throw a list of questions at the agent and get back some
basic metrics: did it return structured output, how many sources did it cite, how long did
it take. useful for sanity checking a prompt or model change without eyeballing every run.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Optional

from agent.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class EvalCase:
    query: str
    expect_keywords: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    query: str
    parsed: bool
    n_sources: int
    n_tools: int
    keyword_hits: int
    seconds: float
    error: Optional[str] = None


@dataclass
class EvalReport:
    results: list[CaseResult]

    @property
    def parse_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.parsed for r in self.results) / len(self.results)

    @property
    def avg_sources(self) -> float:
        vals = [r.n_sources for r in self.results if r.parsed]
        return round(mean(vals), 2) if vals else 0.0

    @property
    def avg_seconds(self) -> float:
        vals = [r.seconds for r in self.results]
        return round(mean(vals), 2) if vals else 0.0

    def summary(self) -> str:
        return (
            f"{len(self.results)} cases | parse rate {self.parse_rate:.0%} | "
            f"avg sources {self.avg_sources} | avg {self.avg_seconds}s"
        )


def run_eval(agent, cases: list[EvalCase]) -> EvalReport:
    """run each case through an already-built agent and collect metrics."""
    results: list[CaseResult] = []
    for case in cases:
        start = time.perf_counter()
        error = None
        parsed = False
        n_sources = n_tools = keyword_hits = 0
        try:
            res = agent.research(case.query)
            parsed = res.structured is not None
            if parsed:
                n_sources = len(res.structured.sources)
                n_tools = len(res.structured.tools_used)
            text = (res.output_text or "").lower()
            keyword_hits = sum(1 for kw in case.expect_keywords if kw.lower() in text)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            log.warning("eval case failed: %s", exc)
        results.append(
            CaseResult(
                query=case.query,
                parsed=parsed,
                n_sources=n_sources,
                n_tools=n_tools,
                keyword_hits=keyword_hits,
                seconds=round(time.perf_counter() - start, 2),
                error=error,
            )
        )
    return EvalReport(results=results)
