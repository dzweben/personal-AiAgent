"""connectors to open scholarly indexes, each normalised to a Paper.

every connector takes an injectable `fetch(url) -> dict` (json) or `fetch_text(url) -> str`
(for arxiv's atom feed), so the parsing is fully testable offline. online, the defaults use
httpx. these indexes are all openly queryable and cover essentially the same literature a
Scholar search would surface -- OpenAlex and Crossref metadata are open (CC0), arXiv and Europe
PMC host open-access full text, Semantic Scholar exposes a public api.

`search_papers` fans out across whichever connectors you enable and merges + dedupes the hits.
"""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from agent.scholar.paper import Paper, dedupe


def _reconstruct_abstract(inverted: dict | None) -> str:
    """OpenAlex ships abstracts as an inverted index {word: [positions]}; rebuild the text."""
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    return " ".join(w for _, w in sorted(positions))


# ---- per-index normalisers ----------------------------------------------------------------


def parse_openalex(payload: dict) -> list[Paper]:
    papers = []
    for w in payload.get("results", []):
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in w.get("authorships", [])
            if a.get("author")
        ]
        papers.append(
            Paper(
                title=w.get("title") or w.get("display_name") or "",
                authors=[a for a in authors if a],
                year=w.get("publication_year"),
                venue=(w.get("host_venue") or {}).get("display_name", "")
                or (w.get("primary_location") or {}).get("source", {}).get("display_name", ""),
                abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
                doi=(w.get("doi") or "").replace("https://doi.org/", ""),
                url=w.get("id", ""),
                source="openalex",
                citations=w.get("cited_by_count", 0) or 0,
                open_access=bool((w.get("open_access") or {}).get("is_oa")),
            )
        )
    return papers


def parse_crossref(payload: dict) -> list[Paper]:
    papers = []
    for it in payload.get("message", {}).get("items", []):
        authors = [
            " ".join(filter(None, [a.get("given"), a.get("family")])) for a in it.get("author", [])
        ]
        year = None
        parts = (it.get("issued") or {}).get("date-parts") or [[None]]
        if parts and parts[0]:
            year = parts[0][0]
        papers.append(
            Paper(
                title=" ".join(it.get("title", [])) if it.get("title") else "",
                authors=[a for a in authors if a],
                year=year,
                venue=" ".join(it.get("container-title", [])),
                abstract=re.sub(r"<[^>]+>", "", it.get("abstract", "")),
                doi=it.get("DOI", ""),
                url=it.get("URL", ""),
                source="crossref",
                citations=it.get("is-referenced-by-count", 0) or 0,
            )
        )
    return papers


def parse_semantic_scholar(payload: dict) -> list[Paper]:
    papers = []
    for p in payload.get("data", []):
        papers.append(
            Paper(
                title=p.get("title") or "",
                authors=[a.get("name", "") for a in p.get("authors", [])],
                year=p.get("year"),
                venue=p.get("venue", ""),
                abstract=p.get("abstract") or "",
                doi=(p.get("externalIds") or {}).get("DOI", ""),
                url=p.get("url", ""),
                source="semantic_scholar",
                citations=p.get("citationCount", 0) or 0,
                open_access=bool(p.get("isOpenAccess")),
            )
        )
    return papers


def parse_europepmc(payload: dict) -> list[Paper]:
    papers = []
    for r in payload.get("resultList", {}).get("result", []):
        authors = [r["authorString"]] if r.get("authorString") else []
        papers.append(
            Paper(
                title=r.get("title", "").rstrip("."),
                authors=authors,
                year=int(r["pubYear"]) if r.get("pubYear", "").isdigit() else None,
                venue=r.get("journalTitle", ""),
                abstract=r.get("abstractText", ""),
                doi=r.get("doi", ""),
                url=f"https://europepmc.org/article/{r.get('source','')}/{r.get('id','')}",
                source="europepmc",
                citations=r.get("citedByCount", 0) or 0,
                open_access=r.get("isOpenAccess") == "Y",
            )
        )
    return papers


def parse_arxiv(atom: str) -> list[Paper]:
    """arxiv returns an atom xml feed; pull the fields we need without a heavy xml dep."""
    papers = []
    for entry in re.findall(r"<entry>(.*?)</entry>", atom, re.DOTALL):

        def grab(tag, e=entry):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", e, re.DOTALL)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

        authors = re.findall(r"<author>\s*<name>(.*?)</name>", entry, re.DOTALL)
        published = grab("published")
        year = int(published[:4]) if published[:4].isdigit() else None
        papers.append(
            Paper(
                title=grab("title"),
                authors=[a.strip() for a in authors],
                year=year,
                venue="arXiv",
                abstract=grab("summary"),
                url=grab("id"),
                source="arxiv",
                open_access=True,
            )
        )
    return papers


# ---- connector factories ------------------------------------------------------------------

CONNECTORS = {
    "openalex": (
        lambda q, n: f"https://api.openalex.org/works?search={quote_plus(q)}&per_page={n}",
        parse_openalex,
        "json",
    ),
    "crossref": (
        lambda q, n: f"https://api.crossref.org/works?query={quote_plus(q)}&rows={n}",
        parse_crossref,
        "json",
    ),
    "semantic_scholar": (
        lambda q, n: (
            "https://api.semanticscholar.org/graph/v1/paper/search?"
            f"query={quote_plus(q)}&limit={n}&fields=title,abstract,year,authors,venue,"
            "citationCount,externalIds,url,isOpenAccess"
        ),
        parse_semantic_scholar,
        "json",
    ),
    "europepmc": (
        lambda q, n: (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
            f"query={quote_plus(q)}&format=json&pageSize={n}&resultType=core"
        ),
        parse_europepmc,
        "json",
    ),
    "arxiv": (
        lambda q, n: f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(q)}&max_results={n}",
        parse_arxiv,
        "text",
    ),
}


def search_papers(
    query: str,
    indexes: list[str] | None = None,
    limit: int = 10,
    fetch_json=None,
    fetch_text=None,
) -> list[Paper]:
    """search the enabled indexes, normalise, merge, and dedupe. injectable fetchers for tests."""
    indexes = indexes or ["openalex", "semantic_scholar"]
    if fetch_json is None:
        fetch_json = _default_fetch_json
    if fetch_text is None:
        fetch_text = _default_fetch_text

    all_papers: list[Paper] = []
    for name in indexes:
        if name not in CONNECTORS:
            continue
        build_url, parse, kind = CONNECTORS[name]
        url = build_url(query, limit)
        try:
            payload = fetch_text(url) if kind == "text" else fetch_json(url)
            all_papers.extend(parse(payload))
        except Exception:  # noqa: BLE001 - one dead index shouldn't sink the search
            continue
    return dedupe([p for p in all_papers if p.title])


def _default_fetch_json(url: str) -> dict:  # pragma: no cover - network
    import httpx

    r = httpx.get(url, timeout=30, headers={"User-Agent": "personal-aiagent/0.2 (research)"})
    r.raise_for_status()
    return r.json()


def _default_fetch_text(url: str) -> str:  # pragma: no cover - network
    import httpx

    r = httpx.get(url, timeout=30, headers={"User-Agent": "personal-aiagent/0.2 (research)"})
    r.raise_for_status()
    return r.text
