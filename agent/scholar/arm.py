"""the research-writing arm: one call from a topic to a grounded, cited literature review.

ResearchWriter chains the whole scholar pipeline:

    search open indexes -> keep only empirical studies + reviews -> stash in a corpus
      -> grade & rank by evidence -> synthesise themes / gaps / trends
      -> draft a fully-cited document with a real reference list

every external touchpoint (paper search, the model) is injectable, so the arm is testable
offline; online it pulls real papers and writes from them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.scholar.classify import keep_scholarly
from agent.scholar.corpus import Corpus
from agent.scholar.paper import Paper
from agent.scholar.quality import rank_by_quality
from agent.scholar.synthesis import consensus, gaps, themes, timeline
from agent.scholar.writing import Document, write_document


@dataclass
class ReviewResult:
    topic: str
    document: Document
    papers: list[Paper] = field(default_factory=list)
    themes: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    timeline: dict = field(default_factory=dict)
    agreement: str = ""

    @property
    def n_papers(self) -> int:
        return len(self.papers)

    def to_markdown(self) -> str:
        """the document, plus an evidence-base appendix so the reader sees what it rests on."""
        lines = [self.document.to_markdown(), "\n## Evidence base\n"]
        lines.append(
            f"Synthesised {self.n_papers} papers; the literature looks **{self.agreement}**. "
            f"Active years: {', '.join(str(y) for y in self.timeline)}.\n"
        )
        for p, g in rank_by_quality(self.papers):
            lines.append(f"- [{g.label}] {p.short_ref()} — {p.title}")
        if self.gaps:
            lines.append("\n### Identified gaps\n")
            lines += [f"- {x}" for x in self.gaps]
        return "\n".join(lines)


class ResearchWriter:
    def __init__(self, search=None, complete=None, settings=None, corpus=None):
        self.search = search  # search(topic, limit) -> list[Paper]
        self.complete = complete
        self.settings = settings
        self.corpus = corpus if corpus is not None else Corpus()

    def gather(self, topic: str, limit: int = 20) -> list[Paper]:
        """search, keep only empirical studies + reviews, and add them to the corpus."""
        if self.search is not None:
            raw = self.search(topic, limit)
        else:
            from agent.scholar.sources import search_papers

            raw = search_papers(topic, limit=limit)
        scholarly = keep_scholarly(raw)
        self.corpus.add(scholarly)
        return scholarly

    def review(
        self,
        topic: str,
        kind: str = "review",
        style: str = "apa",
        max_papers: int = 20,
        section_for=None,
    ) -> ReviewResult:
        """gather the literature and write a grounded, cited document about `topic`."""
        papers = self.gather(topic, limit=max_papers)
        # write from the strongest evidence first
        ranked = [p for p, _ in rank_by_quality(papers)]

        document = write_document(
            topic,
            ranked,
            kind=kind,
            complete=self.complete,
            style=style,
            settings=self.settings,
            section_for=section_for,
        )
        return ReviewResult(
            topic=topic,
            document=document,
            papers=ranked,
            themes=themes(ranked),
            gaps=gaps(ranked),
            timeline=timeline(ranked),
            agreement=consensus(ranked)["agreement"],
        )


def write_review(topic: str, search=None, complete=None, settings=None, **kw) -> ReviewResult:
    """convenience: build a ResearchWriter and produce a review in one call."""
    return ResearchWriter(search=search, complete=complete, settings=settings).review(topic, **kw)
