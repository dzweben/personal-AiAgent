"""tests for the reflection / lessons memory."""

from __future__ import annotations

from agent.reflect import LessonStore, reflect


def _store(tmp_path):
    return LessonStore(path=str(tmp_path / "lessons.sqlite"))


def test_add_and_recall_by_relevance(tmp_path):
    s = _store(tmp_path)
    s.add("caffeine and sleep", "cite the dose-response curve for stimulants")
    s.add("baking bread", "let the dough proof for an hour")
    hits = s.recall("how does caffeine affect sleep quality")
    assert hits
    assert "dose-response" in hits[0].lesson


def test_recall_ranks_by_overlap(tmp_path):
    s = _store(tmp_path)
    s.add("python testing", "use fixtures for setup and teardown")
    s.add("gardening", "water tomatoes in the morning")
    hits = s.recall("best practices for python testing with pytest")
    assert hits[0].topic == "python testing"
    assert hits[0].score >= (hits[1].score if len(hits) > 1 else 0)


def test_recall_empty_when_nothing_relevant(tmp_path):
    s = _store(tmp_path)
    s.add("astronomy", "stars fuse hydrogen into helium")
    assert s.recall("how to bake sourdough bread") == []


def test_reflect_caps_at_three_lessons():
    lessons = reflect("q", "a", extract=lambda q, a: ["one", "two", "three", "four", "five"])
    assert lessons == ["one", "two", "three"]


def test_reflect_filters_blank_lessons():
    lessons = reflect("q", "a", extract=lambda q, a: ["real lesson", "", "  "])
    assert lessons == ["real lesson"]
