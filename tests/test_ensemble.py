"""tests for the persona ensemble (offline, fake answerers)."""

from __future__ import annotations

from agent.ensemble import best_by_score, ensemble, vote


def test_vote_picks_the_consensus_answer():
    answers = [
        "the earth orbits the sun once a year",
        "the earth orbits the sun annually",
        "bananas are a good source of potassium",
    ]
    winner = vote(answers)
    assert "earth orbits the sun" in winner


def test_vote_handles_edge_cases():
    assert vote([]) == ""
    assert vote(["only one"]) == "only one"


def test_ensemble_collects_one_answer_per_persona():
    res = ensemble(
        "what is x?",
        personas=["researcher", "skeptic", "eli5"],
        answer=lambda persona, q: f"{persona} says hi",
    )
    assert set(res.answers) == {"researcher", "skeptic", "eli5"}
    assert res.merged  # vote produced something
    assert "what is x?" in res.pretty()


def test_ensemble_uses_injected_merge():
    res = ensemble(
        "q",
        personas=["a", "b"],
        answer=lambda p, q: f"{p}-ans",
        merge=lambda q, answers: "MERGED:" + "+".join(answers.values()),
    )
    assert res.merged == "MERGED:a-ans+b-ans"


def test_best_by_score_picks_quality():
    answers = [
        "maybe perhaps it depends",
        "In 2021 a trial of 500 found a 12% gain; see https://x.org.",
    ]
    assert "2021" in best_by_score(answers)


def test_strategy_best_used_in_ensemble():
    ans = {"a": "vague maybe", "b": "Concretely, in 2020 it rose 8% per https://x.org data."}
    res = ensemble("q", personas=["a", "b"], answer=lambda p, q: ans[p], strategy="best")
    assert "2020" in res.merged


def test_strategy_longest():
    ans = {"a": "short", "b": "a considerably longer answer that wins on length"}
    res = ensemble("q", personas=["a", "b"], answer=lambda p, q: ans[p], strategy="longest")
    assert res.merged == ans["b"]
