"""find pairs of claims that contradict each other across a set of answers.

when you gather several answers (an ensemble, a multi-hop run, a set of sources), they don't
always agree. this pairs up claims that are about the same thing but point opposite ways --
negation flips, antonym pairs, and disagreeing numbers for the same subject. it's a heuristic
detector (with an injectable model-backed checker for the hard cases), so it runs offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agent.factcheck import extract_claims

_NEG = re.compile(r"\b(?:not|no|never|cannot|can't|isn't|aren't|doesn't|don't|won't|false)\b")
_ANTONYMS = [
    ("increase", "decrease"),
    ("rise", "fall"),
    ("higher", "lower"),
    ("more", "less"),
    ("safe", "dangerous"),
    ("true", "false"),
    ("cause", "prevent"),
    ("help", "harm"),
    ("positive", "negative"),
    ("good", "bad"),
]


@dataclass
class Contradiction:
    a: str
    b: str
    reason: str


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _subject_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _numbers(text: str) -> list[str]:
    return re.findall(r"\b\d+(?:\.\d+)?\b", text)


def _looks_contradictory(a: str, b: str) -> str | None:
    """return a reason string if a and b seem to clash, else None. assumes shared subject."""
    la, lb = a.lower(), b.lower()
    # one negates and the other doesn't
    if bool(_NEG.search(la)) != bool(_NEG.search(lb)):
        return "one statement negates the other"
    # antonym pair present across the two
    for x, y in _ANTONYMS:
        if (x in la and y in lb) or (y in la and x in lb):
            return f"opposing terms: {x}/{y}"
    # same subject but different headline numbers
    na, nb = _numbers(a), _numbers(b)
    if na and nb and set(na) != set(nb) and na[0] != nb[0]:
        return f"different figures: {na[0]} vs {nb[0]}"
    return None


def find_contradictions(
    answers: list[str], subject_threshold: float = 0.25, check=None
) -> list[Contradiction]:
    """compare claims pairwise across answers and report likely contradictions.

    `check(a, b) -> bool` is an optional model-backed verifier for the hard cases; when given,
    a pair must both look contradictory heuristically *and* pass the check.
    """
    claims: list[str] = []
    for ans in answers:
        claims.extend(extract_claims(ans))

    out: list[Contradiction] = []
    seen: set[tuple[int, int]] = set()
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            if (i, j) in seen:
                continue
            seen.add((i, j))
            if _subject_overlap(claims[i], claims[j]) < subject_threshold:
                continue  # not about the same thing
            reason = _looks_contradictory(claims[i], claims[j])
            if not reason:
                continue
            if check is not None and not check(claims[i], claims[j]):
                continue
            out.append(Contradiction(a=claims[i], b=claims[j], reason=reason))
    return out
