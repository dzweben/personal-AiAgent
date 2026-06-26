"""tests for thematic synthesis."""

from __future__ import annotations

from agent.scholar.paper import Paper
from agent.scholar.synthesis import consensus, gaps, themes, timeline

_PAPERS = [
    Paper(
        title="Caffeine and sleep onset",
        abstract="Caffeine delays sleep onset in adults.",
        year=2020,
        authors=["A One"],
    ),
    Paper(
        title="Caffeine and sleep latency",
        abstract="Caffeine increases sleep latency in adults.",
        year=2021,
        authors=["B Two"],
    ),
    Paper(
        title="Exercise and mood",
        abstract="Exercise improves mood. Future research should examine dose.",
        year=2019,
        authors=["C Three"],
    ),
]


def test_themes_group_related_papers():
    th = themes(_PAPERS)
    biggest = th[0]
    assert biggest.size == 2  # the two caffeine papers cluster
    assert "caffeine" in biggest.label


def test_timeline_counts_by_year():
    assert timeline(_PAPERS) == {2019: 1, 2020: 1, 2021: 1}


def test_consensus_detects_agreement():
    agreeing = [
        Paper(title="t1", abstract="Caffeine delays sleep in adults."),
        Paper(title="t2", abstract="Caffeine delays sleep in adults too."),
    ]
    assert consensus(agreeing)["agreement"] == "broadly consistent"


def test_consensus_detects_contradiction():
    clashing = [
        Paper(title="t1", abstract="Caffeine improves alertness in adults."),
        Paper(title="t2", abstract="Caffeine does not improve alertness in adults."),
    ]
    assert consensus(clashing)["agreement"] == "contested"


def test_gaps_flags_single_study_theme():
    out = gaps(_PAPERS)
    assert any("single study" in g for g in out)


def test_gaps_mines_future_work_cue():
    out = gaps(_PAPERS)
    assert any("Future research" in g for g in out)


def test_gaps_accepts_injected_proposer():
    assert gaps(_PAPERS, propose=lambda papers: ["a custom gap"]) == ["a custom gap"]
