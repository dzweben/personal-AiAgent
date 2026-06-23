"""token counting and a rough cost estimate.

uses tiktoken when it is installed for an accurate count, otherwise falls back to the
classic "about 4 characters per token" rule of thumb. the price table is approximate and
will drift over time, it is just here so you have a ballpark before you fire off a big run.
"""

from __future__ import annotations

from dataclasses import dataclass

# usd per 1k tokens, (input, output). approximate, update as prices change.
_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "claude-3-5-sonnet-latest": (0.003, 0.015),
    "claude-3-opus-latest": (0.015, 0.075),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """best effort token count for a string."""
    try:
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # the old reliable: roughly four characters per token
        return max(1, len(text) // 4)


@dataclass
class CostEstimate:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float

    @property
    def total_cost(self) -> float:
        return round(self.input_cost + self.output_cost, 6)

    def pretty(self) -> str:
        return (
            f"{self.model}: ~{self.input_tokens} in + ~{self.output_tokens} out tokens, "
            f"about ${self.total_cost:.4f}"
        )


def estimate_cost(
    prompt: str,
    expected_output_tokens: int = 500,
    model: str = "gpt-4o",
) -> CostEstimate:
    in_tok = count_tokens(prompt, model)
    in_rate, out_rate = _PRICES.get(model, (0.0025, 0.01))
    return CostEstimate(
        model=model,
        input_tokens=in_tok,
        output_tokens=expected_output_tokens,
        input_cost=round(in_tok / 1000 * in_rate, 6),
        output_cost=round(expected_output_tokens / 1000 * out_rate, 6),
    )


def known_models() -> list[str]:
    return sorted(_PRICES.keys())
