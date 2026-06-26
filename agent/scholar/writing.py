"""turn a synthesised body of literature into actual prose -- grounded, with real citations.

this is where papers become writing. it builds an outline (for a literature review, an empirical
IMRaD paper, or a proposal), then drafts each section *from the papers you give it*, weaving in
real in-text citations. the model is injectable and is told to use only the supplied sources and
cite them, so it can't invent references -- every (Author, Year) traces back to a Paper.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.scholar.citations import in_text, reference_list
from agent.scholar.paper import Paper
from agent.scholar.synthesis import themes

# section skeletons per document kind.
OUTLINES = {
    "review": [
        "Introduction",
        "Methods of this review",
        "Themes in the literature",
        "Discussion",
        "Gaps and future directions",
        "Conclusion",
    ],
    "empirical": ["Introduction", "Methods", "Results", "Discussion", "Limitations", "Conclusion"],
    "proposal": [
        "Background",
        "Problem statement",
        "Research questions",
        "Proposed methods",
        "Expected contribution",
    ],
    "annotated-bibliography": ["Overview"],
}


@dataclass
class Section:
    heading: str
    body: str = ""
    cited: list[str] = field(default_factory=list)  # short refs cited in this section


@dataclass
class Document:
    title: str
    kind: str
    sections: list[Section] = field(default_factory=list)
    references: str = ""

    def to_markdown(self) -> str:
        out = [f"# {self.title}\n"]
        for s in self.sections:
            out.append(f"## {s.heading}\n\n{s.body}\n")
        if self.references:
            out.append("## References\n\n" + self.references)
        return "\n".join(out)


def _sources_block(papers: list[Paper], style: str = "apa") -> str:
    """a compact, citeable listing of the papers a section may draw on."""
    lines = []
    for p in papers:
        marker = in_text(p, style) or p.short_ref()
        lines.append(f"- {marker} {p.title}. {p.abstract[:240]}")
    return "\n".join(lines)


def _style_system(style: str, heading: str) -> str:
    """the system prompt that governs writing voice. for APA, the full style engine drives it."""
    if style == "apa":
        from agent.scholar.apa import style_prompt

        return style_prompt(heading) + (
            "\n\nWrite the requested section using ONLY the provided sources, weaving in their "
            "in-text citations exactly as given. Never invent a citation, fact, or paper."
        )
    return (
        "You are an academic writer. Write the requested section using ONLY the provided sources. "
        "Weave in their in-text citations exactly as given. Do not invent citations or facts."
    )


def draft_section(
    heading: str,
    topic: str,
    papers: list[Paper],
    complete,
    style: str = "apa",
    settings=None,
    enforce_apa: bool = True,
) -> Section:
    """draft one section grounded strictly in `papers`, in the requested writing style.

    when style is 'apa' and enforce_apa is set, the draft is run through the APA style checker and,
    if it has violations, sent back to the model once for an APA-compliant rewrite.
    """
    if not papers:
        return Section(heading=heading, body="", cited=[])
    sources = _sources_block(papers, style)
    sys = _style_system(style, heading)
    body = complete(
        f"Topic: {topic}\nSection to write: {heading}\n\nSources you may cite:\n{sources}",
        settings=settings,
        system=sys,
    ).strip()

    if style == "apa" and enforce_apa:
        from agent.scholar.apa import check_apa, suggest_revisions

        # stage 1: apply the unambiguous mechanical fixes (wordiness, biased terms, spacing)
        body = suggest_revisions(body)
        # stage 2: anything left (tense, voice, flow, overclaiming) goes back to the model once
        remaining = check_apa(body)
        if remaining:
            issues = "; ".join(f"{v.snippet} ({v.suggestion})" for v in remaining[:10])
            body = complete(
                f"Rewrite the passage below to fix these APA style issues, preserving every "
                f"citation: {issues}\n\n{body}",
                settings=settings,
                system=sys,
            ).strip()

    cited = [p.short_ref() for p in papers if p.first_author_surname in body]
    return Section(heading=heading, body=body, cited=cited)


def write_document(
    topic: str,
    papers: list[Paper],
    kind: str = "review",
    complete=None,
    style: str = "apa",
    settings=None,
    section_for=None,
) -> Document:
    """assemble a full grounded document: outline, draft each section, append references.

    `section_for(heading, topic, papers) -> Section` is injectable for offline testing; by default
    each section is drafted with the llm via draft_section, fed the papers most relevant to it.
    """
    headings = OUTLINES.get(kind, OUTLINES["review"])
    doc = Document(title=f"{topic}: a {kind}", kind=kind)

    # rough routing of papers to sections: theme-heavy sections get the clustered papers
    theme_list = themes(papers)

    def papers_for(heading: str) -> list[Paper]:
        h = heading.lower()
        if "theme" in h or "result" in h or "background" in h or "discussion" in h:
            return papers
        if "gap" in h or "future" in h:
            return [t.papers[0] for t in theme_list if t.papers]
        return papers[: max(3, len(papers) // 2)]

    for heading in headings:
        sec_papers = papers_for(heading)
        if section_for is not None:
            doc.sections.append(section_for(heading, topic, sec_papers))
        else:
            doc.sections.append(
                draft_section(heading, topic, sec_papers, complete, style, settings)
            )

    doc.references = reference_list(papers, style)
    return doc
