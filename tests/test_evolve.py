"""tests for the expanded genetic prompt optimiser."""

from __future__ import annotations

from agent.evolve import evolve


def test_diversity_history_tracked():
    res = evolve(generations=8, seed=2)
    assert len(res.diversity_history) == len(res.history)
    assert all(0.0 <= d <= 1.0 for d in res.diversity_history)


def test_keep_diverse_maintains_variety():
    diverse = evolve(generations=12, seed=4, keep_diverse=True)
    collapsed = evolve(generations=12, seed=4, keep_diverse=False)
    # diversity-preserving runs should not end up *less* diverse on average
    assert sum(diverse.diversity_history) >= sum(collapsed.diversity_history) - 1e-9


def test_pluggable_operators_are_used():
    calls = {"mutate": 0, "crossover": 0}

    def my_mutate(g, pool, rng):
        calls["mutate"] += 1
        return g

    def my_crossover(a, b, rng):
        calls["crossover"] += 1
        return a

    evolve(generations=4, pop_size=8, seed=1, mutate=my_mutate, crossover=my_crossover)
    assert calls["crossover"] > 0
    assert calls["mutate"] > 0


def test_still_deterministic_under_seed():
    a = evolve(generations=6, seed=9)
    b = evolve(generations=6, seed=9)
    assert a.best == b.best and a.diversity_history == b.diversity_history
