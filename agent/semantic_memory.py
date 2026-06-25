"""semantic memory: remember things by meaning, not exact words, and across sessions.

the existing sqlite memory is a literal transcript. this is different: it embeds each note into
a vector and recalls by similarity, so "how do stimulants affect rest" can pull up a note filed
under "caffeine and sleep". the embedder is a dependency-free feature-hashing bag-of-words --
not as good as a real model, but deterministic, instant, and offline. swap in real embeddings
by passing your own `embed` function. notes persist to a jsonl file so memory survives restarts.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

_DIM = 256


def embed(text: str, dim: int = _DIM) -> list[float]:
    """a deterministic feature-hashing embedding: hash each token into a fixed-width vector.

    crude but real -- shared vocabulary lands in shared dimensions, so cosine similarity tracks
    word overlap and survives small wording changes. L2-normalised so cosine is just a dot.
    """
    vec = [0.0] * dim
    for tok in re.findall(r"\w+", text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)  # noqa: S324 - not security, just a hash
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


@dataclass
class Note:
    text: str
    meta: dict
    score: float = 0.0


class SemanticMemory:
    def __init__(self, path: str | None = None, embed_fn=embed):
        self.path = path
        self.embed = embed_fn
        self._notes: list[dict] = []
        if path and Path(path).exists():
            self._load()

    def _load(self) -> None:
        with open(self.path, encoding="utf-8") as fh:
            self._notes = [json.loads(line) for line in fh if line.strip()]

    def _persist(self, note: dict) -> None:
        if not self.path:
            return
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(note) + "\n")

    def add(self, text: str, **meta) -> None:
        note = {"text": text, "meta": meta, "vec": self.embed(text)}
        self._notes.append(note)
        self._persist(note)

    def __len__(self) -> int:
        return len(self._notes)

    def recall(self, query: str, k: int = 3, min_score: float = 0.05) -> list[Note]:
        """return the k notes most semantically similar to the query."""
        qv = self.embed(query)
        scored = [
            Note(text=n["text"], meta=n["meta"], score=round(cosine(qv, n["vec"]), 4))
            for n in self._notes
        ]
        scored = [n for n in scored if n.score >= min_score]
        scored.sort(key=lambda n: n.score, reverse=True)
        return scored[:k]
