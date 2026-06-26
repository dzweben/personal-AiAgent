"""format real citations from Paper metadata, in every style that matters.

the point of grounding in real papers is that citations are real -- so this turns a Paper into
properly formatted references (APA, MLA, Chicago, Vancouver, BibTeX) and matching in-text cites,
and assembles a deduped, sorted reference list. no model needed; it's pure formatting.
"""

from __future__ import annotations

import re

from agent.scholar.paper import Paper

STYLES = ("apa", "mla", "chicago", "vancouver", "bibtex")


def _surname_first(author: str) -> str:
    parts = author.split()
    if len(parts) < 2:
        return author
    return f"{parts[-1]}, {' '.join(p[0] + '.' for p in parts[:-1])}"


def _authors_apa(authors: list[str]) -> str:
    if not authors:
        return "Anonymous"
    formatted = [_surname_first(a) for a in authors]
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return ", ".join(formatted[:19]) + ", ... " + formatted[-1]


def in_text(paper: Paper, style: str = "apa") -> str:
    """an in-text citation marker, e.g. '(Smith et al., 2021)' or '[1]' for vancouver."""
    yr = paper.year if paper.year else "n.d."
    if style == "vancouver":
        return ""  # vancouver uses numeric markers assigned by the reference list
    who = paper.first_author_surname
    if len(paper.authors) == 2:
        who = f"{paper.first_author_surname} & {paper.authors[1].split()[-1]}"
    elif len(paper.authors) > 2:
        who = f"{paper.first_author_surname} et al."
    if style == "mla":
        return f"({who})"
    return f"({who}, {yr})"


def reference(paper: Paper, style: str = "apa") -> str:
    """one formatted reference-list entry in the requested style."""
    style = style.lower()
    yr = paper.year if paper.year else "n.d."
    title = paper.title.rstrip(".")
    venue = paper.venue
    doi = f" https://doi.org/{paper.doi}" if paper.doi else (f" {paper.url}" if paper.url else "")

    if style == "apa":
        return f"{_authors_apa(paper.authors)} ({yr}). {title}. {venue}.{doi}".replace("..", ".")
    if style == "mla":
        author = paper.authors[0] if paper.authors else "Anonymous"
        author = _surname_first(author)
        etal = " et al." if len(paper.authors) > 1 else ""
        return f'{author}{etal}. "{title}." {venue}, {yr}.'
    if style == "chicago":
        return f'{_authors_apa(paper.authors)}. {yr}. "{title}." {venue}.{doi}'
    if style == "vancouver":
        authors = ", ".join(
            f"{a.split()[-1]} {''.join(p[0] for p in a.split()[:-1])}" for a in paper.authors[:6]
        )
        return f"{authors}. {title}. {venue}. {yr}."
    if style == "bibtex":
        return _bibtex(paper)
    raise ValueError(f"unknown style {style!r}; try one of {STYLES}")


def _bibtex(paper: Paper) -> str:
    key = re.sub(r"\W+", "", paper.first_author_surname.lower()) + str(paper.year or "")
    fields = [
        ("title", paper.title),
        ("author", " and ".join(paper.authors)),
        ("year", str(paper.year) if paper.year else ""),
        ("journal", paper.venue),
        ("doi", paper.doi),
    ]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields if v)
    return f"@article{{{key},\n{body}\n}}"


def reference_list(papers: list[Paper], style: str = "apa") -> str:
    """build a full, deduped reference list. APA/MLA/Chicago sort by author; Vancouver numbers."""
    from agent.scholar.paper import dedupe

    papers = dedupe(papers)
    if style == "vancouver":
        return "\n".join(f"{i}. {reference(p, style)}" for i, p in enumerate(papers, 1))
    entries = sorted((reference(p, style) for p in papers), key=lambda s: s.lower())
    return "\n".join(entries)
