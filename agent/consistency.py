"""self-consistency: ask the same thing several times, keep the answer the samples agree on.

a single sample can be a fluke. so sample N answers, cluster the ones that say substantially
the same thing, and return the representative of the biggest cluster -- plus a consistency
score for how much the samples actually agreed. this is the classic self-consistency trick,
done with cheap bag-of-words clustering so it runs offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ConsistencyResult:
    answer: str
    consistency: float  # 0..1: size of the winning cluster / number of samples
    clusters: list[list[str]] = field(default_factory=list)
    n_samples: int = 0

    @property
    def agreed(self) -> bool:
        return self.consistency >= 0.5


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _similar(a: set[str], b: set[str], threshold: float) -> bool:
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= threshold


def cluster(answers: list[str], threshold: float = 0.4) -> list[list[str]]:
    """greedy single-link clustering of answers by bag-of-words overlap."""
    clusters: list[list[str]] = []
    reps: list[set[str]] = []
    for ans in answers:
        toks = _tokens(ans)
        for i, rep in enumerate(reps):
            if _similar(toks, rep, threshold):
                clusters[i].append(ans)
                reps[i] = rep | toks  # grow the representative token set
                break
        else:
            clusters.append([ans])
            reps.append(toks)
    return clusters


def self_consistency(
    query: str,
    sample=None,
    n: int = 5,
    threshold: float = 0.4,
    settings=None,
) -> ConsistencyResult:
    """draw `n` samples for the query, cluster them, return the majority answer + agreement.

    `sample(query, i) -> str` is injectable. by default it asks the llm with a little randomness
    (different framings per index) so the samples actually vary.
    """
    if sample is None:
        from agent.llm import complete

        framings = [
            "Answer directly.",
            "Answer carefully and precisely.",
            "Answer as if explaining to a colleague.",
            "Answer, double-checking your reasoning.",
            "Answer concisely.",
        ]

        def sample(q: str, i: int) -> str:
            return complete(q, settings=settings, system=framings[i % len(framings)])

    answers = [sample(query, i).strip() for i in range(max(1, n))]
    clusters = sorted(cluster(answers, threshold), key=len, reverse=True)
    winner = clusters[0]
    # the representative is the longest answer in the winning cluster (usually most complete)
    rep = max(winner, key=len)
    return ConsistencyResult(
        answer=rep,
        consistency=round(len(winner) / len(answers), 3),
        clusters=clusters,
        n_samples=len(answers),
    )
