"""the agent's tool belt.

each tool lives in its own little module so they stay readable. this file wires them
together and hands back a list of langchain Tool objects. anything that fails to import
(missing optional dep, no api key, whatever) just gets skipped instead of blowing up the
whole agent, which is the behaviour i actually want day to day.
"""

from __future__ import annotations

from typing import Callable

from agent.logging_utils import get_logger

log = get_logger(__name__)

# (display name, factory) pairs. the factory returns a Tool or a list of Tools, or raises.
_REGISTRY: dict[str, Callable] = {}


def register(name: str):
    def deco(fn: Callable):
        _REGISTRY[name] = fn
        return fn

    return deco


def _safe(name: str, factory: Callable):
    try:
        made = factory()
        return made if isinstance(made, list) else [made]
    except Exception as exc:  # noqa: BLE001 - intentional, we want to keep going
        log.debug("skipping tool %s: %s", name, exc)
        return []


def build_tools(enabled: list[str] | None = None) -> list:
    """return the langchain Tool objects the agent should use.

    pass a list of names to cherry pick, or leave it None to grab everything that loads.
    """
    # import here so importing the package stays cheap
    from agent.tools import (  # noqa: F401
        calculator,
        datetime_tool,
        files,
        python_repl,
        web,
        wiki,
    )

    # these ones lean on optional deps or api keys, so import them defensively
    for optional in ("arxiv", "news", "weather"):
        try:
            __import__(f"agent.tools.{optional}")
        except Exception:  # noqa: BLE001
            pass

    names = enabled if enabled is not None else list(_REGISTRY.keys())
    tools: list = []
    for name in names:
        factory = _REGISTRY.get(name)
        if factory is None:
            log.debug("no tool registered under %r", name)
            continue
        tools.extend(_safe(name, factory))
    log.debug("built %d tools: %s", len(tools), [getattr(t, "name", "?") for t in tools])
    return tools


def available_tool_names() -> list[str]:
    # make sure the modules have registered themselves first
    build_tools(enabled=[])
    return sorted(_REGISTRY.keys())
