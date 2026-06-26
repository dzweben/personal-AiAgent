"""grade how much weight a paper's evidence deserves.

writing good research means leaning harder on stronger evidence. this rolls a paper's study
design, sample size, citation count, recency, and open-access status into a single 0..1 quality
score plus a GRADE-style label (high / moderate / low / very low). it's a transparent heuristic,
not a substitute for reading the paper -- but it's enough to rank and weight a reading list.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.scholar.classify import classify, extract_sample_size
from agent.scholar.paper import Paper

# current-ish year used for recency scoring; passed in so the module stays deterministic.
_DEFAULT_YEAR = 2025


@dataclass
class EvidenceGrade:
    score: float  # 0..1
    label: str  # high | moderate | low | very low
    design: str
    sample_size: int | None
    parts: dict


def _recency(year: int | None, now: int) -> float:
    if not year:
        return 0.3
    age = max(0, now - year)
    return max(0.1, 1.0 - age / 25)  # ~25 years to fully decay


def _sample_score(n: int | None) -> float:
    if not n:
        return 0.3
    # log-ish bands: tiny < 50, modest < 300, solid < 1000, large beyond
    if n < 50:
        return 0.3
    if n < 300:
        return 0.55
    if n < 1000:
        return 0.75
    return 1.0


def grade(paper: Paper, now: int = _DEFAULT_YEAR) -> EvidenceGrade:
    """produce an evidence grade for a single paper."""
    study = classify(paper)
    n = extract_sample_size(paper)

    design_score = study.evidence_rank / 9 if study.evidence_rank else 0.2
    sample = _sample_score(n)
    recency = _recency(paper.year, now)
    citation = min(1.0, paper.citations / 200) if paper.citations else 0.0
    oa = 1.0 if paper.open_access else 0.5

    parts = {
        "design": round(design_score, 3),
        "sample": round(sample, 3),
        "recency": round(recency, 3),
        "citation": round(citation, 3),
        "access": round(oa, 3),
    }
    weights = {"design": 0.4, "sample": 0.2, "recency": 0.15, "citation": 0.2, "access": 0.05}
    score = round(sum(parts[k] * weights[k] for k in parts), 3)

    if score >= 0.7:
        label = "high"
    elif score >= 0.5:
        label = "moderate"
    elif score >= 0.3:
        label = "low"
    else:
        label = "very low"

    return EvidenceGrade(score=score, label=label, design=study.design, sample_size=n, parts=parts)


def rank_by_quality(
    papers: list[Paper], now: int = _DEFAULT_YEAR
) -> list[tuple[Paper, EvidenceGrade]]:
    """return papers paired with their grade, strongest evidence first."""
    graded = [(p, grade(p, now)) for p in papers]
    graded.sort(key=lambda pg: pg[1].score, reverse=True)
    return graded
