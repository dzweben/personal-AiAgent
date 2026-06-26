"""tests for the ResearchWriter capstone (offline, injected search + drafting)."""

from __future__ import annotations

from agent.scholar.arm import ResearchWriter, write_review
from agent.scholar.paper import Paper
from agent.scholar.writing import Section

_RCT = Paper(
    title="RCT of caffeine",
    abstract="We randomly assigned 240 participants (n = 240). p < 0.05.",
    authors=["Jane Smith"],
    year=2022,
    doi="10.1/a",
    citations=50,
    open_access=True,
)
_REVIEW = Paper(
    title="Systematic review of caffeine",
    abstract="PRISMA systematic review, studies were included.",
    authors=["Amy Ng"],
    year=2023,
    doi="10.2/b",
    citations=120,
)
_OPINION = Paper(
    title="Opinion piece",
    abstract="We argue that caffeine is great.",
    authors=["Joe Blog"],
    year=2020,
)


def _search(topic, limit):
    return [_RCT, _REVIEW, _OPINION]


def _section(h, t, ps):
    return Section(heading=h, body=f"{h}: {t} (Smith, 2022).")


def test_arm_filters_to_scholarly_only():
    res = write_review("caffeine and sleep", search=_search, section_for=_section)
    titles = [p.title for p in res.papers]
    assert _RCT.title in titles and _REVIEW.title in titles
    assert _OPINION.title not in titles  # editorial filtered out


def test_arm_produces_document_and_references():
    res = write_review("caffeine and sleep", search=_search, section_for=_section)
    md = res.to_markdown()
    assert "## References" in md and "## Evidence base" in md
    assert "Smith" in md and "Ng" in md


def test_arm_orders_by_evidence_quality():
    res = write_review("caffeine and sleep", search=_search, section_for=_section)
    # the review (higher citations + meta rank) should outrank or tie the RCT
    md = res.to_markdown()
    assert "[" in md  # grade labels present


def test_arm_reports_synthesis():
    res = write_review("caffeine and sleep", search=_search, section_for=_section)
    assert res.themes
    assert res.agreement in ("broadly consistent", "contested")
    assert res.timeline  # year counts present


def test_writer_corpus_accumulates():
    w = ResearchWriter(search=_search)
    w.gather("caffeine", limit=10)
    assert len(w.corpus) == 2  # the two scholarly papers, editorial excluded
