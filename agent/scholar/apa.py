"""the APA 7th-edition writing-style engine -- the whole point of the writing arm.

this is not about citation formatting (that's citations.py); this governs how the *prose itself*
is written, so the output reads like an APA paper. it does two things:

  1. style_prompt() -- a thorough instruction set encoding APA writing conventions (tone, voice,
     verb tense for describing research, number rules, bias-free language, hedging, mechanics)
     that's fed to the model so it writes in APA style.
  2. check_apa() -- a style linter that flags common APA violations (contractions, low numbers as
     digits, colloquialisms, overclaiming causation, anthropomorphism, double spaces), so the arm
     can grade and self-correct its own prose toward APA.

all offline and deterministic; the linter needs no model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# the rules, grouped, so they can be shown to a user and folded into the prompt.
APA_RULES = {
    "tone": [
        "Write formally and objectively; avoid colloquialisms, idioms, slang, and contractions.",
        "Be precise and concise; prefer plain, direct sentences over flowery or vague ones.",
    ],
    "voice": [
        "Prefer the active voice ('researchers measured X'), but use passive when the recipient "
        "of the action is the focus.",
        "Use first person ('I', 'we') for your own actions as the author; do not use the editorial "
        "'we' to mean people in general.",
    ],
    "tense": [
        "Use past tense or present perfect to describe prior research (e.g., 'Smith (2020) found', "
        "'studies have shown').",
        "Use present tense for conclusions and established facts ('the results suggest').",
    ],
    "numbers": [
        "Spell out numbers below 10 ('three studies'); use numerals for 10 and above ('12 trials').",
        "Use numerals for exact statistics, ages, sample sizes, percentages, and time.",
    ],
    "citations": [
        "Use author-date citations: narrative ('Smith (2020) argued') or parenthetical "
        "('(Smith, 2020)').",
        "Use 'et al.' for works with three or more authors from the first citation.",
    ],
    "bias_free": [
        "Use bias-free, person-first language; describe people specifically and respectfully.",
        "Do not equate people with their conditions (write 'people with depression', not "
        "'depressives').",
    ],
    "claims": [
        "Do not overstate findings: correlational research does not 'prove' or establish causation; "
        "say it 'suggests', 'supports', or 'is associated with'.",
        "Qualify claims appropriately and attribute them to their source.",
    ],
    "mechanics": [
        "Use the serial (Oxford) comma. Use one space after end punctuation.",
        "Do not anthropomorphise (a 'study' can examine, but it cannot 'believe' or 'want').",
    ],
}


def style_prompt(section: str | None = None) -> str:
    """build the APA-style system instruction handed to the writer."""
    lines = [
        "You are writing in strict APA 7th-edition style. Follow these conventions exactly:",
    ]
    for rules in APA_RULES.values():
        for r in rules:
            lines.append(f"- {r}")
    lines.append(
        "Write in a scholarly register suitable for a peer-reviewed journal. Use clear topic "
        "sentences and logical transitions. Cite only the sources provided; never invent a citation."
    )
    if section:
        lines.append(f"You are drafting the '{section}' section.")
    return "\n".join(lines)


# ---- the style checker --------------------------------------------------------------------

_CONTRACTION_RE = re.compile(
    r"\b(?:don't|doesn't|isn't|aren't|can't|won't|didn't|it's|they're|we're|you're|that's|"
    r"there's|wasn't|weren't|hasn't|haven't|wouldn't|shouldn't|couldn't|i'm|let's)\b",
    re.IGNORECASE,
)
_COLLOQUIAL = (
    "a lot",
    "lots of",
    "kind of",
    "sort of",
    "really",
    "very",
    "huge",
    "tons of",
    "stuff",
    "things like",
    "basically",
    "pretty much",
    "big time",
    "loads of",
)
_OVERCLAIM_RE = re.compile(
    r"\b(prove[sd]?|proven|proof that|definitely causes?|always|never)\b", re.IGNORECASE
)
_ANTHRO_RE = re.compile(
    r"\b(the (?:study|paper|research|data|table|figure)) "
    r"(believe[sd]?|thinks?|thought|wants?|wanted|feels?|felt|knows?|knew|hopes?)\b",
    re.IGNORECASE,
)
# a standalone digit 1-9 used as a quantity ("3 studies") should be spelled out in APA
_LOW_NUMERAL_RE = re.compile(r"(?<![\d.])\b([1-9])\b\s+(?=[a-zA-Z])")


@dataclass
class Violation:
    rule: str
    snippet: str
    suggestion: str


def check_apa(text: str) -> list[Violation]:
    """flag common APA writing-style violations in a passage. heuristic, offline."""
    violations: list[Violation] = []

    for m in _CONTRACTION_RE.finditer(text):
        violations.append(
            Violation("no contractions", m.group(0), "spell it out (e.g., 'do not' for \"don't\")")
        )
    low = text.lower()
    for word in _COLLOQUIAL:
        if re.search(rf"\b{re.escape(word)}\b", low):
            violations.append(
                Violation("formal tone", word, "replace the colloquialism with precise wording")
            )
    for m in _OVERCLAIM_RE.finditer(text):
        violations.append(
            Violation(
                "no overclaiming", m.group(0), "use 'suggests', 'supports', or 'is associated with'"
            )
        )
    for m in _ANTHRO_RE.finditer(text):
        violations.append(
            Violation(
                "no anthropomorphism",
                m.group(0),
                "attribute mental states to people, not artifacts",
            )
        )
    for m in _LOW_NUMERAL_RE.finditer(text):
        # skip things that look like a citation year or stat by requiring a following word (handled by regex)
        violations.append(
            Violation("spell out numbers < 10", m.group(0).strip(), "write the number as a word")
        )
    if "  " in text:
        violations.append(
            Violation("single spacing", "double space", "use one space after punctuation")
        )
    return violations


def apa_score(text: str) -> float:
    """0..1 APA-compliance score: 1.0 is clean, each violation costs a little."""
    if not text.strip():
        return 0.0
    n_sentences = max(1, len(re.findall(r"[.!?]", text)))
    penalty = len(check_apa(text)) / (n_sentences + 3)
    return round(max(0.0, 1.0 - penalty), 3)
