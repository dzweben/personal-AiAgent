"""record a chained run step-by-step so you can replay, inspect, or share it later.

the council makes a lot of moves -- route, ensemble, fact-check, critique, score. a Recorder
captures each move as it happens, and the result serialises to plain json. pair it with
agent.capsule to ship a whole run as one string, or with agent.trace to draw it as a tree.
nothing here calls a model; it's just bookkeeping, so it's trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Move:
    step: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recorder:
    title: str = "run"
    moves: list[Move] = field(default_factory=list)

    def record(self, step: str, summary: str, **data: Any) -> Recorder:
        self.moves.append(Move(step=step, summary=summary, data=data))
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "moves": [{"step": m.step, "summary": m.summary, "data": m.data} for m in self.moves],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Recorder:
        rec = cls(title=payload.get("title", "run"))
        for m in payload.get("moves", []):
            rec.moves.append(
                Move(step=m.get("step", "?"), summary=m.get("summary", ""), data=m.get("data", {}))
            )
        return rec

    def pretty(self) -> str:
        lines = [f"▶ {self.title}"]
        for i, m in enumerate(self.moves, 1):
            lines.append(f"  {i}. {m.step}: {m.summary}")
        return "\n".join(lines)

    def to_capsule(self) -> str:
        """pack the whole run into a portable capsule string."""
        from agent.capsule import encode

        return encode(self.to_dict())

    @classmethod
    def from_capsule(cls, capsule: str) -> Recorder:
        from agent.capsule import decode

        return cls.from_dict(decode(capsule))
