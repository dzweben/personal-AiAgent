"""the normalized record every scholarly source maps onto.

each index (OpenAlex, Crossref, …) returns a different json shape; a Paper is the one tidy
form the rest of the arm works with. it carries just enough to cite, filter, and write from:
title, authors, year, venue, abstract, doi/url, citation count, and where it came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Paper:
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    abstract: str = ""
    doi: str = ""
    url: str = ""
    source: str = ""  # which index it came from (openalex, arxiv, …)
    citations: int = 0
    open_access: bool = False

    @property
    def key(self) -> str:
        """a dedup key: the doi if we have one, else a normalised title."""
        if self.doi:
            return _norm_doi(self.doi)
        return "title:" + re.sub(r"\W+", " ", self.title.lower()).strip()

    @property
    def first_author(self) -> str:
        return self.authors[0] if self.authors else "Anonymous"

    @property
    def first_author_surname(self) -> str:
        return self.first_author.split()[-1] if self.first_author else "Anonymous"

    def short_ref(self) -> str:
        """a one-line human label, e.g. 'Smith et al. (2021)'."""
        who = self.first_author_surname
        if len(self.authors) == 2:
            who = f"{self.first_author_surname} & {self.authors[1].split()[-1]}"
        elif len(self.authors) > 2:
            who = f"{self.first_author_surname} et al."
        yr = self.year if self.year else "n.d."
        return f"{who} ({yr})"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "abstract": self.abstract,
            "doi": self.doi,
            "url": self.url,
            "source": self.source,
            "citations": self.citations,
            "open_access": self.open_access,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Paper:
        return cls(**{k: d.get(k, getattr(cls, k, None)) for k in cls.__dataclass_fields__})


def _norm_doi(doi: str) -> str:
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return "doi:" + doi


def dedupe(papers: list[Paper]) -> list[Paper]:
    """drop duplicate papers (same doi/title), keeping the one with the richest metadata."""
    best: dict[str, Paper] = {}
    for p in papers:
        cur = best.get(p.key)
        if cur is None or _richness(p) > _richness(cur):
            best[p.key] = p
    return list(best.values())


def _richness(p: Paper) -> int:
    """how complete a record is -- used to pick the better of two duplicates."""
    return (
        bool(p.abstract) * 3
        + bool(p.doi) * 2
        + bool(p.authors)
        + bool(p.venue)
        + bool(p.year)
        + (p.citations > 0)
    )
