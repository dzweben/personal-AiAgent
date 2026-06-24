"""a query router: look at the question, score every mode, pick the best fit.

the council uses this to decide whether a query wants a straight research pass, a two-sided
debate, a multi-role swarm, a quick definition, or just a calculator. rather than first-match,
it now scores each mode from weighted signals, so it can report a confidence and the runner-up.
still all heuristics -- no model call -- so it's instant, free, and easy to test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MODES = ("calc", "define", "debate", "swarm", "research")


@dataclass
class Route:
    mode: str
    reason: str
    confidence: float = 1.0
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def runner_up(self) -> str | None:
        ranked = sorted(self.scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None


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
    "or should",
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
    "options for",
)
_DEFINE_HINTS = ("what is", "what are", "define", "meaning of", "who is", "who was")
_RESEARCH_HINTS = ("why", "how does", "explain", "what happens", "history of", "evidence")


def _count_hits(text: str, hints) -> int:
    return sum(1 for h in hints if h in text)


def route(query: str) -> Route:
    """classify a query into one of MODES, scoring every mode and reporting confidence."""
    q = query.strip().lower()
    scores = dict.fromkeys(MODES, 0.0)

    # a pure arithmetic expression -> calculator (a strong, near-certain signal)
    if re.fullmatch(r"[\d\s+\-*/().%^]+", q) and re.search(r"\d", q):
        scores["calc"] = 5.0

    scores["debate"] += 2.0 * _count_hits(q, _DEBATE_HINTS)
    scores["swarm"] += 1.8 * _count_hits(q, _SWARM_HINTS)
    scores["research"] += 1.2 * _count_hits(q, _RESEARCH_HINTS)

    # short "what is X" lookups lean definitional; long analytical ones don't
    define_hits = sum(1 for h in _DEFINE_HINTS if q.startswith(h))
    if define_hits and len(q.split()) <= 8:
        scores["define"] += 2.5
    elif define_hits:
        scores["research"] += 1.0  # "what is the impact of ..." is really a research ask

    # everyone gets a small research floor so it's the sensible default
    scores["research"] += 0.5

    best = max(scores, key=scores.get)
    total = sum(scores.values()) or 1.0
    confidence = round(scores[best] / total, 3)
    reasons = {
        "calc": "looks like a bare arithmetic expression",
        "debate": "phrased as a should-we / either-or question",
        "swarm": "asks to compare or strategise, wants multiple angles",
        "define": "short definitional lookup",
        "research": "general question, default to a research pass",
    }
    return Route(mode=best, reason=reasons[best], confidence=confidence, scores=scores)
