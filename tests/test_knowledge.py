"""tests for the knowledge graph."""

from __future__ import annotations

from agent.knowledge import KnowledgeGraph, extract_entities


def test_ingest_extracts_triples():
    g = KnowledgeGraph()
    added = g.ingest("Caffeine is a stimulant. Caffeine affects sleep.")
    assert added >= 2
    assert "Caffeine" in g.entities


def test_neighbors_are_bidirectional():
    g = KnowledgeGraph()
    g.ingest("Caffeine affects sleep.")
    assert "sleep" in {n.lower() for n in g.neighbors("Caffeine")}
    assert "caffeine" in {n.lower() for n in g.neighbors("sleep")}


def test_path_connects_entities_across_hops():
    g = KnowledgeGraph()
    g.ingest("Caffeine affects sleep.")
    g.ingest("Sleep requires melatonin.")
    path = g.path("Caffeine", "melatonin")
    assert path is not None
    assert path[0] == "caffeine" and path[-1] == "melatonin"


def test_path_none_when_unconnected():
    g = KnowledgeGraph()
    g.ingest("Caffeine affects sleep.")
    g.ingest("Gravity bends light.")
    assert g.path("Caffeine", "light") is None


def test_extract_entities_skips_stopwords():
    ents = extract_entities("The NASA team studied Mars. It was a long mission.")
    assert "NASA" in ents and "Mars" in ents
    assert "The" not in ents and "It" not in ents
