"""adversarial self-attack: try to break the agent's own answer before a user does.

it throws a battery of standard attacks at an answer -- find a counterexample, check the edge
cases, look for hidden assumptions, etc. -- and asks a responder whether the answer survives
each one. anything it doesn't survive is a weakness the council can route back into the critic.
the responder is injectable, so the attack battery and bookkeeping test offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# the catalog: each attack has a category and a severity (how damaging if the answer fails it).
ATTACK_CATALOG = [
    ("factual", 1.0, "Find a concrete counterexample that breaks this answer."),
    ("logical", 0.8, "What hidden assumption does this answer depend on?"),
    ("coverage", 0.6, "Where does this answer fail at the edge cases or extremes?"),
    ("recency", 0.7, "Is there a more recent fact that would change this answer?"),
    ("causal", 0.8, "Could the cited reasoning be a correlation mistaken for causation?"),
    ("depth", 0.5, "What would a domain expert say is oversimplified here?"),
    ("bias", 0.6, "What perspective or stakeholder does this answer quietly ignore?"),
]

# kept for backwards compatibility: the plain list of attack strings.
ATTACKS = [text for _cat, _sev, text in ATTACK_CATALOG]

_SEVERITY = {text: sev for _cat, sev, text in ATTACK_CATALOG}
_CATEGORY = {text: cat for cat, _sev, text in ATTACK_CATALOG}


@dataclass
class Probe:
    attack: str
    holds: bool
    reply: str = ""
    category: str = "general"
    severity: float = 0.5


@dataclass
class RedTeamResult:
    answer: str
    probes: list[Probe] = field(default_factory=list)

    @property
    def weaknesses(self) -> list[Probe]:
        # most damaging first
        return sorted(
            (p for p in self.probes if not p.holds), key=lambda p: p.severity, reverse=True
        )

    @property
    def survived(self) -> bool:
        return not self.weaknesses

    @property
    def robustness(self) -> float:
        """0..1: severity-weighted fraction of attacks the answer held against."""
        if not self.probes:
            return 1.0
        total = sum(p.severity for p in self.probes) or 1.0
        held = sum(p.severity for p in self.probes if p.holds)
        return round(held / total, 3)

    def by_category(self) -> dict[str, bool]:
        """did the answer survive every attack in each category?"""
        out: dict[str, bool] = {}
        for p in self.probes:
            out[p.category] = out.get(p.category, True) and p.holds
        return out

    def pretty(self) -> str:
        head = "SURVIVED" if self.survived else "FOUND WEAKNESSES"
        lines = [f"red team: {head} (robustness {self.robustness:.2f})"]
        for p in self.probes:
            mark = "✓" if p.holds else "✗"
            lines.append(f"  {mark} [{p.category} {p.severity:.1f}] {p.attack}")
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
        probes.append(
            Probe(
                attack=attack,
                holds=bool(holds),
                reply=reply,
                category=_CATEGORY.get(attack, "general"),
                severity=_SEVERITY.get(attack, 0.5),
            )
        )
    return RedTeamResult(answer=answer, probes=probes)
