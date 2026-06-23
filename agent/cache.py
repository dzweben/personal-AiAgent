"""a dead simple on disk cache for tool/llm results.

keyed by a hash of whatever you throw at it. i mostly use this to avoid re-running the
same web search five times while i am poking at a query. there is a ttl so stale stuff
expires on its own.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class DiskCache:
    def __init__(self, path: str = ".agent_cache", ttl_seconds: int = 24 * 3600):
        self.dir = Path(path)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds

    def _key(self, *parts: Any) -> str:
        blob = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]

    def _file(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, *parts: Any) -> Optional[Any]:
        f = self._file(self._key(*parts))
        if not f.exists():
            return None
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if self.ttl and (time.time() - payload.get("ts", 0)) > self.ttl:
            f.unlink(missing_ok=True)
            return None
        return payload.get("value")

    def set(self, value: Any, *parts: Any) -> None:
        f = self._file(self._key(*parts))
        try:
            f.write_text(
                json.dumps({"ts": time.time(), "value": value}, default=str),
                encoding="utf-8",
            )
        except OSError:
            pass

    def clear(self) -> int:
        removed = 0
        for f in self.dir.glob("*.json"):
            f.unlink(missing_ok=True)
            removed += 1
        return removed
