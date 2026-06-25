"""break a big question into a graph of smaller ones.

a hard question is usually several easier questions wearing a trenchcoat. the planner pulls
them apart into sub-questions with dependencies, so a downstream executor can answer the
independent ones in parallel and the dependent ones in order. the decomposition is injectable
(an llm does a great job), but there's a real heuristic fallback so it works offline too.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_CONJUNCTIONS = re.compile(r"\s+(?:and|also|as well as|plus|then)\s+|;\s*|\?\s*", re.IGNORECASE)
_WH = ("what", "why", "how", "when", "where", "who", "which", "is", "are", "should", "does")


@dataclass
class SubQuestion:
    text: str
    deps: list[int] = field(default_factory=list)  # indices of sub-questions this one builds on


@dataclass
class Plan:
    question: str
    subquestions: list[SubQuestion] = field(default_factory=list)

    @property
    def is_trivial(self) -> bool:
        return len(self.subquestions) <= 1

    def roots(self) -> list[int]:
        """indices with no dependencies -- the questions that can be answered first."""
        return [i for i, sq in enumerate(self.subquestions) if not sq.deps]

    def pretty(self) -> str:
        lines = [f"plan for: {self.question}"]
        for i, sq in enumerate(self.subquestions):
            dep = f" (after {sq.deps})" if sq.deps else ""
            lines.append(f"  {i}. {sq.text}{dep}")
        return "\n".join(lines)


def naive_decompose(question: str, max_subs: int = 5) -> list[str]:
    """offline split: break a compound question on conjunctions into standalone sub-questions."""
    parts = [p.strip(" ,.;") for p in _CONJUNCTIONS.split(question) if p and p.strip(" ,.;")]
    subs = []
    for part in parts:
        if len(part.split()) < 3:
            continue  # too small to be its own question
        # re-attach a question word if the fragment lost it after a split
        if not part.lower().startswith(_WH):
            part = f"what about: {part}"
        subs.append(part if part.endswith("?") else part + "?")
        if len(subs) >= max_subs:
            break
    return subs or [question]


def decompose(question: str, propose=None, max_subs: int = 5, synthesize: bool = True) -> Plan:
    """produce a Plan. `propose(question) -> list[str]` is injectable; defaults to the heuristic.

    when `synthesize` is set and there's more than one sub-question, a final synthesis node is
    appended that depends on all the others -- the place where their answers get combined.
    """
    propose = propose or naive_decompose
    raw = [s.strip() for s in propose(question) if s and s.strip()][:max_subs]
    plan = Plan(question=question, subquestions=[SubQuestion(text=s) for s in raw])

    if synthesize and len(plan.subquestions) > 1:
        deps = list(range(len(plan.subquestions)))
        plan.subquestions.append(
            SubQuestion(text=f"Synthesise an overall answer to: {question}", deps=deps)
        )
    return plan
