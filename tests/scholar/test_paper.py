"""tests for the scholarly Paper model."""

from __future__ import annotations

from agent.scholar.paper import Paper, dedupe


def test_short_ref_formats_by_author_count():
    assert Paper(title="t", authors=["Jane Smith"], year=2020).short_ref() == "Smith (2020)"
    two = Paper(title="t", authors=["Jane Smith", "Bob Lee"], year=2020)
    assert two.short_ref() == "Smith & Lee (2020)"
    many = Paper(title="t", authors=["Jane Smith", "Bob Lee", "Amy Ng"], year=2020)
    assert many.short_ref() == "Smith et al. (2020)"


def test_short_ref_handles_missing_year():
    assert "n.d." in Paper(title="t", authors=["A B"]).short_ref()


def test_key_prefers_doi():
    assert Paper(title="t", doi="10.1/ABC").key == "doi:10.1/abc"
    assert Paper(title="My Title").key.startswith("title:")


def test_key_normalizes_doi_url():
    assert Paper(title="t", doi="https://doi.org/10.1/abc").key == "doi:10.1/abc"


def test_dedupe_keeps_richer_record():
    sparse = Paper(title="Same", doi="10.5/z")
    rich = Paper(title="Same", doi="10.5/z", abstract="abs", authors=["A B"], year=2020)
    out = dedupe([sparse, rich])
    assert len(out) == 1 and out[0].abstract == "abs"


def test_dedupe_different_papers_kept():
    a = Paper(title="A", doi="10.1/a")
    b = Paper(title="B", doi="10.2/b")
    assert len(dedupe([a, b])) == 2


def test_dict_roundtrip():
    p = Paper(title="t", authors=["A B"], year=2021, doi="10.1/x", citations=5)
    assert Paper.from_dict(p.to_dict()).to_dict() == p.to_dict()
