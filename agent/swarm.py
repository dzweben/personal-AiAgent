"""a tiny society of agents working a shared blackboard.

instead of one agent, spin up several with different roles (researcher, critic, synthesiser…)
and let them take turns writing to a common blackboard. each one sees what the others wrote and
builds on it. it's the classic blackboard architecture, shrunk to a weekend-project scale.

the turn-taking is plain python and testable offline; each role's contribution comes from an
injectable `contribute` callable that defaults to the llm.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_ROLES = ["researcher", "critic", "synthesizer"]

_ROLE_BRIEF = {
    "researcher": "Surface the key facts and the strongest evidence. Be specific.",
    "critic": "Poke holes: what's missing, wrong, or overclaimed on the board so far?",
    "synthesizer": "Pull the board into one coherent, balanced position.",
    "devils_advocate": "Argue the unpopular counter-position as well as you can.",
    "pragmatist": "What should someone actually DO with this? Concrete next steps.",
}


@dataclass
class Entry:
    role: str
    round: int
    text: str


@dataclass
class SwarmResult:
    task: str
    board: list[Entry] = field(default_factory=list)
    final: str = ""

    def pretty(self) -> str:
        lines = [f"task: {self.task}", ""]
        for e in self.board:
            lines.append(f"[r{e.round} · {e.role}] {e.text}")
        if self.final:
            lines += ["", f"[final] {self.final}"]
        return "\n".join(lines)

    def last_by(self, role: str) -> str | None:
        hits = [e.text for e in self.board if e.role == role]
        return hits[-1] if hits else None


def run_swarm(
    task: str,
    roles: list[str] | None = None,
    rounds: int = 1,
    contribute=None,
    synthesize=None,
    settings=None,
) -> SwarmResult:
    """run a blackboard collaboration, then fold the board into one final answer.

    each role contributes once per round, in order; afterwards `synthesize(task, board_text)`
    distils the whole board into a single consolidated answer. both callables are injectable.
    """
    roles = roles or DEFAULT_ROLES
    auto = contribute is None  # llm path -> we also get a default synthesizer
    if contribute is None:
        from agent.llm import complete

        def contribute(role: str, task: str, board_text: str) -> str:
            brief = _ROLE_BRIEF.get(role, f"Act as the {role}.")
            sys = f"You are the {role} on a small research team. {brief} Keep it under 4 sentences."
            return complete(
                f"Task: {task}\n\nBlackboard so far:\n{board_text}", settings=settings, system=sys
            )

    if synthesize is None and auto:
        from agent.llm import complete

        def synthesize(task: str, board_text: str) -> str:
            sys = (
                "You are the lead. Fold the team's blackboard into one clear, balanced answer "
                "that incorporates the strongest points and resolves disagreements."
            )
            return complete(
                f"Task: {task}\n\nBlackboard:\n{board_text}", settings=settings, system=sys
            )

    result = SwarmResult(task=task)
    for r in range(max(1, rounds)):
        for role in roles:
            board_text = result.pretty() if result.board else "(empty)"
            text = contribute(role, task, board_text)
            result.board.append(Entry(role=role, round=r + 1, text=text.strip()))

    # synthesise a final answer when we have a synthesizer (always on the llm path; opt-in offline)
    if synthesize is not None:
        result.final = synthesize(task, result.pretty()).strip()
    return result
