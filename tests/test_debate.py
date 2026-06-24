"""tests for the expanded debate engine (N-party + convergence)."""

from __future__ import annotations

from agent.debate import run_debate


def test_n_party_debate():
    res = run_debate(
        "q",
        speakers=("optimist", "skeptic", "pragmatist"),
        rounds=2,
        respond=lambda s, q, sf: f"{s} argues",
        moderate=lambda q, sf: "synthesis",
    )
    assert len(res.transcript) == 6  # 3 speakers x 2 rounds
    assert res.rounds_run == 2
    assert not res.converged


def test_convergence_stops_early():
    res = run_debate(
        "q",
        speakers=("a", "b"),
        rounds=6,
        converge_threshold=0.9,
        respond=lambda s, q, sf: "the same identical argument repeated",
        moderate=lambda q, sf: "synthesis",
    )
    assert res.converged
    assert res.rounds_run < 6


def test_no_false_convergence_when_args_differ():
    counter = {"n": 0}

    def respond(s, q, sf):
        counter["n"] += 1
        return f"completely different fresh argument number {counter['n']} with novel words zzz{counter['n']}"

    res = run_debate(
        "q",
        speakers=("a", "b"),
        rounds=3,
        converge_threshold=0.95,
        respond=respond,
        moderate=lambda q, sf: "synth",
    )
    assert res.rounds_run == 3
    assert not res.converged
