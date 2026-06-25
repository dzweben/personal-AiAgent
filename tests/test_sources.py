"""tests for source extraction and ranking."""

from __future__ import annotations

from agent.sources import authority, extract_sources, sourcing_score


def test_extracts_and_dedupes_by_domain():
    text = "See https://nih.gov/a and https://nih.gov/b and https://example.org/c."
    sources = extract_sources(text)
    domains = [s.domain for s in sources]
    assert "nih.gov" in domains and "example.org" in domains
    assert domains.count("nih.gov") == 1  # deduped


def test_authority_orders_gov_above_blog():
    assert authority("cdc.gov") > authority("example.com")
    assert authority("medium.com") < authority("example.org")


def test_sources_sorted_by_authority():
    text = "https://medium.com/x and https://nih.gov/y and https://foo.com/z"
    sources = extract_sources(text)
    auths = [s.authority for s in sources]
    assert auths == sorted(auths, reverse=True)


def test_sourcing_score_rewards_credible_citations():
    weak = "https://medium.com/post"
    strong = "https://nih.gov/a and https://nature.com/b and https://cdc.gov/c"
    assert sourcing_score(strong) > sourcing_score(weak)


def test_no_sources_scores_zero():
    assert sourcing_score("an answer with no links at all") == 0.0


def test_bare_domain_is_picked_up():
    sources = extract_sources("according to nature.com this is true")
    assert any(s.domain == "nature.com" for s in sources)
