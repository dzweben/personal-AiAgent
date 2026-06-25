"""build a little knowledge graph out of the answers the agent produces.

as the agent answers questions, this harvests entities (capitalised names, acronyms) and the
relations between them (simple subject-verb-object patterns) and stitches them into a graph you
can grow and query: what's connected to X, what's the path between X and Y. it's a deliberately
simple offline extractor -- no spaCy, no model -- but it's enough to remember how things relate.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

# a capitalised word (optionally multi-word) or an all-caps acronym, not at sentence start only
_ENTITY_RE = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*|[A-Z]{2,})\b")
_STOP_ENTITIES = {
    "The",
    "A",
    "An",
    "It",
    "This",
    "That",
    "These",
    "Those",
    "He",
    "She",
    "They",
    "I",
}
# subject VERB object, where subject/object are entity-ish
_REL_RE = re.compile(
    r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+"
    r"(is|are|was|were|has|have|causes?|affects?|contains?|powers?|owns?|created?|uses?|"
    r"produces?|requires?|enables?|includes?|blocks?|delays?|reduces?|raises?|lowers?|"
    r"improves?|prevents?|increases?|decreases?|leads?|drives?|triggers?)\s+"
    r"(?:(?:a|an|the)\s+)?([a-zA-Z][a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})"
)


@dataclass
class Triple:
    subject: str
    relation: str
    obj: str


@dataclass
class KnowledgeGraph:
    edges: list[Triple] = field(default_factory=list)
    _adj: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def add(self, subject: str, relation: str, obj: str) -> None:
        self.edges.append(Triple(subject, relation, obj))
        self._adj[subject.lower()].add(obj.lower())
        self._adj[obj.lower()].add(subject.lower())

    @property
    def entities(self) -> set[str]:
        names: set[str] = set()
        for t in self.edges:
            names.add(t.subject)
            names.add(t.obj)
        return names

    def ingest(self, text: str) -> int:
        """pull triples out of text and add them. returns how many were added."""
        added = 0
        for subj, rel, obj in _REL_RE.findall(text):
            subj, obj = subj.strip(), obj.strip()
            if subj in _STOP_ENTITIES:
                continue
            self.add(subj, rel, obj)
            added += 1
        return added

    def neighbors(self, entity: str) -> set[str]:
        return set(self._adj.get(entity.lower(), set()))

    def path(self, start: str, goal: str) -> list[str] | None:
        """shortest connection between two entities via BFS, or None if unconnected."""
        start_l, goal_l = start.lower(), goal.lower()
        if start_l not in self._adj or goal_l not in self._adj:
            return None
        queue = [[start_l]]
        seen = {start_l}
        while queue:
            trail = queue.pop(0)
            if trail[-1] == goal_l:
                return trail
            for nxt in self._adj[trail[-1]]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append([*trail, nxt])
        return None


def extract_entities(text: str) -> list[str]:
    """return distinct entity-ish names mentioned in text (order preserved)."""
    out, seen = [], set()
    for m in _ENTITY_RE.findall(text):
        # a sentence-initial stopword can glue onto a real entity ("The NASA") -- peel it off
        words = m.split()
        while words and words[0] in _STOP_ENTITIES:
            words = words[1:]
        m = " ".join(words)
        if not m or m in _STOP_ENTITIES or m.lower() in seen:
            continue
        seen.add(m.lower())
        out.append(m)
    return out
