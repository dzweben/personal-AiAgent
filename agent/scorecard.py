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


# default blend weights; override per-call to tune what the score rewards.
DEFAULT_WEIGHTS = {
    "length": 0.15,
    "sourcing": 0.2,
    "hedging": 0.15,
    "readability": 0.13,
    "concreteness": 0.17,
    "specificity": 0.1,
    "structure": 0.1,
}

_PART_NAMES = tuple(DEFAULT_WEIGHTS)

# specificity markers: dates, percentages, units, proper-noun-ish capitalised mid-sentence words
_SPECIFIC_RE = re.compile(
    r"\b\d{4}\b|\d+%|\b\d+(\.\d+)?\s?(kg|km|m|mm|cm|ml|l|°c|°f|hz|gb|mb)\b", re.IGNORECASE
)


def score(answer: str, n_sources: int = 0, weights: dict[str, float] | None = None) -> Scorecard:
    """grade an answer on several axes and return a blended 0..1 score.

    pass `weights` (a partial dict is fine) to retune which qualities matter; anything omitted
    falls back to DEFAULT_WEIGHTS.
    """
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    text = answer.strip()
    if not text:
        # nothing to grade -- don't let empty defaults (no hedges, no long sentences) inflate it
        return Scorecard(overall=0.0, parts=dict.fromkeys(_PART_NAMES, 0.0))
    words = re.findall(r"\w+", text)
    n_words = len(words)
    sentences = _sentences(text)
    low = text.lower()

    # length: reward a substantive but not bloated answer (sweet spot ~40-250 words)
    if n_words < 40:
        length = n_words / 40
    elif n_words <= 250:
        length = 1.0
    else:
        length = max(0.3, 250 / n_words)

    # sourcing: any citations / urls at all, scaled
    urls = len(re.findall(r"https?://", text))
    sourcing = min(1.0, (n_sources + urls) / 3)

    # hedging: too many weasel words drags it down
    hedge_hits = sum(low.count(h) for h in _HEDGES)
    hedging = max(0.0, 1.0 - hedge_hits * 0.15)

    # readability: punish runaway sentences
    avg_len = (n_words / len(sentences)) if sentences else 0
    readability = 1.0 if avg_len <= 28 else max(0.2, 28 / avg_len)

    # concreteness: numbers are a good sign
    concreteness = min(1.0, len(re.findall(r"\b\d+\b", text)) / 4)

    # specificity: dates, percentages, units -> the answer commits to particulars
    specificity = min(1.0, len(_SPECIFIC_RE.findall(text)) / 3)

    # structure: multiple sentences, or list/heading markers, read as organised
    has_list = bool(re.search(r"(^|\n)\s*[-*\d]", text))
    structure = min(1.0, (len(sentences) / 4) * (1.2 if has_list else 1.0))

    parts = {
        "length": round(length, 3),
        "sourcing": round(sourcing, 3),
        "hedging": round(hedging, 3),
        "readability": round(readability, 3),
        "concreteness": round(concreteness, 3),
        "specificity": round(specificity, 3),
        "structure": round(structure, 3),
    }
    total_w = sum(weights[k] for k in parts) or 1.0
    overall = sum(parts[k] * weights[k] for k in parts) / total_w
    return Scorecard(overall=round(overall, 3), parts=parts)


def compare(a: str, b: str, n_sources_a: int = 0, n_sources_b: int = 0) -> dict:
    """score two answers and report which wins, with the per-dimension deltas."""
    sa, sb = score(a, n_sources_a), score(b, n_sources_b)
    deltas = {k: round(sb.parts[k] - sa.parts[k], 3) for k in sa.parts}
    winner = "a" if sa.overall >= sb.overall else "b"
    return {"a": sa, "b": sb, "winner": winner, "deltas": deltas}
