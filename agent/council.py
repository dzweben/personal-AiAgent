"""the council: one pipeline that chains the whole cabinet into a single, better answer.

convene() runs a question through the works:

    route -> ensemble (several personas answer) -> fact-check the merged draft
          -> constitutional critique + rewrite -> adversarial red-team -> score it

and then, if you ask it to, it *loops*: as long as the score is under your target or the red
team found a weak spot, it feeds those weaknesses (plus any unsupported claims) back into a
reviser and re-evaluates, until it clears the bar or runs out of iterations. every move is
recorded (agent.replay) so the run is inspectable and shareable, and an optional budget guard
keeps the whole thing from running away. all the model-touching parts come from a single
injectable `complete(prompt) -> str`, so the entire chain is testable offline with one fake.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
    iterations: int = 1
    score_history: list[float] = field(default_factory=list)

    def pretty(self) -> str:
        verdicts = summarize_verdicts(self.claims)
        survived = "survived" if self.redteam_survived else f"{len(self.weaknesses)} weak spots"
        trail = " → ".join(f"{s:.2f}" for s in self.score_history)
        lines = [
            f"Q: {self.question}",
            f"route: {self.mode}   iterations: {self.iterations}",
            "",
            self.answer,
            "",
            f"claims: {verdicts}",
            f"red team: {survived}",
            f"{self.scorecard.pretty()}   (history: {trail})",
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


def _evaluate(answer, verify_fn, respond_fn, settings):
    """run the judgement stages on an answer: fact-check, red-team, score."""
    checks = factcheck(answer, verify=verify_fn, settings=settings)
    rt = redteam(answer, respond=respond_fn, settings=settings)
    supported = summarize_verdicts(checks).get("supported", 0)
    sc = score(answer, n_sources=supported)
    return checks, rt, sc


def _feedback(checks, rt) -> list[str]:
    """collect concrete fixes from red-team weaknesses and non-supported claims."""
    issues = [f"address this weakness: {p.attack} ({p.reply})" for p in rt.weaknesses]
    issues += [
        f"this claim is {c.verdict}, fix or qualify it: {c.claim}"
        for c in checks
        if c.verdict != "supported"
    ]
    return issues


def convene(
    question: str,
    complete=None,
    personas: list[str] | None = None,
    refine_rounds: int = 2,
    settings=None,
    budget=None,
    target_score: float = 0.0,
    max_iterations: int = 1,
) -> CouncilResult:
    """run the council pipeline, optionally looping until the score clears `target_score`.

    with the defaults (target_score=0.0, max_iterations=1) it's a single pass. raise either to
    turn on the self-correction loop.
    """
    rec = Recorder(title=f"council: {question}")

    r = route(question)
    rec.record("route", f"{r.mode} — {r.reason}", mode=r.mode)

    if complete is not None:
        answer_fn, verify_fn, judge_fn, revise_fn, respond_fn = _components_from_complete(complete)
    else:
        answer_fn = verify_fn = judge_fn = revise_fn = respond_fn = None
    # a reviser is needed for the self-correction loop even on the live-llm path
    if revise_fn is None:
        from agent.critique import _default_reviser

        revise_fn = _default_reviser(settings)

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
    history = [sc.overall]

    # the self-correction loop: keep going while we're short of target or the red team bit
    iteration = 1
    while iteration < max_iterations and (sc.overall < target_score or not rt.survived):
        issues = _feedback(checks, rt)
        if not issues:
            break
        answer = revise_fn(answer, issues).strip()
        rec.record("revise", f"addressed {len(issues)} issue(s)", iteration=iteration + 1)
        checks, rt, sc = _evaluate(answer, verify_fn, respond_fn, settings)
        rec.record(
            "recheck",
            f"{summarize_verdicts(checks)} | {'survived' if rt.survived else 'weak'} | {sc.pretty()}",
            overall=sc.overall,
        )
        history.append(sc.overall)
        iteration += 1

    return CouncilResult(
        question=question,
        mode=r.mode,
        answer=answer,
        scorecard=sc,
        claims=checks,
        redteam_survived=rt.survived,
        weaknesses=rt.weaknesses,
        recorder=rec,
        iterations=iteration,
        score_history=history,
    )
