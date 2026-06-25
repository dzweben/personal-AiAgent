"""tests for argument mapping."""

from __future__ import annotations

from agent.argmap import build_argmap


def test_attack_edge_between_opposing_turns():
    turns = [
        ("optimist", "Nuclear power is safe for large-scale generation."),
        ("skeptic", "Nuclear power is not safe for large-scale generation."),
    ]
    amap = build_argmap(turns)
    assert len(amap.attacks()) == 1
    assert amap.attacks()[0].kind == "attack"


def test_support_edge_between_same_speaker_agreeing():
    turns = [
        ("optimist", "Solar power keeps getting cheaper every year."),
        ("skeptic", "But solar power is intermittent without storage."),
        ("optimist", "Solar power keeps getting cheaper and more efficient every year."),
    ]
    amap = build_argmap(turns)
    assert any(e.kind == "support" for e in amap.edges)


def test_unrelated_turns_have_no_edges():
    turns = [
        ("a", "The Great Wall of China is very long."),
        ("b", "Photosynthesis happens in chloroplasts."),
    ]
    assert build_argmap(turns).edges == []


def test_contested_lists_attacked_nodes():
    turns = [
        ("a", "Coffee improves focus in adults."),
        ("b", "Coffee does not improve focus in adults."),
    ]
    amap = build_argmap(turns)
    assert amap.contested()  # at least one node is attacked


def test_nodes_use_headline_sentence():
    turns = [("a", "Coffee helps focus. It also has downsides like jitters.")]
    amap = build_argmap(turns)
    assert amap.nodes[0].claim == "Coffee helps focus."
