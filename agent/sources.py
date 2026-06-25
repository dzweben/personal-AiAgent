"""pull the sources out of an answer, dedupe them, and rank them by rough credibility.

an answer with citations is worth more if those citations are any good. this extracts urls
(and bare domains), normalises and dedupes them, and scores each by a small domain-authority
heuristic -- peer-reviewed and government/edu domains rank above random blogs. all offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

_URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
_BARE_DOMAIN_RE = re.compile(r"\b([a-z0-9-]+\.(?:org|edu|gov|com|net|io|ac\.uk))\b", re.IGNORECASE)

# rough authority priors by domain class. not gospel -- just a sane ordering.
_TIER = {
    "gov": 1.0,
    "edu": 0.95,
    "ac.uk": 0.95,
    "who.int": 1.0,
    "nih.gov": 1.0,
    "nature.com": 0.9,
    "science.org": 0.9,
    "ncbi.nlm.nih.gov": 0.95,
    "wikipedia.org": 0.7,
    "org": 0.65,
    "io": 0.5,
    "com": 0.45,
    "net": 0.4,
}
_BLOG_HINTS = ("medium.com", "substack.com", "blogspot.", "wordpress.", "reddit.com", "quora.com")


@dataclass
class Source:
    url: str
    domain: str
    authority: float


def _domain(url: str) -> str:
    host = urlparse(url if "//" in url else f"http://{url}").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def authority(domain: str) -> float:
    """a 0..1 credibility prior for a domain."""
    d = domain.lower()
    if any(b in d for b in _BLOG_HINTS):
        return 0.3
    # most specific match wins: full host, then known second-level, then tld
    for key in sorted(_TIER, key=len, reverse=True):
        if d == key or d.endswith("." + key) or d.endswith(key):
            return _TIER[key]
    return 0.4


def extract_sources(text: str) -> list[Source]:
    """find urls and bare domains in text, dedupe by domain, and score each. best first."""
    found: dict[str, str] = {}  # domain -> best url seen
    for url in _URL_RE.findall(text):
        url = url.rstrip(".,);")
        dom = _domain(url)
        if dom and dom not in found:
            found[dom] = url
    for dom in _BARE_DOMAIN_RE.findall(text):
        dom = dom.lower()
        if dom not in found:
            found[dom] = dom
    sources = [Source(url=u, domain=d, authority=authority(d)) for d, u in found.items()]
    return sorted(sources, key=lambda s: s.authority, reverse=True)


def sourcing_score(text: str) -> float:
    """0..1 overall sourcing strength: how many credible sources back the text."""
    sources = extract_sources(text)
    if not sources:
        return 0.0
    # reward both count (up to 3) and average authority
    avg = sum(s.authority for s in sources) / len(sources)
    coverage = min(1.0, len(sources) / 3)
    return round(0.5 * avg + 0.5 * coverage, 3)
