"""developer-ish lookup tools: hacker news, github repo search, and a dictionary.

all three use free, no-key public apis over plain http, so they need nothing but httpx.
"""

from __future__ import annotations

from langchain_core.tools import Tool

from agent.tools import register


def _hackernews(query: str) -> str:
    import httpx

    try:
        resp = httpx.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": 5},
            timeout=15,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception as exc:  # noqa: BLE001
        return f"hacker news lookup failed: {exc}"
    if not hits:
        return "no stories found"
    lines = []
    for h in hits[:5]:
        title = h.get("title") or h.get("story_title") or "untitled"
        points = h.get("points", 0)
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        lines.append(f"{title} ({points} points)\n{url}")
    return "\n\n".join(lines)


@register("hackernews")
def make_hackernews():
    return Tool(
        name="hackernews",
        func=_hackernews,
        description="Search Hacker News stories on a topic. Input is a search query.",
    )


def _github_search(query: str) -> str:
    import httpx

    try:
        resp = httpx.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "per_page": 5},
            headers={"Accept": "application/vnd.github+json"},
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as exc:  # noqa: BLE001
        return f"github search failed: {exc}"
    if not items:
        return "no repositories found"
    lines = []
    for repo in items[:5]:
        lines.append(
            f"{repo.get('full_name')} ({repo.get('stargazers_count', 0)} stars)\n"
            f"{repo.get('description') or 'no description'}\n{repo.get('html_url')}"
        )
    return "\n\n".join(lines)


@register("github_search")
def make_github_search():
    return Tool(
        name="github_search",
        func=_github_search,
        description="Search GitHub for repositories, sorted by stars. Input is a search query.",
    )


def _define(word: str) -> str:
    import httpx

    word = word.strip().split()[0] if word.strip() else ""
    if not word:
        return "give me a word to define"
    try:
        resp = httpx.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return f"could not look up {word}: {exc}"
    if not isinstance(data, list) or not data:
        return f"no definition found for {word}"
    out = [f"{word}:"]
    for meaning in data[0].get("meanings", [])[:3]:
        pos = meaning.get("partOfSpeech", "")
        for d in meaning.get("definitions", [])[:2]:
            out.append(f"  ({pos}) {d.get('definition')}")
    return "\n".join(out)


@register("dictionary")
def make_dictionary():
    return Tool(
        name="dictionary",
        func=_define,
        description="Get the definition of an English word. Input is a single word.",
    )
