"""tests for the heuristic scorecard."""

from __future__ import annotations

from agent.scorecard import score


def test_good_answer_beats_vague_one():
    good = (
        "Green tea contains catechins which act as antioxidants. A 2020 review of 12 trials "
        "found a 5% drop in LDL cholesterol. See https://example.org/study for details."
    )
    vague = "maybe it's good, perhaps, i think it might possibly help somehow, sort of."
    assert score(good, n_sources=2).overall > score(vague).overall


def test_empty_answer_scores_low():
    assert score("").overall < 0.2


def test_hedging_drags_score_down():
    plain = "The boiling point of water at sea level is 100 degrees Celsius."
    hedged = "Maybe the boiling point is perhaps possibly around 100, i think, probably."
    assert score(plain).parts["hedging"] > score(hedged).parts["hedging"]


def test_parts_present_and_bounded():
    sc = score("A normal sentence with some detail and a number like 42.")
    assert set(sc.parts) == {"length", "sourcing", "hedging", "readability", "concreteness"}
    assert all(0.0 <= v <= 1.0 for v in sc.parts.values())
    assert 0.0 <= sc.overall <= 1.0
