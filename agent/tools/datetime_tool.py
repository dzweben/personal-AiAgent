"""tiny tool so the agent can actually tell what day it is.

models are famously bad at knowing the current date, so handing them a real clock cuts
out a whole class of dumb mistakes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from langchain_core.tools import Tool

from agent.tools import register


def _now(fmt: str = "") -> str:
    fmt = (fmt or "").strip().strip('"').strip("'")
    now_local = datetime.now()
    now_utc = datetime.now(timezone.utc)
    if fmt:
        try:
            return now_local.strftime(fmt)
        except Exception as exc:  # noqa: BLE001
            return f"bad format string: {exc}"
    return (
        f"local: {now_local:%Y-%m-%d %H:%M:%S} "
        f"({now_local.strftime('%A')}) | utc: {now_utc:%Y-%m-%d %H:%M:%S}"
    )


@register("datetime")
def make_datetime():
    return Tool(
        name="datetime",
        func=_now,
        description=(
            "Get the current date and time. Optionally pass a strftime format string, "
            "otherwise you get a sensible default with local and utc time."
        ),
    )
