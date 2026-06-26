"""tests for the citation engine."""

from __future__ import annotations

import pytest

from agent.scholar.citations import STYLES, in_text, reference, reference_list
from agent.scholar.paper import Paper

_P = Paper(
    title="Effects of caffeine on sleep",
    authors=["Jane A Smith", "Bob Lee"],
    year=2021,
    venue="Journal of Sleep",
    doi="10.1/abc",
)


def test_apa_reference():
    ref = reference(_P, "apa")
    assert "Smith, J. A." in ref and "(2021)" in ref and "10.1/abc" in ref


def test_apa_in_text_two_authors():
    assert in_text(_P, "apa") == "(Smith & Lee, 2021)"


def test_in_text_et_al_for_three_plus():
    p = Paper(title="t", authors=["A One", "B Two", "C Three"], year=2020)
    assert in_text(p, "apa") == "(One et al., 2020)"


def test_bibtex_has_key_and_fields():
    bib = reference(_P, "bibtex")
    assert bib.startswith("@article{smith2021")
    assert "author = {Jane A Smith and Bob Lee}" in bib


@pytest.mark.parametrize("style", STYLES)
def test_every_style_produces_nonempty_reference(style):
    assert reference(_P, style).strip()


def test_unknown_style_raises():
    with pytest.raises(ValueError):
        reference(_P, "turabian")


def test_reference_list_dedupes_and_sorts():
    a = Paper(title="Zebra study", authors=["Zoe Zane"], year=2020, doi="10.1/z")
    b = Paper(title="Apple study", authors=["Amy Apple"], year=2019, doi="10.2/a")
    dup = Paper(title="Apple study", authors=["Amy Apple"], year=2019, doi="10.2/a")
    out = reference_list([a, b, dup], "apa")
    assert out.count("Apple study") == 1  # deduped
    assert out.index("Apple") < out.index("Zane")  # sorted by author surname


def test_vancouver_numbers_entries():
    out = reference_list([_P], "vancouver")
    assert out.startswith("1. ")


def test_missing_year_is_nd():
    p = Paper(title="t", authors=["A B"])
    assert "n.d." in reference(p, "apa")
