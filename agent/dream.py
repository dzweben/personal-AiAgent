"""dream mode: when the agent is idle, let it free-associate over its own memory.

it pulls salient words out of past conversations and recombines them into spontaneous "what if"
questions -- little research prompts the agent generates for itself. it's deliberately a bit
surreal; think of it as the agent's notebook of shower thoughts rather than a serious feature.

completely offline and deterministic under a seeded rng, so it's easy to test and needs no api.
"""

from __future__ import annotations

import random
import re

_STOPWORDS = frozenset(
    """the a an and or but if then else of to in on at for with without from by as is are was
    were be been being it its this that these those i you he she they we them his her their our
    my your what which who whom how why when where do does did done can could would should will
    just about into over under than too very can't dont don't isnt about not no yes""".split()
)

_TEMPLATES = [
    "what if {a} has more to do with {b} than anyone admits?",
    "is there a hidden link between {a} and {b}?",
    "what would {a} look like if we rebuilt it around {b}?",
    "could {b} be the missing piece in {a}?",
    "why does nobody talk about {a} and {b} in the same breath?",
    "if {a} failed, would {b} explain why?",
]


def _salient_words(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]{3,}", text.lower())
    seen, out = set(), []
    for w in words:
        if w in _STOPWORDS or w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def dream(snippets: list[str], n: int = 5, seed: int = 0) -> list[str]:
    """recombine words from `snippets` into n surreal research questions."""
    rng = random.Random(seed)
    vocab = _salient_words(" ".join(snippets))
    if len(vocab) < 2:
        return []
    dreams = []
    for _ in range(n):
        a, b = rng.sample(vocab, 2)
        template = rng.choice(_TEMPLATES)
        dreams.append(template.format(a=a, b=b))
    return dreams


def dream_from_memory(memory, n: int = 5, seed: int = 0) -> list[str]:
    """pull recent turns out of a ConversationMemory and dream over them."""
    snippets = [content for _role, content in memory.history(limit=50)]
    return dream(snippets, n=n, seed=seed)
