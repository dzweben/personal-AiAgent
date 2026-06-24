"""pull the checkable claims out of an answer and verify them one by one.

an answer is only as good as its claims, so this splits the text into declarative sentences,
keeps the ones that actually assert something factual, and runs each past a verifier. the
verifier is injectable (a real one would search the web or ask a model); offline it's whatever
you pass in. the result is a per-claim verdict you can show the user or feed into the critic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

VERDICTS = ("supported", "refuted", "unclear")


@dataclass
class ClaimCheck:
    claim: str
    verdict: str
    note: str = ""
    importance: float = 0.5


# sentences that are usually opinion/instruction rather than checkable fact
_SOFT_STARTS = ("i ", "you ", "we should", "let's", "please", "consider", "maybe", "perhaps")


def claim_importance(claim: str) -> float:
    """rough 0..1 weight for how much a claim matters: numbers, dates, and length raise it."""
    score = 0.3
    if re.search(r"\b\d", claim):
        score += 0.3  # quantified claims carry more weight
    if re.search(r"\b\d{4}\b|\d+%", claim):
        score += 0.2  # dates / percentages are load-bearing specifics
    if len(claim.split()) >= 12:
        score += 0.2  # a longer assertion usually says more
    return min(1.0, round(score, 3))


def extract_claims(text: str, max_claims: int = 8) -> list[str]:
    """split into sentences and keep the deduped ones that look like factual assertions."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    claims: list[str] = []
    seen: set[str] = set()
    for s in sentences:
        low = s.lower()
        if s.endswith("?"):
            continue  # questions aren't claims
        if any(low.startswith(p) for p in _SOFT_STARTS):
            continue
        if len(s.split()) < 4:
            continue  # too short to be a real claim
        key = re.sub(r"\W+", " ", low).strip()
        if key in seen:
            continue  # drop near-duplicate restatements
        seen.add(key)
        claims.append(s)
        if len(claims) >= max_claims:
            break
    return claims


def _default_verifier(settings=None):
    from agent.llm import complete

    def verify(claim: str):
        out = complete(
            f"Claim: {claim}\n\nIs this supported, refuted, or unclear from established "
            "knowledge? Reply with one of those words, then a brief reason.",
            settings=settings,
            system="You are a careful fact-checker. Be honest about uncertainty.",
        )
        first = out.strip().split()[0].lower().strip(".,:") if out.strip() else "unclear"
        verdict = first if first in VERDICTS else "unclear"
        return verdict, out.strip()

    return verify


def factcheck(text: str, verify=None, settings=None) -> list[ClaimCheck]:
    """extract claims and verify each. `verify(claim) -> (verdict, note)` is injectable."""
    verify = verify or _default_verifier(settings)
    checks = []
    for claim in extract_claims(text):
        verdict, note = verify(claim)
        verdict = verdict if verdict in VERDICTS else "unclear"
        checks.append(
            ClaimCheck(claim=claim, verdict=verdict, note=note, importance=claim_importance(claim))
        )
    return checks


def summarize_verdicts(checks: list[ClaimCheck]) -> dict[str, int]:
    """tally how many claims landed in each verdict bucket."""
    tally = dict.fromkeys(VERDICTS, 0)
    for c in checks:
        tally[c.verdict] = tally.get(c.verdict, 0) + 1
    return tally


def credibility(checks: list[ClaimCheck]) -> float:
    """an importance-weighted 0..1 credibility score across all checked claims.

    supported claims count fully, unclear claims half, refuted claims not at all -- each weighted
    by how load-bearing the claim is. no claims -> 0.5 (nothing to judge either way).
    """
    if not checks:
        return 0.5
    weight = {"supported": 1.0, "unclear": 0.5, "refuted": 0.0}
    total = sum(c.importance for c in checks) or 1.0
    earned = sum(weight.get(c.verdict, 0.5) * c.importance for c in checks)
    return round(earned / total, 3)
