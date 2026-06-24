"""third-party tool loading.

the built-in tools live in agent/tools/, but i wanted a way to bolt on extra tools without
editing the package -- handy when i'm hacking on something throwaway and don't want it in
the repo. two discovery routes, both opt-in:

  1. a `plugins/` directory (override with AIAGENT_PLUGIN_DIR). every .py file in there is
     imported, and anything it registers via @register lands in the normal tool belt.
  2. python entry points under the "aiagent.tools" group, so a pip-installed package can ship
     tools that show up automatically.

a plugin module just imports `register` from agent.tools and decorates a factory, exactly the
way the built-in modules do. anything that blows up while loading is logged and skipped so one
bad plugin can't take the whole agent down.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from agent.logging_utils import get_logger

log = get_logger(__name__)

_ENTRY_POINT_GROUP = "aiagent.tools"


def plugin_dir() -> Path:
    """where we look for loose .py plugins. env var wins, otherwise ./plugins."""
    return Path(os.environ.get("AIAGENT_PLUGIN_DIR", "plugins"))


def _load_from_dir(directory: Path) -> list[str]:
    loaded: list[str] = []
    if not directory.is_dir():
        return loaded
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        mod_name = f"aiagent_plugin_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded.append(path.stem)
            log.debug("loaded plugin file %s", path)
        except Exception as exc:  # noqa: BLE001 - never let one plugin sink the rest
            log.warning("skipping plugin %s: %s", path, exc)
    return loaded


def _load_from_entry_points() -> list[str]:
    loaded: list[str] = []
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover - py<3.8, not a thing here
        return loaded

    try:
        eps = entry_points()
        # the api shape changed across python versions; handle both politely.
        group = (
            eps.select(group=_ENTRY_POINT_GROUP)
            if hasattr(eps, "select")
            else eps.get(_ENTRY_POINT_GROUP, [])
        )
    except Exception as exc:  # noqa: BLE001
        log.debug("could not read entry points: %s", exc)
        return loaded

    for ep in group:
        try:
            ep.load()  # importing the module is enough; it self-registers
            loaded.append(ep.name)
            log.debug("loaded plugin entry point %s", ep.name)
        except Exception as exc:  # noqa: BLE001
            log.warning("skipping plugin entry point %s: %s", ep.name, exc)
    return loaded


def load_plugins(directory: Path | None = None) -> list[str]:
    """import every discoverable plugin so its tools register. returns the names loaded."""
    directory = directory or plugin_dir()
    found = _load_from_dir(directory) + _load_from_entry_points()
    if found:
        log.info("loaded %d plugin(s): %s", len(found), ", ".join(found))
    return found
