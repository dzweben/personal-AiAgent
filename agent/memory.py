"""conversation memory backed by sqlite.

keeps a rolling log of turns so the agent can remember earlier parts of a session, and so
i can go back and look at what i asked last week. nothing fancy, just a single table.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from agent.logging_utils import get_logger

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS turns (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session    TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session);
"""


class ConversationMemory:
    def __init__(
        self, path: str = ".agent_memory.sqlite", session: str = "default", max_history: int = 20
    ):
        self.path = path
        self.session = session
        self.max_history = max_history
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add(self, role: str, content: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO turns (session, role, content, created_at) VALUES (?, ?, ?, ?)",
                (self.session, role, content, datetime.now().isoformat()),
            )

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.add("assistant", content)

    def history(self, limit: int | None = None) -> list[tuple[str, str]]:
        """return [(role, content), ...] oldest first, capped at max_history by default."""
        n = limit or self.max_history
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT role, content FROM turns WHERE session = ? ORDER BY id DESC LIMIT ?",
                (self.session, n),
            ).fetchall()
        return list(reversed(rows))

    def as_langchain_messages(self) -> list[tuple[str, str]]:
        """shape the history the way ChatPromptTemplate placeholders want it."""
        mapping = {"user": "human", "assistant": "ai"}
        return [(mapping.get(role, "human"), content) for role, content in self.history()]

    def clear(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM turns WHERE session = ?", (self.session,))

    def sessions(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT DISTINCT session FROM turns ORDER BY session").fetchall()
        return [r[0] for r in rows]
