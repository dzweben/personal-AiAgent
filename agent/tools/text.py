"""text utilities the agent can call: stats, readability, and regex extraction.

all pure python, no deps. handy when a query is really about a chunk of text rather than
something you need to go search for.
"""

from __future__ import annotations

import re

from langchain_core.tools import Tool

from agent.tools import register


def _syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _text_stats(text: str) -> str:
    words = re.findall(r"\b\w+\b", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    n_words = len(words)
    n_sent = max(1, len(sentences))
    n_chars = len(text)
    syllables = sum(_syllables(w) for w in words) or 1
    # flesch reading ease, the classic readability score
    flesch = 206.835 - 1.015 * (n_words / n_sent) - 84.6 * (syllables / max(1, n_words))
    return (
        f"characters: {n_chars}\n"
        f"words: {n_words}\n"
        f"sentences: {n_sent}\n"
        f"avg words/sentence: {round(n_words / n_sent, 1)}\n"
        f"flesch reading ease: {round(flesch, 1)} "
        f"(higher is easier, 60-70 is plain english)"
    )


@register("text_stats")
def make_text_stats():
    return Tool(
        name="text_stats",
        func=_text_stats,
        description=(
            "Analyse a chunk of text: word/sentence counts and a Flesch reading ease score. "
            "Input is the text itself."
        ),
    )


def _regex_extract(spec: str) -> str:
    """expects 'PATTERN ::: TEXT'. returns all matches of pattern in text."""
    if ":::" not in spec:
        return "format is 'PATTERN ::: TEXT to search'"
    pattern, _, text = spec.partition(":::")
    try:
        matches = re.findall(pattern.strip(), text)
    except re.error as exc:
        return f"bad regex: {exc}"
    if not matches:
        return "no matches"
    flat = [m if isinstance(m, str) else " ".join(m) for m in matches]
    return "\n".join(flat[:50])


@register("regex_extract")
def make_regex_extract():
    return Tool(
        name="regex_extract",
        func=_regex_extract,
        description=(
            "Extract all regex matches from some text. "
            "Input format: 'PATTERN ::: the text to search in'."
        ),
    )
