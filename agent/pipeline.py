"""a tiny composable pipeline so the wilder features can be chained cleanly.

everything in the chaos cabinet takes some context, does a thing, and produces more context.
this gives them a common shape: a Context bag that flows through an ordered list of named
Steps. each step is just `fn(context) -> context`, so they compose without ceremony and the
whole run is inspectable afterwards (every step leaves a note).

pure python, no deps, trivially testable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    """the bag that flows through a pipeline. `bag` is free-form; `notes` is the audit trail."""

    query: str
    bag: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def set(self, key: str, value: Any) -> Context:
        self.bag[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.bag.get(key, default)

    def note(self, message: str) -> Context:
        self.notes.append(message)
        return self


Step = Callable[[Context], Context]


@dataclass
class Pipeline:
    """an ordered list of (name, step) pairs you can run a Context through."""

    steps: list[tuple[str, Step]] = field(default_factory=list)

    def then(self, name: str, step: Step) -> Pipeline:
        """add a step and return self, so you can chain `.then(...).then(...)`."""
        self.steps.append((name, step))
        return self

    def run(self, ctx: Context, *, on_error: str = "raise") -> Context:
        """flow the context through every step.

        on_error="raise" lets exceptions propagate; on_error="skip" notes the failure and keeps
        going with the context as it was before the failing step.
        """
        for name, step in self.steps:
            try:
                ctx = step(ctx)
                ctx.note(f"ran {name}")
            except Exception as exc:  # noqa: BLE001 - behaviour is caller-selected
                if on_error == "raise":
                    raise
                ctx.note(f"skipped {name}: {exc}")
        return ctx

    @property
    def names(self) -> list[str]:
        return [name for name, _ in self.steps]
