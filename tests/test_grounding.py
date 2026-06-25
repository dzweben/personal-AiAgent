"""tests for web grounding (offline, fake search + fetch)."""

from __future__ import annotations

from agent.grounding import Passage, as_context, grounded_answer, html_to_text, retrieve

_PAGES = {
    "https://good.com": "<html><script>junk()</script><p>Caffeine blocks adenosine and delays sleep onset in adults.</p></html>",
    "https://bad.com": "<p>Bananas are an excellent source of dietary potassium and fiber.</p>",
}


def test_html_to_text_strips_tags_and_scripts():
    out = html_to_text("<div><style>x{}</style><p>Hello <b>there</b></p></div>")
    assert "Hello there" in out
    assert "<" not in out and "style" not in out


def test_retrieve_ranks_relevant_passages_first():
    passages = retrieve(
        "how does caffeine affect sleep",
        search=lambda q: list(_PAGES.keys()),
        fetch=lambda url: _PAGES[url],
    )
    assert passages
    assert passages[0].url == "https://good.com"
    assert "caffeine" in passages[0].text.lower()


def test_retrieve_filters_irrelevant_pages():
    passages = retrieve(
        "caffeine sleep adenosine",
        search=lambda q: list(_PAGES.keys()),
        fetch=lambda url: _PAGES[url],
    )
    # the banana page shares no query terms -> excluded
    assert all("banana" not in p.text.lower() for p in passages)


def test_retrieve_handles_failed_fetch():
    passages = retrieve(
        "anything",
        search=lambda q: ["https://x.com"],
        fetch=lambda url: None,  # fetch failed
    )
    assert passages == []


def test_as_context_includes_citations():
    ctx = as_context([Passage(text="some fact", url="https://src.com", score=1.0)])
    assert "https://src.com" in ctx and "some fact" in ctx


def test_as_context_empty():
    assert "no sources" in as_context([])


def test_grounded_answer_cites_sources():
    retrieve = lambda q: [
        Passage("Caffeine blocks adenosine.", "https://nih.gov/x", 1.0)
    ]  # noqa: E731
    answer = grounded_answer(retrieve, complete=lambda p: "Caffeine delays sleep.")
    out = answer("how does caffeine affect sleep?")
    assert "nih.gov" in out


def test_grounded_answer_passes_context_to_model():
    seen = {}

    def complete(prompt):
        seen["prompt"] = prompt
        return "answer with http://nih.gov/x already cited"

    retrieve = lambda q: [Passage("important fact here", "http://nih.gov/x", 1.0)]  # noqa: E731
    grounded_answer(retrieve, complete=complete)("q")
    assert "important fact here" in seen["prompt"]
    assert "ONLY the sources" in seen["prompt"]
