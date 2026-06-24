"""tests for the genetic persona-mix tuning (offline, fake answerer)."""

from __future__ import annotations

from agent.council_evolve import CANDIDATE_PERSONAS, convene_evolved, evolve_personas


def _biased_answer(good_personas):
    """personas in `good_personas` give a strong answer; everyone else gives a weak one."""
    strong = "The subject has documented effects backed by evidence; see https://example.org for 3 studies."
    weak = "maybe, perhaps it depends, hard to say really."

    def answer(persona, q):
        return strong if persona in good_personas else weak

    return answer


def test_evolution_prefers_the_strong_personas():
    res = evolve_personas(
        "q", answer=_biased_answer({"researcher", "journalist"}), generations=10, seed=3
    )
    # the winning line-up should include at least one strong persona
    assert any(p in res.personas for p in ("researcher", "journalist"))
    assert res.fitness >= res.history[0]
    assert all(p in CANDIDATE_PERSONAS for p in res.personas)


def test_evolution_is_deterministic_under_seed():
    a = evolve_personas("q", answer=_biased_answer({"researcher"}), generations=6, seed=5)
    b = evolve_personas("q", answer=_biased_answer({"researcher"}), generations=6, seed=5)
    assert a.personas == b.personas and a.fitness == b.fitness


def test_convene_evolved_runs_council_with_found_personas():
    def fake(prompt):
        if "HOLDS or BREAKS" in prompt:
            return "HOLDS"
        if "supported, refuted" in prompt:
            return "supported"
        if "Reply OK if fine" in prompt:
            return "OK"
        if "As a" in prompt:
            return "Documented effects with evidence at https://x.org across 3 studies."
        return "x"

    result, search = convene_evolved("q", complete=fake, seed=1)
    assert result.answer
    assert search.personas  # a line-up was chosen
    assert 0.0 <= result.scorecard.overall <= 1.0
