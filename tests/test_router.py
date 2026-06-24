"""tests for the query router."""

from __future__ import annotations

import pytest

from agent.router import MODES, route


@pytest.mark.parametrize(
    "query,expected",
    [
        ("2 + 2 * 3", "calc"),
        ("(10 / 2) + 4", "calc"),
        ("should we migrate to kubernetes?", "debate"),
        ("is postgres better than mysql?", "debate"),
        ("compare the trade-offs of microservices", "swarm"),
        ("what should our caching strategy be", "swarm"),
        ("what is entropy", "define"),
        ("define recursion", "define"),
        ("why do volcanoes erupt the way they do", "research"),
    ],
)
def test_route_picks_expected_mode(query, expected):
    assert route(query).mode == expected


def test_route_always_returns_a_known_mode():
    assert route("anything at all here").mode in MODES
    assert route("").mode in MODES


def test_route_has_a_reason():
    assert route("what is x").reason


def test_route_reports_confidence_and_scores():
    r = route("should we adopt kubernetes?")
    assert 0.0 < r.confidence <= 1.0
    assert set(r.scores) == set(MODES)
    assert r.scores[r.mode] == max(r.scores.values())


def test_runner_up_is_second_best():
    r = route("should we use postgres or mysql?")
    assert r.mode == "debate"
    assert r.runner_up in MODES and r.runner_up != "debate"


def test_long_what_is_question_is_research_not_define():
    r = route("what is the long-term economic impact of automation on labor markets")
    assert r.mode == "research"
