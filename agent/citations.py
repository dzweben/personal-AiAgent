"""little citation helper.

turns the agent's sources into numbered references and can spit out a bibliography in a
couple of styles. nothing academic-grade, just enough to make a report look tidy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime

from agent.models import Source


def normalise_sources(raw: Iterable) -> list[Source]:
    """accept a mix of strings and Source objects and give back Source objects."""
    out: list[Source] = []
    for item in raw:
        if isinstance(item, Source):
            out.append(item)
        elif isinstance(item, str):
            if item.startswith(("http://", "https://")):
                out.append(Source(url=item))
            else:
                out.append(Source(title=item))
        elif isinstance(item, dict):
            out.append(Source(**item))
    return out


def _domain(url: str | None) -> str:
    if not url:
        return ""
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1).replace("www.", "") if m else ""


def numbered(sources: Iterable) -> str:
    """[1] title (url) style list."""
    srcs = normalise_sources(sources)
    if not srcs:
        return "(no sources)"
    return "\n".join(f"[{i}] {s.short()}" for i, s in enumerate(srcs, 1))


def bibliography(sources: Iterable, style: str = "plain") -> str:
    srcs = normalise_sources(sources)
    if not srcs:
        return "(no sources)"
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    for s in srcs:
        title = s.title or _domain(s.url) or "Untitled"
        if style == "apa":
            lines.append(f"{title}. Retrieved {today}, from {s.url or 'n/a'}")
        elif style == "mla":
            lines.append(f'"{title}." Web. {today}. <{s.url or "n/a"}>.')
        else:
            lines.append(f"- {title} | {s.url or 'no url'}")
    return "\n".join(lines)


def inline_map(sources: Iterable) -> dict[str, int]:
    """map a source url/title to its citation number, handy for inserting [n] markers."""
    srcs = normalise_sources(sources)
    return {(s.url or s.title or ""): i for i, s in enumerate(srcs, 1)}
