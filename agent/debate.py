"""dialectic mode: make two voices argue a question until something useful falls out.

instead of one model answering, this runs a structured debate -- an optimist and a skeptic (or
whatever two stances you pick) trade arguments for a few rounds, then a moderator synthesises
the most defensible position. it's the "rubber duck, but the duck fights back" feature.

the round structure is plain python and fully testable offline; the actual talking is done by
an injectable `respond` callable, which defaults to agent.llm.complete.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Turn:
    speaker: str
    text: str


@dataclass
class DebateResult:
    question: str
    transcript: list[Turn] = field(default_factory=list)
    synthesis: str = ""
    rounds_run: int = 0
    converged: bool = False

    def pretty(self) -> str:
        lines = [f"Q: {self.question}", ""]
        for t in self.transcript:
            lines.append(f"[{t.speaker}] {t.text}")
        if self.synthesis:
            note = " (converged early)" if self.converged else ""
            lines += ["", f"[moderator]{note} {self.synthesis}"]
        return "\n".join(lines)


def _transcript_text(transcript: list[Turn]) -> str:
    return "\n".join(f"{t.speaker}: {t.text}" for t in transcript) or "(nothing yet)"


def _round_overlap(prev: list[str], curr: list[str]) -> float:
    """bag-of-words similarity between two rounds' arguments. high = nothing new was said."""
    import re

    a = set(re.findall(r"\w+", " ".join(prev).lower()))
    b = set(re.findall(r"\w+", " ".join(curr).lower()))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def run_debate(
    question: str,
    speakers: tuple[str, ...] = ("optimist", "skeptic"),
    rounds: int = 2,
    respond=None,
    moderate=None,
    converge_threshold: float = 1.01,
    settings=None,
) -> DebateResult:
    """run `rounds` rounds where each speaker responds in turn, then synthesise.

    `respond(speaker, question, transcript_text)` and `moderate(question, transcript_text)` are
    injectable for testing. by default they route through the llm with stance-flavoured prompts.
    """
    if respond is None:
        from agent.llm import complete

        def respond(speaker: str, q: str, so_far: str) -> str:
            sys = (
                f"You are the {speaker} in a debate. Make ONE sharp, concrete argument for your "
                "side, engaging with what was already said. Two sentences max."
            )
            return complete(
                f"Question: {q}\n\nDebate so far:\n{so_far}", settings=settings, system=sys
            )

    if moderate is None:
        from agent.llm import complete

        def moderate(q: str, so_far: str) -> str:
            sys = (
                "You are a neutral moderator. Weigh the arguments and state the most defensible "
                "position in 2-3 sentences, noting any genuine trade-off."
            )
            return complete(f"Question: {q}\n\nDebate:\n{so_far}", settings=settings, system=sys)

    result = DebateResult(question=question)
    prev_round: list[str] = []
    for r in range(max(1, rounds)):
        this_round: list[str] = []
        for speaker in speakers:
            text = respond(speaker, question, _transcript_text(result.transcript)).strip()
            result.transcript.append(Turn(speaker=speaker, text=text))
            this_round.append(text)
        result.rounds_run = r + 1
        # stop early if a round barely added anything new over the last one
        if prev_round and _round_overlap(prev_round, this_round) >= converge_threshold:
            result.converged = True
            break
        prev_round = this_round
    result.synthesis = moderate(question, _transcript_text(result.transcript)).strip()
    return result
