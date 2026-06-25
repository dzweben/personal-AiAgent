"""tests for semantic memory (deterministic, offline embedder)."""

from __future__ import annotations

from agent.semantic_memory import SemanticMemory, cosine, embed


def test_embedding_is_deterministic_and_normalised():
    a, b = embed("hello world"), embed("hello world")
    assert a == b
    assert abs(sum(x * x for x in a) - 1.0) < 1e-6  # unit length


def test_similar_text_scores_higher_than_unrelated():
    base = embed("caffeine affects sleep quality")
    near = embed("caffeine affects sleep a lot")
    far = embed("tomatoes grow in the garden")
    assert cosine(base, near) > cosine(base, far)


def test_recall_ranks_by_similarity():
    m = SemanticMemory()
    m.add("caffeine blocks adenosine and delays sleep", topic="caffeine")
    m.add("tomatoes need sun and water", topic="gardening")
    hits = m.recall("how does caffeine affect sleep")
    assert hits[0].meta["topic"] == "caffeine"


def test_recall_filters_below_min_score():
    m = SemanticMemory()
    m.add("astrophysics and stellar nucleosynthesis", topic="space")
    assert m.recall("how to bake banana bread", min_score=0.5) == []


def test_persistence_roundtrip(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    m = SemanticMemory(path)
    m.add("a memorable note", tag="x")
    reloaded = SemanticMemory(path)
    assert len(reloaded) == 1
    assert reloaded.recall("memorable note")[0].meta["tag"] == "x"
