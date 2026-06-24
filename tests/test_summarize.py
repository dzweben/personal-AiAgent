"""tests for the map-reduce summarizer (offline, fake summariser)."""

from __future__ import annotations

from agent.summarize import chunk, summarize


def test_chunk_short_text_is_one_chunk():
    assert chunk("hello world", 100) == ["hello world"]
    assert chunk("", 100) == []


def test_chunk_splits_large_text():
    chunks = chunk("word " * 500, size=200)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


def test_chunk_hard_splits_a_giant_paragraph():
    giant = "x" * 1000  # no spaces, one paragraph
    chunks = chunk(giant, size=100)
    assert len(chunks) >= 10


def test_summarize_maps_then_reduces():
    # fake summariser: just take the first 5 chars and tag it
    calls = []

    def fake(text):
        calls.append(text)
        return text.strip()[:5]

    out = summarize("alpha " * 300, summarize_one=fake, chunk_size=150)
    # more than one chunk means map (per chunk) + at least one reduce call
    assert len(calls) > 1
    assert isinstance(out, str) and out


def test_summarize_single_chunk_calls_once():
    calls = []
    summarize("short text", summarize_one=lambda t: calls.append(t) or "ok", chunk_size=500)
    assert len(calls) == 1
