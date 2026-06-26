"""synthesise a body of papers the way a literature review should: by theme, not paper-by-paper.

given a pile of papers, this groups them into themes, surfaces where the evidence agrees and
where it clashes, sketches the chronological trend, and flags likely gaps. it's the analytical
spine a good review is built on, and it's all offline heuristics (clustering, contradiction
detection, term frequencies) so it's deterministic and testable -- the prose comes later.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from agent.consistency import cluster
from agent.contradiction import find_contradictions
from agent.scholar.paper import Paper

_STOP = set(
    """the a an and or but of to in on at for with without from by as is are was were be been
    this that these those it its their our we their study studies results effect effects using
    used between among during both can may also more than into over under not no""".split()
)


@dataclass
class Theme:
    label: str
    papers: list[Paper] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.papers)


def _key_terms(text: str, n: int = 3) -> list[str]:
    words = [w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP]
    return [w for w, _ in Counter(words).most_common(n)]


def themes(papers: list[Paper], threshold: float = 0.25) -> list[Theme]:
    """cluster papers into themes by abstract/title similarity. biggest theme first."""
    texts = [f"{p.title}. {p.abstract}" for p in papers]
    clusters = cluster(texts, threshold=threshold)
    # map each clustered text back to its paper
    by_text = dict(zip(texts, papers, strict=False))
    out = []
    for group in clusters:
        members = [by_text[t] for t in group if t in by_text]
        label = ", ".join(_key_terms(" ".join(group))) or "general"
        out.append(Theme(label=label, papers=members))
    out.sort(key=lambda t: t.size, reverse=True)
    return out


def consensus(papers: list[Paper]) -> dict:
    """report how much the abstracts agree: contradictions found vs claims compared."""
    abstracts = [p.abstract for p in papers if p.abstract]
    contradictions = find_contradictions(abstracts)
    return {
        "papers": len(papers),
        "contradictions": contradictions,
        "agreement": "contested" if contradictions else "broadly consistent",
    }


def timeline(papers: list[Paper]) -> dict[int, int]:
    """count papers per year, oldest first -- a quick read on how active the field is."""
    years = Counter(p.year for p in papers if p.year)
    return dict(sorted(years.items()))


def gaps(papers: list[Paper], propose=None) -> list[str]:
    """suggest research gaps. heuristic default; pass `propose(papers)` for a model-written take.

    the offline heuristic flags thin themes (one paper) and mines abstracts for explicit
    "future work / limitations / remains unclear" cues.
    """
    if propose is not None:
        return propose(papers)
    out: list[str] = []
    for theme in themes(papers):
        if theme.size == 1:
            out.append(f"'{theme.label}' rests on a single study; needs replication")
    cue = re.compile(
        r"(future (?:work|research|studies)[^.]*|remains? (?:unclear|unknown)[^.]*|"
        r"limited evidence[^.]*|further (?:research|study)[^.]*)",
        re.IGNORECASE,
    )
    for p in papers:
        for m in cue.findall(p.abstract or ""):
            out.append(f"{p.short_ref()}: {m.strip()}")
    # dedupe while preserving order
    seen, deduped = set(), []
    for g in out:
        if g.lower() not in seen:
            seen.add(g.lower())
            deduped.append(g)
    return deduped[:8]
