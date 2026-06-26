"""tests for study classification and evidence grading."""

from __future__ import annotations

from agent.scholar.classify import classify, extract_sample_size, keep_scholarly
from agent.scholar.paper import Paper
from agent.scholar.quality import grade, rank_by_quality

_RCT = Paper(
    title="A randomized controlled trial of caffeine",
    abstract="We randomly assigned 240 participants (n = 240). Results show p < 0.05.",
    year=2022,
    citations=80,
    open_access=True,
)
_META = Paper(
    title="Caffeine and sleep: a systematic review and meta-analysis",
    abstract="Studies were included following a PRISMA search strategy of 5000 participants.",
    year=2023,
    citations=300,
)
_EDITORIAL = Paper(title="Why caffeine matters: an editorial", abstract="We argue that it matters.")


def test_rct_is_empirical():
    c = classify(_RCT)
    assert c.is_empirical and not c.is_review
    assert c.design == "rct" and c.evidence_rank == 7


def test_meta_analysis_is_review_top_rank():
    c = classify(_META)
    assert c.is_review and c.evidence_rank == 9


def test_editorial_is_neither():
    c = classify(_EDITORIAL)
    assert not c.is_empirical and not c.is_review


def test_keep_scholarly_filters_out_editorials():
    kept = keep_scholarly([_RCT, _META, _EDITORIAL])
    titles = [p.title for p in kept]
    assert _RCT.title in titles and _META.title in titles
    assert _EDITORIAL.title not in titles


def test_extract_sample_size():
    assert extract_sample_size(_RCT) == 240
    assert extract_sample_size(Paper(title="t", abstract="we surveyed 1,024 respondents")) == 1024
    assert extract_sample_size(Paper(title="t", abstract="no numbers here")) is None


def test_grade_strong_vs_weak():
    weak = Paper(title="A case report", abstract="We report a case.", year=2001, citations=1)
    assert grade(_META, now=2025).score > grade(weak, now=2025).score
    assert grade(_META, now=2025).label in ("high", "moderate")
    assert grade(weak, now=2025).label in ("low", "very low")


def test_rank_by_quality_orders_strongest_first():
    weak = Paper(title="case report", abstract="we report a case", year=2000)
    ranked = rank_by_quality([weak, _META], now=2025)
    assert ranked[0][0].title == _META.title
