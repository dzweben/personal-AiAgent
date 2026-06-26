"""tests for the corpus store."""

from __future__ import annotations

from agent.scholar.corpus import Corpus
from agent.scholar.paper import Paper

_PAPERS = [
    Paper(title="Caffeine and sleep quality", abstract="caffeine delays sleep onset in adults", doi="10.1/a"),
    Paper(title="Exercise and heart health", abstract="running improves cardiovascular outcomes", doi="10.2/b"),
]


def test_add_dedupes():
    c = Corpus()
    added = c.add([*_PAPERS, Paper(title="Caffeine and sleep quality", abstract="dup", doi="10.1/a")])
    assert added == 2
    assert len(c) == 2


def test_semantic_search_finds_relevant_paper():
    c = Corpus()
    c.add(_PAPERS)
    hits = c.search("how does caffeine affect sleep")
    assert hits[0].title == "Caffeine and sleep quality"


def test_relevance_higher_for_on_topic_paper():
    c = Corpus()
    rel_caffeine = c.relevance("caffeine sleep", _PAPERS[0])
    rel_exercise = c.relevance("caffeine sleep", _PAPERS[1])
    assert rel_caffeine > rel_exercise


def test_persistence(tmp_path):
    path = str(tmp_path / "corpus.jsonl")
    Corpus(path).add(_PAPERS)
    reloaded = Corpus(path)
    assert len(reloaded) == 2
    assert reloaded.search("exercise cardiovascular")[0].doi == "10.2/b"


def test_duplicate_keeps_richer_metadata():
    c = Corpus()
    c.add([Paper(title="Study", doi="10.9/x")])
    c.add([Paper(title="Study", doi="10.9/x", abstract="now with abstract", year=2020)])
    assert len(c) == 1
    assert c.papers[0].abstract == "now with abstract"
