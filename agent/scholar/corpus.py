"""a local library of papers the arm has gathered, searchable by meaning.

once you've searched the open indexes, you want to keep what you found: dedupe it, hold it,
and pull the most relevant papers back out for a given section you're writing. the corpus does
that -- it stores Paper records, indexes their title+abstract into semantic memory, and answers
"which of my papers are about X?" it persists to disk so a literature project survives restarts.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent.scholar.paper import Paper, dedupe
from agent.semantic_memory import SemanticMemory, embed


class Corpus:
    def __init__(self, path: str | None = None):
        self.path = path
        self._papers: dict[str, Paper] = {}
        self._index = SemanticMemory()  # in-memory semantic index over title+abstract
        if path and Path(path).exists():
            self._load()

    def _load(self) -> None:
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    self._add_paper(Paper.from_dict(json.loads(line)), persist=False)

    def _add_paper(self, paper: Paper, persist: bool = True) -> bool:
        if paper.key in self._papers:
            # keep the richer of the two duplicates
            self._papers[paper.key] = dedupe([self._papers[paper.key], paper])[0]
            return False
        self._papers[paper.key] = paper
        self._index.add(f"{paper.title}. {paper.abstract}", key=paper.key)
        if persist and self.path:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(paper.to_dict()) + "\n")
        return True

    def add(self, papers: list[Paper]) -> int:
        """add papers, skipping duplicates. returns how many new ones landed."""
        return sum(self._add_paper(p) for p in dedupe(papers))

    def __len__(self) -> int:
        return len(self._papers)

    @property
    def papers(self) -> list[Paper]:
        return list(self._papers.values())

    def search(self, query: str, k: int = 5) -> list[Paper]:
        """return the k papers most semantically relevant to the query."""
        hits = self._index.recall(query, k=k, min_score=0.0)
        out = []
        for note in hits:
            key = note.meta.get("key")
            if key in self._papers:
                out.append(self._papers[key])
        return out

    def relevance(self, query: str, paper: Paper) -> float:
        """cosine similarity between a query and a paper's text (for ranking/weighting)."""
        from agent.semantic_memory import cosine

        return round(cosine(embed(query), embed(f"{paper.title}. {paper.abstract}")), 4)
