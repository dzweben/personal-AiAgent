"""tell empirical studies and literature reviews apart, and grade the strength of evidence.

the arm is meant to write from empirical work and reviews specifically, so it needs to look at a
paper's title/abstract and decide: is this an original study, a review/meta-analysis, or neither
(an editorial, opinion, protocol)? and how strong is the evidence -- a randomised trial outranks
a case report. these are abstract-text heuristics, deliberately transparent and offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agent.scholar.paper import Paper

# study-design markers, roughly ordered by evidence strength (the classic pyramid).
_DESIGN_RANK = [
    ("meta-analysis", 9, ("meta-analysis", "meta analysis", "pooled analysis")),
    ("systematic-review", 8, ("systematic review", "prisma")),
    (
        "rct",
        7,
        (
            "randomized controlled trial",
            "randomised controlled trial",
            "randomly assigned",
            "double-blind",
            "placebo-controlled",
        ),
    ),
    ("cohort", 6, ("cohort study", "prospective cohort", "longitudinal study", "followed over")),
    ("case-control", 5, ("case-control", "case control")),
    ("cross-sectional", 4, ("cross-sectional", "survey of", "questionnaire")),
    ("review", 3, ("literature review", "narrative review", "we review", "this review")),
    ("case-report", 2, ("case report", "case series", "we report a case")),
]

_EMPIRICAL_HINTS = (
    "we measured",
    "we collected",
    "participants",
    "n =",
    "sample of",
    "data were",
    "results show",
    "we conducted",
    "experiment",
    "we found that",
    "statistically significant",
    "p <",
    "p=",
    "regression",
    "odds ratio",
    "confidence interval",
    "we analyzed",
    "we analysed",
)
_REVIEW_HINTS = (
    "systematic review",
    "meta-analysis",
    "meta analysis",
    "literature review",
    "narrative review",
    "we review",
    "this review",
    "scoping review",
    "we synthesise",
    "we synthesize",
    "studies were included",
    "search strategy",
)
_NONRESEARCH_HINTS = (
    "editorial",
    "commentary",
    "opinion",
    "we argue that",
    "perspective",
    "letter to the editor",
)


@dataclass
class StudyType:
    is_empirical: bool
    is_review: bool
    design: str
    evidence_rank: int  # 0..9, higher = stronger
    reason: str = ""


def _text(paper: Paper) -> str:
    return f"{paper.title}. {paper.abstract}".lower()


def detect_design(paper: Paper) -> tuple[str, int]:
    """return the (design, rank) of the strongest design signal present, or ('unknown', 0)."""
    text = _text(paper)
    for design, rank, markers in _DESIGN_RANK:
        if any(m in text for m in markers):
            return design, rank
    return "unknown", 0


def classify(paper: Paper) -> StudyType:
    """classify a paper as empirical / review and grade its evidence."""
    text = _text(paper)
    design, rank = detect_design(paper)

    is_review = design in ("meta-analysis", "systematic-review", "review") or any(
        h in text for h in _REVIEW_HINTS
    )
    is_empirical = (not is_review) and (
        rank >= 4 or sum(1 for h in _EMPIRICAL_HINTS if h in text) >= 2
    )
    # editorials / opinion pieces are neither
    if any(h in text for h in _NONRESEARCH_HINTS) and not (is_review and rank >= 8):
        if rank < 4:
            is_empirical = False

    reason = f"design={design}, rank={rank}"
    return StudyType(
        is_empirical=is_empirical,
        is_review=is_review,
        design=design,
        evidence_rank=rank,
        reason=reason,
    )


def keep_scholarly(papers: list[Paper]) -> list[Paper]:
    """filter a list down to empirical studies and reviews (the arm's allowed diet)."""
    return [p for p in papers if (c := classify(p)).is_empirical or c.is_review]


def extract_sample_size(paper: Paper) -> int | None:
    """best-effort pull of the study's N from the abstract (e.g. 'n = 240', '1,024 participants')."""
    text = _text(paper)
    m = re.search(r"\bn\s*=\s*([\d,]+)", text)
    if m:
        return int(m.group(1).replace(",", ""))
    m = re.search(r"([\d,]{2,})\s+(?:participants|patients|subjects|respondents|adults)", text)
    if m:
        return int(m.group(1).replace(",", ""))
    return None
