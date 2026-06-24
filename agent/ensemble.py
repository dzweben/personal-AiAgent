"""ask the same question from several angles, then reconcile the answers.

run a query through N personas (researcher, skeptic, eli5, …), collect their answers, and merge
them -- either by a model-written synthesis or, offline, by a simple longest/most-agreed pick.
it's the "wisdom of crowds, except the crowd is all you" feature, and it feeds the council.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DEFAULT_PERSONAS = ["researcher", "skeptic", "eli5"]


@dataclass
class EnsembleResult:
    query: str
    answers: dict[str, str] = field(default_factory=dict)
    merged: str = ""

    def pretty(self) -> str:
        lines = [f"Q: {self.query}", ""]
        for persona, ans in self.answers.items():
            lines.append(f"[{persona}] {ans}")
        if self.merged:
            lines += ["", f"[merged] {self.merged}"]
        return "\n".join(lines)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def vote(answers: list[str]) -> str:
    """pick the answer that's most similar to the others (a cheap consensus proxy).

    similarity is bag-of-words overlap; ties break toward the longer answer. fully offline.
    """
    if not answers:
        return ""
    if len(answers) == 1:
        return answers[0]
    token_sets = [set(_normalize(a).split()) for a in answers]

    def agreement(i: int) -> float:
        a = token_sets[i]
        if not a:
            return 0.0
        scores = []
        for j, b in enumerate(token_sets):
            if i == j or not b:
                continue
            scores.append(len(a & b) / len(a | b))
        return sum(scores) / len(scores) if scores else 0.0

    best = max(range(len(answers)), key=lambda i: (agreement(i), len(answers[i])))
    return answers[best]


def ensemble(
    query: str,
    personas: list[str] | None = None,
    answer=None,
    merge=None,
    settings=None,
) -> EnsembleResult:
    """gather one answer per persona and merge them. `answer`/`merge` injectable for testing."""
    personas = personas or DEFAULT_PERSONAS
    if answer is None:
        from agent.llm import complete

        def answer(persona: str, q: str) -> str:
            from agent import personas as personas_mod

            try:
                blurb = personas_mod.get(persona).blurb
            except Exception:  # noqa: BLE001 - unknown persona name is fine
                blurb = f"Answer as a {persona}."
            return complete(q, settings=settings, system=f"{blurb} Answer in 3-4 sentences.")

    result = EnsembleResult(query=query)
    for persona in personas:
        result.answers[persona] = answer(persona, query).strip()

    if merge is None:
        result.merged = vote(list(result.answers.values()))
    else:
        result.merged = merge(query, result.answers).strip()
    return result
