"""tests for the grounded writing layer (offline, injected section drafting)."""

from __future__ import annotations

from agent.scholar.paper import Paper
from agent.scholar.writing import OUTLINES, Section, draft_section, write_document

_PAPERS = [
    Paper(
        title="Caffeine delays sleep",
        abstract="Caffeine delays sleep onset.",
        authors=["Jane Smith"],
        year=2021,
        doi="10.1/a",
    ),
    Paper(
        title="Caffeine and latency",
        abstract="Caffeine increases latency.",
        authors=["Amy Ng"],
        year=2020,
        doi="10.2/b",
    ),
]


def test_write_document_builds_full_outline():
    doc = write_document(
        "caffeine and sleep",
        _PAPERS,
        kind="review",
        section_for=lambda h, t, ps: Section(heading=h, body=f"{h} body"),
    )
    assert [s.heading for s in doc.sections] == OUTLINES["review"]
    assert "## References" in doc.to_markdown()


def test_references_appear_in_document():
    doc = write_document(
        "topic", _PAPERS, section_for=lambda h, t, ps: Section(heading=h, body="x")
    )
    md = doc.to_markdown()
    assert "Smith" in md and "Ng" in md  # both papers referenced


def test_draft_section_grounds_in_papers_and_detects_citations():
    def complete(prompt, system=None, settings=None):
        # a model that cites Smith
        assert "ONLY the provided sources" in system
        return "The literature shows clear effects (Smith, 2021)."

    sec = draft_section("Introduction", "caffeine", _PAPERS, complete=complete)
    assert "Smith" in sec.body
    assert any("Smith" in c for c in sec.cited)


def test_draft_section_empty_when_no_papers():
    sec = draft_section("Intro", "t", [], complete=lambda *a, **k: "x")
    assert sec.body == ""


def test_empirical_kind_uses_imrad():
    doc = write_document(
        "t", _PAPERS, kind="empirical", section_for=lambda h, t, ps: Section(heading=h, body="x")
    )
    headings = [s.heading for s in doc.sections]
    assert "Methods" in headings and "Results" in headings
