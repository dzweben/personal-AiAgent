"""oracle mode: oblique-strategy style cards to knock a question loose.

stuck on how to think about something? draw a few cards. each one reframes your query from a
weird angle to force lateral thinking. inspired by brian eno & peter schmidt's oblique
strategies, repurposed as research provocations. pure offline, deterministic under a seed.
"""

from __future__ import annotations

import random

DECK = [
    "invert it: what would make the opposite true?",
    "what would this look like at 1000x the scale?",
    "who profits if the common answer is wrong?",
    "explain it to someone from 200 years ago.",
    "what's the most boring possible explanation?",
    "what evidence would change your mind entirely?",
    "remove the most important constraint -- now what?",
    "what is everyone in this field too embarrassed to ask?",
    "follow the money. then follow the incentives.",
    "what would a child notice that an expert misses?",
    "assume the data is lying. where would it hide?",
    "what happens if you wait ten years before answering?",
    "what's the second-order effect nobody models?",
    "steelman the position you find most annoying.",
    "what would you do if failure were impossible?",
    "find the exception that breaks the rule.",
]


def draw(query: str, n: int = 3, seed: int = 0) -> list[str]:
    """draw n cards and pair each with the query as a reframing prompt."""
    rng = random.Random(seed)
    n = max(1, min(n, len(DECK)))
    cards = rng.sample(DECK, n)
    return [f"{query}\n  ↳ {card}" for card in cards]
