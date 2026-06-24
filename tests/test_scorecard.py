"""tests for the heuristic scorecard."""

from __future__ import annotations

from agent.scorecard import compare, score


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
    assert set(sc.parts) == {
        "length",
        "sourcing",
        "hedging",
        "readability",
        "concreteness",
        "specificity",
        "structure",
    }
    assert all(0.0 <= v <= 1.0 for v in sc.parts.values())
    assert 0.0 <= sc.overall <= 1.0


def test_custom_weights_change_the_blend():
    text = "short and vague maybe."
    default = score(text).overall
    length_only = score(
        text,
        weights={
            "length": 1.0,
            "sourcing": 0,
            "hedging": 0,
            "readability": 0,
            "concreteness": 0,
            "specificity": 0,
            "structure": 0,
        },
    ).overall
    assert default != length_only


def test_specificity_rewards_particulars():
    vague = "It changed a lot over the years and improved quite a bit overall here."
    specific = "It rose 42% between 2010 and 2020, reaching 8849 m in total height."
    assert score(specific).parts["specificity"] > score(vague).parts["specificity"]


def test_compare_picks_the_stronger_answer():
    res = compare("maybe it helps perhaps", "A 2021 trial showed a 5% effect; see https://x.org.")
    assert res["winner"] == "b"
    assert set(res["deltas"]) == set(res["a"].parts)
