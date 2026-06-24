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
