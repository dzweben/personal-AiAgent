"""a spend guard you can wrap around a multi-step run so it can't run away on you.

the council and other chained features can make a lot of model calls. a Budget tracks estimated
spend across all of them and raises before it blows past a ceiling you set, so an experiment
can't quietly cost real money. it reuses agent.usage for the per-call estimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.usage import estimate_cost


class BudgetExceeded(RuntimeError):
    """raised when a charge would push the running total past the ceiling."""


@dataclass
class Charge:
    label: str
    cost: float


@dataclass
class Budget:
    """track estimated spend against an optional usd ceiling.

    max_usd=None means "no ceiling, just keep the tally". set a number to enforce a hard cap.
    """

    max_usd: float | None = None
    model: str = "gpt-4o"
    charges: list[Charge] = field(default_factory=list)

    @property
    def spent(self) -> float:
        return round(sum(c.cost for c in self.charges), 6)

    def remaining(self) -> float:
        return float("inf") if self.max_usd is None else round(self.max_usd - self.spent, 6)

    def would_exceed(self, cost: float) -> bool:
        return self.max_usd is not None and self.spent + cost > self.max_usd

    def charge(self, prompt: str, expected_output_tokens: int = 500, label: str = "call") -> float:
        """estimate the cost of a call, record it, and enforce the ceiling. returns the cost."""
        est = estimate_cost(prompt, expected_output_tokens, self.model)
        cost = est.total_cost
        if self.would_exceed(cost):
            raise BudgetExceeded(
                f"{label} would cost ~${cost:.4f}, over the ${self.max_usd:.4f} budget "
                f"(already spent ${self.spent:.4f})"
            )
        self.charges.append(Charge(label=label, cost=cost))
        return cost

    def guard(self, prompt: str, expected_output_tokens: int = 500) -> bool:
        """non-raising check: True if there's room for this call, False otherwise."""
        est = estimate_cost(prompt, expected_output_tokens, self.model)
        return not self.would_exceed(est.total_cost)

    def pretty(self) -> str:
        cap = "no cap" if self.max_usd is None else f"${self.max_usd:.4f} cap"
        return f"spent ${self.spent:.4f} across {len(self.charges)} calls ({cap})"
