"""readability and prose-health metrics.

numbers that describe how a passage reads: Flesch reading ease and Flesch-Kincaid grade level,
average sentence length, how much it varies (monotone prose is tiring), the share of sentences in
the passive voice, and the nominalization rate (turning verbs into abstract nouns is the single
most common cause of murky academic writing -- Williams' central point). all offline, no deps.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

_VOWEL_RUN = re.compile(r"[aeiouy]+", re.IGNORECASE)
_PASSIVE = re.compile(
    r"\b(?:was|were|is|are|been|being|be|am)\s+(?:\w+ed|shown|found|made|given|taken|done|seen|known|held|built)\b",
    re.IGNORECASE,
)
# common nominalization endings on words longer than a stem
_NOMINALIZATION = re.compile(
    r"\b\w{4,}(?:tion|sion|ment|ance|ence|ity|ness|ization|isation)\b", re.IGNORECASE
)


@dataclass
class Readability:
    words: int
    sentences: int
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    avg_sentence_length: float
    sentence_length_stdev: float
    passive_ratio: float
    nominalization_per_100w: float

    def pretty(self) -> str:
        return (
            f"Flesch {self.flesch_reading_ease:.0f} (grade {self.flesch_kincaid_grade:.1f}); "
            f"avg {self.avg_sentence_length:.1f} words/sentence (±{self.sentence_length_stdev:.1f}); "
            f"passive {self.passive_ratio:.0%}; "
            f"{self.nominalization_per_100w:.1f} nominalizations/100 words"
        )


def count_syllables(word: str) -> int:
    """a heuristic syllable count: vowel groups, minus a silent trailing 'e'."""
    word = word.lower().strip()
    if not word:
        return 0
    groups = _VOWEL_RUN.findall(word)
    n = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ie")) and n > 1:
        n -= 1
    return max(1, n)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def readability(text: str) -> Readability:
    """compute the prose-health metrics for a passage."""
    sentences = _sentences(text)
    words = re.findall(r"[A-Za-z']+", text)
    n_words = len(words)
    n_sentences = max(1, len(sentences))
    syllables = sum(count_syllables(w) for w in words)

    asl = n_words / n_sentences
    asw = syllables / max(1, n_words)
    flesch = 206.835 - 1.015 * asl - 84.6 * asw
    fk_grade = 0.39 * asl + 11.8 * asw - 15.59

    lengths = [len(re.findall(r"[A-Za-z']+", s)) for s in sentences] or [0]
    stdev = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0

    passive = len(_PASSIVE.findall(text))
    nominalizations = len(_NOMINALIZATION.findall(text))

    return Readability(
        words=n_words,
        sentences=len(sentences),
        flesch_reading_ease=round(flesch, 1),
        flesch_kincaid_grade=round(fk_grade, 1),
        avg_sentence_length=round(asl, 1),
        sentence_length_stdev=round(stdev, 1),
        passive_ratio=round(passive / n_sentences, 3),
        nominalization_per_100w=round(nominalizations / max(1, n_words) * 100, 1),
    )
