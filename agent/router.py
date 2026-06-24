"""a dead-simple query router: look at the question, pick the mode that fits.

the council uses this to decide whether a query wants a straight research pass, a two-sided
debate, a multi-role swarm, a quick definition, or just a calculator. it's all keyword/shape
heuristics -- no model call -- so it's instant, free, and easy to test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MODES = ("calc", "define", "debate", "swarm", "research")


@dataclass
class Route:
    mode: str
    reason: str


_DEBATE_HINTS = (
    "should we",
    "should i",
    "is it better",
    "better than",
    " vs ",
    " versus ",
    "pros and cons",
    "worth it",
    "good idea",
)
_SWARM_HINTS = (
    "compare",
    "trade-off",
    "tradeoff",
    "trade off",
    "strategy",
    "approach",
    "design",
    "plan for",
    "how should",
    "evaluate",
)
_DEFINE_HINTS = ("what is", "what are", "define", "meaning of", "who is", "who was")


def route(query: str) -> Route:
    """classify a query into one of MODES with a short reason."""
    q = query.strip().lower()

    # a pure arithmetic expression -> calculator
    if re.fullmatch(r"[\d\s+\-*/().%^]+", q) and re.search(r"\d", q):
        return Route("calc", "looks like a bare arithmetic expression")

    if any(h in q for h in _DEBATE_HINTS):
        return Route("debate", "phrased as a should-we / either-or question")

    if any(h in q for h in _SWARM_HINTS):
        return Route("swarm", "asks to compare or strategise, wants multiple angles")

    # short "what is X" lookups -> define (but not long analytical questions)
    if any(q.startswith(h) for h in _DEFINE_HINTS) and len(q.split()) <= 8:
        return Route("define", "short definitional lookup")

    return Route("research", "general question, default to a research pass")
