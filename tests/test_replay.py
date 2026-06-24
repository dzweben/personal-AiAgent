"""tests for the run recorder."""

from __future__ import annotations

from agent.replay import Recorder


def test_record_and_serialize():
    rec = Recorder("council run")
    rec.record("route", "picked research", mode="research")
    rec.record("score", "graded 0.8", overall=0.8)
    d = rec.to_dict()
    assert d["title"] == "council run"
    assert len(d["moves"]) == 2
    assert d["moves"][0]["data"]["mode"] == "research"


def test_dict_roundtrip():
    rec = Recorder("x").record("a", "did a").record("b", "did b", n=2)
    again = Recorder.from_dict(rec.to_dict())
    assert again.to_dict() == rec.to_dict()


def test_capsule_roundtrip():
    rec = Recorder("y").record("step", "summary", value=[1, 2, 3])
    cap = rec.to_capsule()
    assert cap.startswith("AICAP1:")
    restored = Recorder.from_capsule(cap)
    assert restored.moves[0].data["value"] == [1, 2, 3]


def test_pretty_lists_moves():
    rec = Recorder("z").record("one", "first").record("two", "second")
    out = rec.pretty()
    assert "1. one" in out and "2. two" in out
