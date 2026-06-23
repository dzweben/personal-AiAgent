"""web tools: duckduckgo search plus a couple of plain http helpers.

the duckduckgo search is the one that survived from the very first version of this
project. the http_get / fetch_url tools are new and let the agent actually read pages.
"""

from __future__ import annotations

from langchain.tools import Tool

from agent.tools import register


@register("search")
def make_search():
    from langchain_community.tools import DuckDuckGoSearchRun

    search = DuckDuckGoSearchRun()
    return Tool(
        name="search",
        func=search.run,
        description="Search the web for information using DuckDuckGo. Input is a search query.",
    )


def _http_get(url: str) -> str:
    import httpx

    url = url.strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        resp = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "personal-aiagent/0.2"})
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return f"could not fetch {url}: {exc}"
    text = resp.text
    return text[:8000]


@register("http_get")
def make_http_get():
    return Tool(
        name="http_get",
        func=_http_get,
        description=(
            "Fetch the raw contents of a URL over HTTP(S). Input is a single URL. "
            "Returns up to the first 8000 characters of the response body."
        ),
    )


def _fetch_readable(url: str) -> str:
    """fetch a page and try to strip it down to readable text."""
    raw = _http_get(url)
    if raw.startswith("could not fetch"):
        return raw
    try:
        import re

        # cheap and cheerful html to text, good enough for the agent to skim
        no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        no_tags = re.sub(r"<[^>]+>", " ", no_scripts)
        collapsed = re.sub(r"\s+", " ", no_tags).strip()
        return collapsed[:6000]
    except Exception:  # noqa: BLE001
        return raw


@register("fetch_url")
def make_fetch_url():
    return Tool(
        name="fetch_url",
        func=_fetch_readable,
        description=(
            "Fetch a web page and return cleaned up readable text (tags stripped). "
            "Use this when you want to actually read an article rather than just search."
        ),
    )
