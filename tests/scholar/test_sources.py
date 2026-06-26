"""tests for the scholarly source connectors (offline, fake fetchers)."""

from __future__ import annotations

from agent.scholar.sources import (
    parse_arxiv,
    parse_crossref,
    parse_europepmc,
    parse_openalex,
    parse_semantic_scholar,
    search_papers,
)

_OA = {
    "results": [
        {
            "title": "Caffeine and Sleep",
            "publication_year": 2021,
            "cited_by_count": 42,
            "doi": "https://doi.org/10.1/x",
            "authorships": [{"author": {"display_name": "Jane Smith"}}],
            "abstract_inverted_index": {"Caffeine": [0], "affects": [1], "sleep": [2]},
            "open_access": {"is_oa": True},
        }
    ]
}


def test_openalex_reconstructs_abstract():
    p = parse_openalex(_OA)[0]
    assert p.abstract == "Caffeine affects sleep"
    assert p.year == 2021 and p.citations == 42 and p.open_access
    assert p.doi == "10.1/x"


def test_crossref_parses_authors_and_year():
    payload = {
        "message": {
            "items": [
                {
                    "title": ["A Study"],
                    "author": [{"given": "Bob", "family": "Lee"}],
                    "issued": {"date-parts": [[2019, 3]]},
                    "DOI": "10.2/y",
                    "container-title": ["Journal of Things"],
                }
            ]
        }
    }
    p = parse_crossref(payload)[0]
    assert p.authors == ["Bob Lee"] and p.year == 2019 and p.venue == "Journal of Things"


def test_semantic_scholar_parses():
    payload = {
        "data": [{"title": "T", "year": 2020, "authors": [{"name": "A B"}], "citationCount": 5}]
    }
    p = parse_semantic_scholar(payload)[0]
    assert p.year == 2020 and p.citations == 5


def test_europepmc_parses():
    payload = {
        "resultList": {
            "result": [
                {
                    "title": "Trial.",
                    "authorString": "Smith J",
                    "pubYear": "2018",
                    "isOpenAccess": "Y",
                }
            ]
        }
    }
    p = parse_europepmc(payload)[0]
    assert p.year == 2018 and p.open_access and p.title == "Trial"


def test_arxiv_parses_atom():
    atom = (
        "<feed><entry><title>Deep Nets</title><id>http://arxiv.org/abs/1</id>"
        "<published>2019-05-01</published><summary>We study nets.</summary>"
        "<author><name>A Researcher</name></author></entry></feed>"
    )
    p = parse_arxiv(atom)[0]
    assert p.title == "Deep Nets" and p.year == 2019 and p.open_access


def test_search_merges_and_dedupes_across_indexes():
    # both indexes return the same DOI -> deduped to one
    papers = search_papers(
        "caffeine",
        indexes=["openalex", "semantic_scholar"],
        fetch_json=lambda url: (
            _OA
            if "openalex" in url
            else {"data": [{"title": "Caffeine and Sleep", "externalIds": {"DOI": "10.1/x"}}]}
        ),
    )
    assert len(papers) == 1


def test_search_survives_a_dead_index():
    def fetch(url):
        if "openalex" in url:
            return _OA
        raise RuntimeError("index down")

    papers = search_papers("q", indexes=["openalex", "crossref"], fetch_json=fetch)
    assert len(papers) == 1  # openalex still came through
