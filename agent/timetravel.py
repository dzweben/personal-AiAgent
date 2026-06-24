"""git-backed conversation memory, so you can branch and rewind your own thoughts.

every time you snapshot, the current conversation state is committed into a little private git
repo. that means you get `git`'s whole superpower set for free: a timeline of every snapshot,
branching into alternate conversation timelines ("what if i'd asked it differently"), and diffs
between any two points. it's version control for your train of thought.

it shells out to real git in a directory you choose, so it needs git on the path (it always is)
and is fully testable offline.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from agent.logging_utils import get_logger

log = get_logger(__name__)

_SNAPSHOT_FILE = "conversation.md"


@dataclass
class Snapshot:
    sha: str
    label: str


class TimeTravel:
    def __init__(self, path: str = ".agent_timeline"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        if not (self.path / ".git").exists():
            self._git("init", "-q")
            self._git("config", "user.email", "agent@local")
            self._git("config", "user.name", "aiagent")
            # an empty root commit so the first branch/diff has somewhere to stand
            (self.path / _SNAPSHOT_FILE).write_text("", encoding="utf-8")
            self._git("add", _SNAPSHOT_FILE)
            self._git("commit", "-q", "-m", "root")

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def snapshot(self, content: str, label: str) -> str:
        """commit the current conversation content under a label, return the short sha."""
        (self.path / _SNAPSHOT_FILE).write_text(content, encoding="utf-8")
        self._git("add", _SNAPSHOT_FILE)
        self._git("commit", "-q", "--allow-empty", "-m", label)
        return self._git("rev-parse", "--short", "HEAD")

    def timeline(self) -> list[Snapshot]:
        """list snapshots newest-first (excluding the empty root)."""
        out = self._git("log", "--pretty=%h\t%s")
        snaps = []
        for line in out.splitlines():
            sha, _, label = line.partition("\t")
            if label == "root":
                continue
            snaps.append(Snapshot(sha=sha, label=label))
        return snaps

    def branch(self, name: str) -> None:
        """fork an alternate timeline and switch to it."""
        self._git("checkout", "-q", "-b", name)

    def switch(self, name: str) -> None:
        self._git("checkout", "-q", name)

    def branches(self) -> list[str]:
        out = self._git("branch", "--format=%(refname:short)")
        return [b.strip() for b in out.splitlines() if b.strip()]

    def diff(self, ref_a: str, ref_b: str = "HEAD") -> str:
        return self._git("diff", ref_a, ref_b, "--", _SNAPSHOT_FILE)
