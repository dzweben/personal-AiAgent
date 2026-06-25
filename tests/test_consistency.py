"""tests for self-consistency sampling."""

from __future__ import annotations

from agent.consistency import cluster, self_consistency


def test_cluster_groups_similar_answers():
    answers = [
        "the cat sat on the mat",
        "the cat sat on the mat today",
        "quantum chromodynamics is hard",
    ]
    clusters = cluster(answers, threshold=0.4)
    sizes = sorted(len(c) for c in clusters)
    assert sizes == [1, 2]


def test_majority_cluster_wins():
    samples = [
        "water boils at one hundred degrees celsius",
        "water boils at 100 degrees celsius normally",
        "the moon is made of green cheese entirely",
    ]
    res = self_consistency("q", sample=lambda q, i: samples[i], n=3, threshold=0.3)
    assert "water boils" in res.answer
    assert res.agreed


def test_consistency_score_reflects_agreement():
    # all identical -> consistency 1.0
    same = self_consistency("q", sample=lambda q, i: "identical answer here", n=4)
    assert same.consistency == 1.0
    # all different -> low consistency (genuinely disjoint vocab per sample)
    pools = [
        "alpha bravo charlie delta",
        "echo foxtrot golf hotel",
        "india juliet kilo lima",
        "mike november oscar papa",
    ]
    diff = self_consistency("q", sample=lambda q, i: pools[i], n=4)
    assert diff.consistency < 0.5
    assert not diff.agreed


def test_returns_number_of_samples():
    res = self_consistency("q", sample=lambda q, i: "x", n=6)
    assert res.n_samples == 6
