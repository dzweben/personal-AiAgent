"""grounding: actually go read the web instead of trusting the model's memory.

this is the jump from "clever" to "useful". given a query, it searches, fetches the top pages
(in parallel), strips them to readable text, splits them into passages, and ranks the passages
by relevance to the query. the result is a block of real, cited context you can hand to the
model -- so answers are grounded in sources with urls, not vibes.

search and fetch are injectable, so the whole pipeline tests offline with fakes; the defaults
use the project's existing DuckDuckGo + httpx tools when you're online.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agent.parallel import map_parallel

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_ANYTAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


@dataclass
class Passage:
    text: str
    url: str
    score: float = 0.0


def html_to_text(html: str) -> str:
    """crude but dependable html -> text: drop script/style, strip tags, unwrap entities."""
    if "<" not in html:
        return _WS_RE.sub(" ", html).strip()
    no_blocks = _TAG_RE.sub(" ", html)
    no_tags = _ANYTAG_RE.sub(" ", no_blocks)
    unescaped = (
        no_tags.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    return _WS_RE.sub(" ", unescaped).strip()


def _passages(text: str, size: int = 500) -> list[str]:
    """split readable text into passage-sized chunks on sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) + 1 <= size:
            buf = f"{buf} {s}".strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    return chunks


def _relevance(query: str, passage: str) -> float:
    q = set(re.findall(r"\w+", query.lower()))
    p = set(re.findall(r"\w+", passage.lower()))
    if not q or not p:
        return 0.0
    return len(q & p) / len(q)


def retrieve(
    query: str,
    search,
    fetch,
    k_pages: int = 3,
    k_passages: int = 5,
    workers: int = 4,
) -> list[Passage]:
    """search -> fetch top pages in parallel -> extract & rank passages. best passages first.

    `search(query) -> list[str urls]` (or list of (title, url)); `fetch(url) -> html/text`.
    """
    hits = search(query) or []
    urls = [(h[1] if isinstance(h, (tuple, list)) else h) for h in hits][:k_pages]

    pages = map_parallel(fetch, urls, workers=workers)
    passages: list[Passage] = []
    for url, raw in zip(urls, pages, strict=False):
        if not raw:
            continue
        text = html_to_text(raw)
        for chunk in _passages(text):
            passages.append(Passage(text=chunk, url=url, score=_relevance(query, chunk)))

    passages = [p for p in passages if p.score > 0]
    passages.sort(key=lambda p: p.score, reverse=True)
    return passages[:k_passages]


def as_context(passages: list[Passage]) -> str:
    """format ranked passages into a cited context block for a prompt."""
    if not passages:
        return "(no sources found)"
    lines = []
    for i, p in enumerate(passages, 1):
        lines.append(f"[{i}] ({p.url})\n{p.text}")
    return "\n\n".join(lines)


def grounded_answer(retrieve_fn, complete, settings=None):
    """build an answer(question) that reads real sources first, then answers citing them.

    this is the function the deep-research pipeline plugs in when you want grounded, cited
    answers instead of model-memory ones. `retrieve_fn(question) -> [Passage]` and
    `complete(prompt) -> str` are both injectable, so it tests offline.
    """

    def answer(question: str) -> str:
        passages = retrieve_fn(question)
        context = as_context(passages)
        urls = " ".join(dict.fromkeys(p.url for p in passages))  # unique, order-preserved
        prompt = (
            f"Use ONLY the sources below to answer. Cite the urls you used.\n\n"
            f"Sources:\n{context}\n\nQuestion: {question}"
        )
        body = complete(prompt)
        # make sure the source urls are present so downstream source-extraction can see them
        if urls and "http" not in body:
            body = f"{body}\n\nSources: {urls}"
        return body

    return answer


def default_retriever(k_pages: int = 3, k_passages: int = 5):
    """build a retrieve() bound to the project's real search + fetch tools (needs network)."""
    from agent.tools.web import _fetch_readable

    def search(query: str):
        from langchain_community.tools import DuckDuckGoSearchResults

        raw = DuckDuckGoSearchResults().run(query)
        return re.findall(r"https?://[^\s,\]]+", raw)

    def fetch(url: str) -> str:
        return _fetch_readable(url)

    def _retrieve(query: str) -> list[Passage]:
        return retrieve(query, search, fetch, k_pages=k_pages, k_passages=k_passages)

    return _retrieve
