"""long-term lessons memory: the agent learns from its own runs.

after finishing a question, the agent can reflect -- "what did I learn that would help next
time?" -- and stash those lessons in a small sqlite store keyed by topic. before a new run, it
recalls the lessons most relevant to the question and folds them into the prompt. it's a crude
but real form of getting better with experience. the lesson extractor is injectable; storage
and recall are pure and offline.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS lessons (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    topic      TEXT NOT NULL,
    lesson     TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@dataclass
class Lesson:
    topic: str
    lesson: str
    score: float = 0.0


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


class LessonStore:
    def __init__(self, path: str = ".agent_lessons.sqlite"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add(self, topic: str, lesson: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO lessons (topic, lesson, created_at) VALUES (?, ?, ?)",
                (topic, lesson, datetime.now().isoformat()),
            )

    def all(self) -> list[Lesson]:
        with self._conn() as conn:
            rows = conn.execute("SELECT topic, lesson FROM lessons").fetchall()
        return [Lesson(topic=t, lesson=ls) for t, ls in rows]

    def recall(self, query: str, k: int = 3) -> list[Lesson]:
        """return the k lessons most relevant to the query by topic/lesson token overlap."""
        q = _tokens(query)
        scored: list[Lesson] = []
        for lesson in self.all():
            toks = _tokens(lesson.topic + " " + lesson.lesson)
            overlap = len(q & toks) / len(q | toks) if (q or toks) else 0.0
            if overlap > 0:
                scored.append(
                    Lesson(topic=lesson.topic, lesson=lesson.lesson, score=round(overlap, 3))
                )
        scored.sort(key=lambda lesson: lesson.score, reverse=True)
        return scored[:k]


def reflect(question: str, answer: str, extract=None, settings=None) -> list[str]:
    """derive reusable lessons from a finished run. `extract(question, answer)` is injectable.

    the default asks the llm for terse, transferable lessons. with no extractor and no model
    you can still call this with your own `extract`.
    """
    if extract is None:
        from agent.llm import complete

        def extract(q: str, a: str) -> list[str]:
            out = complete(
                f"Question: {q}\n\nAnswer: {a}\n\nList 1-3 short, transferable lessons for "
                "answering similar questions in future. One per line, no numbering.",
                settings=settings,
                system="You distil reusable lessons. Be terse and general.",
            )
            return [ln.strip("-* ").strip() for ln in out.splitlines() if ln.strip()]

    return [lesson for lesson in extract(question, answer) if lesson][:3]
