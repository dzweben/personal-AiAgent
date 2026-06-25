"""turn a debate transcript into a structured argument map.

a debate is a flat list of turns; this lifts it into a little graph of claims with typed edges
between them -- which turns SUPPORT each other and which ATTACK each other -- so you can see the
shape of the disagreement at a glance. it reuses the contradiction heuristics for attacks and
bag-of-words overlap for support. all offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from agent.contradiction import _looks_contradictory, _subject_overlap


@dataclass
class ArgNode:
    idx: int
    speaker: str
    claim: str


@dataclass
class ArgEdge:
    src: int
    dst: int
    kind: str  # "support" or "attack"
    reason: str = ""


@dataclass
class ArgMap:
    nodes: list[ArgNode] = field(default_factory=list)
    edges: list[ArgEdge] = field(default_factory=list)

    def supports(self) -> list[ArgEdge]:
        return [e for e in self.edges if e.kind == "support"]

    def attacks(self) -> list[ArgEdge]:
        return [e for e in self.edges if e.kind == "attack"]

    def contested(self) -> list[int]:
        """node indices that are attacked by at least one other node."""
        return sorted({e.dst for e in self.attacks()})

    def pretty(self) -> str:
        lines = ["argument map:"]
        for n in self.nodes:
            lines.append(f"  [{n.idx}] {n.speaker}: {n.claim}")
        for e in self.edges:
            arrow = "⊢" if e.kind == "support" else "⊥"
            lines.append(f"  {e.src} {arrow} {e.dst} ({e.kind}: {e.reason})")
        return "\n".join(lines)


def _headline(text: str) -> str:
    """the first sentence is usually the turn's main claim."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0].strip() if parts else text.strip()


def build_argmap(turns, support_threshold: float = 0.3) -> ArgMap:
    """build an argument map from `turns`, a sequence of (speaker, text) pairs."""
    amap = ArgMap()
    for i, (speaker, text) in enumerate(turns):
        amap.nodes.append(ArgNode(idx=i, speaker=speaker, claim=_headline(text)))

    for i in range(len(amap.nodes)):
        for j in range(i + 1, len(amap.nodes)):
            a, b = amap.nodes[i].claim, amap.nodes[j].claim
            overlap = _subject_overlap(a, b)
            if overlap < 0.15:
                continue  # unrelated turns -- no edge
            reason = _looks_contradictory(a, b)
            if reason:
                amap.edges.append(ArgEdge(src=i, dst=j, kind="attack", reason=reason))
            elif overlap >= support_threshold and amap.nodes[i].speaker == amap.nodes[j].speaker:
                amap.edges.append(
                    ArgEdge(
                        src=i, dst=j, kind="support", reason=f"same stance, overlap {overlap:.2f}"
                    )
                )
    return amap
