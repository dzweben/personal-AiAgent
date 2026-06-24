"""adversarial self-attack: try to break the agent's own answer before a user does.

it throws a battery of standard attacks at an answer -- find a counterexample, check the edge
cases, look for hidden assumptions, etc. -- and asks a responder whether the answer survives
each one. anything it doesn't survive is a weakness the council can route back into the critic.
the responder is injectable, so the attack battery and bookkeeping test offline.
"""

from __future__ import annotations

from dataclasses import dataclass

# the standard battery. each is a lens an adversary would use on any claim.
ATTACKS = [
    "Find a concrete counterexample that breaks this answer.",
    "What hidden assumption does this answer depend on?",
    "Where does this answer fail at the edge cases or extremes?",
    "Is there a more recent fact that would change this answer?",
    "Could the cited reasoning be a correlation mistaken for causation?",
    "What would a domain expert say is oversimplified here?",
]


@dataclass
class Probe:
    attack: str
    holds: bool
    reply: str = ""


@dataclass
class RedTeamResult:
    answer: str
    probes: list[Probe]

    @property
    def weaknesses(self) -> list[Probe]:
        return [p for p in self.probes if not p.holds]

    @property
    def survived(self) -> bool:
        return not self.weaknesses

    def pretty(self) -> str:
        lines = [f"red team: {'SURVIVED' if self.survived else 'FOUND WEAKNESSES'}"]
        for p in self.probes:
            mark = "✓" if p.holds else "✗"
            lines.append(f"  {mark} {p.attack}")
            if not p.holds and p.reply:
                lines.append(f"      ↳ {p.reply}")
        return "\n".join(lines)


def _default_responder(settings=None):
    from agent.llm import complete

    def respond(answer: str, attack: str):
        out = complete(
            f"Answer under review:\n{answer}\n\nAttack: {attack}\n\nDoes the answer survive this "
            "attack? Start your reply with HOLDS or BREAKS, then explain briefly.",
            settings=settings,
            system="You are a ruthless but fair adversarial reviewer.",
        )
        holds = not out.strip().upper().startswith("BREAKS")
        return holds, out.strip()

    return respond


def redteam(
    answer: str, attacks: list[str] | None = None, respond=None, settings=None
) -> RedTeamResult:
    """run the attack battery against an answer. `respond(answer, attack) -> (holds, reply)`."""
    attacks = attacks or ATTACKS
    respond = respond or _default_responder(settings)
    probes = []
    for attack in attacks:
        holds, reply = respond(answer, attack)
        probes.append(Probe(attack=attack, holds=bool(holds), reply=reply))
    return RedTeamResult(answer=answer, probes=probes)
