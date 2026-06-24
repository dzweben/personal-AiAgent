"""a constitutional self-critique loop: the agent grades its own answer and rewrites it.

give it an answer and a short list of principles ("a constitution"). a judge checks the answer
against each principle and lists what's wrong; a reviser rewrites to fix those issues; repeat
until the judge is happy or we run out of rounds. it's the agent marking its own homework, on
purpose, in a loop.

judge and reviser are injectable so the loop is testable without a model. defaults route
through agent.llm.complete.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_CONSTITUTION = [
    "Be accurate and do not invent facts or sources.",
    "Be clear and free of jargon a beginner couldn't follow.",
    "Acknowledge uncertainty and competing views where they exist.",
    "Stay on the question actually asked.",
    "Be concise: no filler, no repetition.",
]


@dataclass
class RefineResult:
    final: str
    rounds: int
    issues_per_round: list[list[str]] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.rounds > 0 and any(self.issues_per_round)


def _default_judge(settings=None):
    from agent.llm import complete

    def judge(answer: str, principles: list[str]) -> list[str]:
        rules = "\n".join(f"- {p}" for p in principles)
        sys = (
            "You are a strict reviewer. List concrete violations of the principles, one per "
            "line, no numbering. If the answer fully complies, reply with exactly: OK"
        )
        out = complete(f"Principles:\n{rules}\n\nAnswer:\n{answer}", settings=settings, system=sys)
        return _parse_issues(out)

    return judge


def _default_reviser(settings=None):
    from agent.llm import complete

    def revise(answer: str, issues: list[str]) -> str:
        problems = "\n".join(f"- {i}" for i in issues)
        sys = "Rewrite the answer so it fixes every listed issue. Output only the new answer."
        return complete(f"Issues:\n{problems}\n\nAnswer:\n{answer}", settings=settings, system=sys)

    return revise


def _parse_issues(text: str) -> list[str]:
    text = text.strip()
    if not text or text.strip().upper().startswith("OK"):
        return []
    issues = []
    for line in text.splitlines():
        line = line.lstrip("-*0123456789. ").strip()
        if line and line.upper() != "OK":
            issues.append(line)
    return issues


def refine(
    answer: str,
    principles: list[str] | None = None,
    judge=None,
    revise=None,
    max_rounds: int = 3,
    settings=None,
) -> RefineResult:
    """loop critique -> revise until the judge finds nothing or we hit max_rounds."""
    principles = principles or DEFAULT_CONSTITUTION
    judge = judge or _default_judge(settings)
    revise = revise or _default_reviser(settings)

    current = answer
    issues_log: list[list[str]] = []
    for _ in range(max(1, max_rounds)):
        issues = judge(current, principles)
        issues_log.append(issues)
        if not issues:
            break
        current = revise(current, issues).strip()
    return RefineResult(final=current, rounds=len(issues_log), issues_per_round=issues_log)
