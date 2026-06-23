"""news headlines tool. uses newsapi.org if you have a key, otherwise it is a no-op.

this one only registers itself when NEWSAPI_KEY is set, so the agent does not advertise
a tool it cannot actually use.
"""

from __future__ import annotations

import os

from langchain_core.tools import Tool

from agent.tools import register


def _headlines(query: str) -> str:
    import httpx

    key = os.environ.get("NEWSAPI_KEY")
    if not key:
        return "no NEWSAPI_KEY set, cannot fetch news"
    params = {"q": query, "pageSize": 5, "sortBy": "publishedAt", "language": "en", "apiKey": key}
    try:
        resp = httpx.get("https://newsapi.org/v2/everything", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return f"news request failed: {exc}"

    articles = data.get("articles", [])[:5]
    if not articles:
        return "no recent articles found"
    lines = []
    for a in articles:
        title = a.get("title", "untitled")
        src = (a.get("source") or {}).get("name", "?")
        url = a.get("url", "")
        lines.append(f"{title} ({src})\n{url}")
    return "\n\n".join(lines)


@register("news")
def make_news():
    if not os.environ.get("NEWSAPI_KEY"):
        raise RuntimeError("NEWSAPI_KEY not set, skipping news tool")
    return Tool(
        name="news",
        func=_headlines,
        description="Get recent news headlines about a topic. Input is a search query.",
    )
