"""a cheap, offline confidence/quality scorecard for an answer.

it is not a real quality model -- it is a bundle of dumb-but-useful heuristics (does it cite
sources? is it drowning in hedge words? is it a reasonable length? are the sentences readable?)
rolled into a 0..1 score. good enough to rank revisions in the critique loop and to give the
council something to optimise toward, with no api call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEDGES = (
    "maybe",
    "perhaps",
    "might",
    "possibly",
    "i think",
    "probably",
    "sort of",
    "kind of",
    "it seems",
    "arguably",
)


@dataclass
class Scorecard:
    overall: float
    parts: dict[str, float] = field(default_factory=dict)

    def pretty(self) -> str:
        bits = ", ".join(f"{k}={v:.2f}" for k, v in self.parts.items())
        return f"score {self.overall:.2f} ({bits})"


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def score(answer: str, n_sources: int = 0) -> Scorecard:
    """grade an answer on a few axes and return a blended 0..1 score."""
    text = answer.strip()
    if not text:
        # nothing to grade -- don't let empty defaults (no hedges, no long sentences) inflate it
        parts = dict.fromkeys(("length", "sourcing", "hedging", "readability", "concreteness"), 0.0)
        return Scorecard(overall=0.0, parts=parts)
    words = re.findall(r"\w+", text)
    n_words = len(words)
    sentences = _sentences(text)

    # length: reward a substantive but not bloated answer (sweet spot ~40-250 words)
    if n_words == 0:
        length = 0.0
    elif n_words < 40:
        length = n_words / 40
    elif n_words <= 250:
        length = 1.0
    else:
        length = max(0.3, 250 / n_words)

    # sourcing: any citations / urls at all, scaled
    urls = len(re.findall(r"https?://", text))
    sourcing = min(1.0, (n_sources + urls) / 3)

    # hedging: too many weasel words drags it down
    low = text.lower()
    hedge_hits = sum(low.count(h) for h in _HEDGES)
    hedging = max(0.0, 1.0 - hedge_hits * 0.15)

    # readability: punish runaway sentences
    avg_len = (n_words / len(sentences)) if sentences else 0
    readability = 1.0 if avg_len <= 28 else max(0.2, 28 / avg_len)

    # concreteness: numbers and named specifics are a good sign
    concreteness = min(1.0, len(re.findall(r"\b\d+\b", text)) / 4)

    parts = {
        "length": round(length, 3),
        "sourcing": round(sourcing, 3),
        "hedging": round(hedging, 3),
        "readability": round(readability, 3),
        "concreteness": round(concreteness, 3),
    }
    weights = {
        "length": 0.2,
        "sourcing": 0.25,
        "hedging": 0.2,
        "readability": 0.15,
        "concreteness": 0.2,
    }
    overall = sum(parts[k] * weights[k] for k in parts)
    return Scorecard(overall=round(overall, 3), parts=parts)
