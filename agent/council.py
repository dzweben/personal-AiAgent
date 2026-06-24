"""the council: one pipeline that chains the whole cabinet into a single, better answer.

convene() runs a question through the works:

    route -> ensemble (several personas answer) -> fact-check the merged draft
          -> constitutional critique + rewrite -> adversarial red-team -> score it

every move is recorded (agent.replay) so the run is inspectable and shareable, and an optional
budget guard keeps the whole thing from running away. all the model-touching parts come from a
single injectable `complete(prompt) -> str`, so the entire chain is testable offline with one
fake function.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.critique import refine
from agent.ensemble import ensemble
from agent.factcheck import VERDICTS, factcheck, summarize_verdicts
from agent.redteam import redteam
from agent.replay import Recorder
from agent.router import route
from agent.scorecard import Scorecard, score


@dataclass
class CouncilResult:
    question: str
    mode: str
    answer: str
    scorecard: Scorecard
    claims: list
    redteam_survived: bool
    weaknesses: list
    recorder: Recorder

    def pretty(self) -> str:
        verdicts = summarize_verdicts(self.claims)
        lines = [
            f"Q: {self.question}",
            f"route: {self.mode}",
            "",
            self.answer,
            "",
            f"claims: {verdicts}",
            f"red team: {'survived' if self.redteam_survived else f'{len(self.weaknesses)} weak spots'}",
            self.scorecard.pretty(),
        ]
        return "\n".join(lines)


def _components_from_complete(complete):
    """derive every model-touching callable the chain needs from one complete(prompt) fn."""

    def answer(persona, q):
        return complete(f"As a {persona}, answer: {q}")

    def verify(claim):
        out = complete(f"Is this claim supported, refuted, or unclear? {claim}")
        first = out.strip().split()[0].lower().strip(".,:") if out.strip() else "unclear"
        return (first if first in VERDICTS else "unclear"), out.strip()

    def judge(ans, principles):
        from agent.critique import _parse_issues

        rules = "; ".join(principles)
        return _parse_issues(complete(f"Critique this against [{rules}]. Reply OK if fine:\n{ans}"))

    def revise(ans, issues):
        return complete(f"Rewrite to fix {issues}:\n{ans}")

    def respond(ans, attack):
        out = complete(f"Attack: {attack}\nAnswer: {ans}\nReply HOLDS or BREAKS.")
        return (not out.strip().upper().startswith("BREAKS")), out.strip()

    return answer, verify, judge, revise, respond


def convene(
    question: str,
    complete=None,
    personas: list[str] | None = None,
    refine_rounds: int = 2,
    settings=None,
    budget=None,
) -> CouncilResult:
    """run the full council pipeline and return a graded, fact-checked, hardened answer."""
    rec = Recorder(title=f"council: {question}")

    r = route(question)
    rec.record("route", f"{r.mode} — {r.reason}", mode=r.mode)

    # wire the model-touching callables (from an injected complete, or each module's llm default)
    if complete is not None:
        answer_fn, verify_fn, judge_fn, revise_fn, respond_fn = _components_from_complete(complete)
    else:
        answer_fn = verify_fn = judge_fn = revise_fn = respond_fn = None

    if budget is not None and not budget.guard(question):
        rec.record("budget", "no headroom; returning early")

    ens = ensemble(question, personas=personas, answer=answer_fn, settings=settings)
    rec.record("ensemble", f"{len(ens.answers)} personas merged", personas=list(ens.answers))
    draft = ens.merged

    checks = factcheck(draft, verify=verify_fn, settings=settings)
    rec.record("factcheck", str(summarize_verdicts(checks)), n_claims=len(checks))

    refined = refine(
        draft, judge=judge_fn, revise=revise_fn, max_rounds=refine_rounds, settings=settings
    )
    rec.record("critique", f"{refined.rounds} round(s)", rounds=refined.rounds)
    answer = refined.final

    rt = redteam(answer, respond=respond_fn, settings=settings)
    rec.record(
        "redteam",
        "survived" if rt.survived else f"{len(rt.weaknesses)} weakness(es)",
        survived=rt.survived,
    )

    supported = summarize_verdicts(checks).get("supported", 0)
    sc = score(answer, n_sources=supported)
    rec.record("score", sc.pretty(), overall=sc.overall)

    return CouncilResult(
        question=question,
        mode=r.mode,
        answer=answer,
        scorecard=sc,
        claims=checks,
        redteam_survived=rt.survived,
        weaknesses=rt.weaknesses,
        recorder=rec,
    )
