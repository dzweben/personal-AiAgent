"""a tiny vector store abstraction.

i wanted something that works with chromadb when it is installed, but does not fall over
on a minimal install. so there are two backends:

  - "chroma": real persistent vector db with embeddings
  - "memory": a pure python cosine similarity store with a hashing based pseudo embedding

the memory backend is obviously not as good, but it needs zero extra deps and is enough to
demo the retrieval flow and run the tests offline.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field

from agent.logging_utils import get_logger

log = get_logger(__name__)


def simple_chunk(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """split text into overlapping chunks on word boundaries. good enough for rag."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    # work in characters but cut on words so we do not slice mid token
    buf: list[str] = []
    length = 0
    for word in words:
        buf.append(word)
        length += len(word) + 1
        if length >= chunk_size:
            chunks.append(" ".join(buf))
            # keep a tail for overlap
            keep = max(0, len(buf) - max(1, overlap // 5))
            buf = buf[keep:]
            length = sum(len(w) + 1 for w in buf)
    if buf:
        chunks.append(" ".join(buf))
    return chunks


def _hash_embed(text: str, dims: int = 256) -> list[float]:
    """deterministic bag of words hashing embedding. no model required.

    not semantically smart, but it captures token overlap which is plenty for a fallback.
    """
    vec = [0.0] * dims
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dims] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


@dataclass
class _Doc:
    text: str
    meta: dict
    vec: list[float] = field(default_factory=list)


class VectorStore:
    def __init__(
        self, backend: str = "memory", collection: str = "research", path: str = ".chroma"
    ):
        self.backend = backend
        self.collection = collection
        self.path = path
        self._docs: list[_Doc] = []
        self._client = None
        self._coll = None
        if backend == "chroma":
            self._init_chroma()

    def _init_chroma(self) -> None:
        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=self.path)
            self._coll = self._client.get_or_create_collection(self.collection)
        except Exception as exc:  # noqa: BLE001
            log.warning("chroma backend unavailable (%s), falling back to memory store", exc)
            self.backend = "memory"

    def add(self, text: str, meta: dict | None = None) -> int:
        """add one document (or chunk). returns how many chunks were stored."""
        meta = meta or {}
        chunks = simple_chunk(text)
        if self.backend == "chroma" and self._coll is not None:
            ids = [f"{len(self._docs) + i}" for i in range(len(chunks))]
            self._coll.add(documents=chunks, metadatas=[meta] * len(chunks), ids=ids)
            self._docs.extend(_Doc(text=c, meta=meta) for c in chunks)
            return len(chunks)
        for c in chunks:
            self._docs.append(_Doc(text=c, meta=meta, vec=_hash_embed(c)))
        return len(chunks)

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        if self.backend == "chroma" and self._coll is not None:
            res = self._coll.query(query_texts=[query], n_results=top_k)
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            return [
                {"text": d, "meta": m, "score": None} for d, m in zip(docs, metas, strict=False)
            ]

        qv = _hash_embed(query)
        scored = [(_cosine(qv, d.vec), d) for d in self._docs]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"text": d.text, "meta": d.meta, "score": round(score, 4)}
            for score, d in scored[:top_k]
            if score > 0
        ]

    def count(self) -> int:
        return len(self._docs)

    def as_context(self, query: str, top_k: int = 4) -> str:
        """join the top hits into a block you can stuff into a prompt."""
        hits = self.search(query, top_k=top_k)
        if not hits:
            return ""
        return "\n\n".join(f"[{i+1}] {h['text']}" for i, h in enumerate(hits))
