"""tests for the compounding experience layer."""

from __future__ import annotations

from agent.experience import Experience


def test_remember_then_recall(tmp_path):
    exp = Experience(str(tmp_path / "exp"))
    exp.remember(
        "how does caffeine affect sleep",
        "Caffeine blocks adenosine and delays sleep onset.",
        lessons=["always mention the dose-response curve for caffeine"],
    )
    ctx = exp.recall_context("how does caffeine affect sleep quality")
    assert "dose-response" in ctx


def test_recall_empty_when_nothing_relevant(tmp_path):
    exp = Experience(str(tmp_path / "exp"))
    exp.remember("gardening tips", "Water tomatoes in the morning.", lessons=["mention sunlight"])
    assert exp.recall_context("quantum field theory renormalization") == ""


def test_stats_count_lessons_and_notes(tmp_path):
    exp = Experience(str(tmp_path / "exp"))
    exp.remember("q1", "answer one", lessons=["lesson a", "lesson b"])
    exp.remember("q2", "answer two", lessons=["lesson c"])
    stats = exp.stats()
    assert stats["lessons"] == 3 and stats["notes"] == 2


def test_persists_across_instances(tmp_path):
    d = str(tmp_path / "exp")
    Experience(d).remember(
        "caffeine and sleep", "an answer about caffeine", lessons=["cite studies"]
    )
    reopened = Experience(d)
    assert reopened.stats()["notes"] == 1
    assert "cite studies" in reopened.recall_context("caffeine and sleep effects")


def test_remember_uses_extract_when_no_lessons(tmp_path):
    exp = Experience(str(tmp_path / "exp"))
    exp.remember("q", "an answer", extract=lambda q, a: ["derived lesson here"])
    assert exp.stats()["lessons"] == 1
