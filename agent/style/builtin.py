"""the built-in writing-rule library -- the actual craft knowledge.

rules are grouped by the level they work at (word -> sentence -> paragraph -> document) and tagged
with the authority they come from. this is meant to grow; adding a rule is adding a Rule. nothing
here calls a model -- every rule is a transparent detector.

authorities referenced:
  APA      -- APA Publication Manual, 7th ed. (chs. 4-5)
  Williams -- Joseph M. Williams, *Style: Lessons in Clarity and Grace*
  Strunk   -- Strunk & White, *The Elements of Style*
  Hyland   -- Ken Hyland on academic metadiscourse / hedging
"""

from __future__ import annotations

import re

from agent.style.rules import Rule, lexicon_rule, regex_rule, register

# ===========================================================================================
# WORD LEVEL -- diction, precision, bias
# ===========================================================================================

WORDINESS = {
    "due to the fact that": "because",
    "in order to": "to",
    "a majority of": "most",
    "a number of": "several",
    "at this point in time": "now",
    "in the event that": "if",
    "for the purpose of": "to",
    "in spite of the fact that": "although",
    "has the ability to": "can",
    "is able to": "can",
    "a total of": "",
    "it is important to note that": "",
    "with regard to": "regarding",
    "in terms of": "",
    "as a means of": "to",
    "the fact that": "that",
    "in the process of": "",
}
lexicon_rule("wordiness", "concision", WORDINESS, "Wordy phrase; tighten it.", source="Williams")

REDUNDANT_PAIRS = {
    "each and every": "each",
    "basic fundamentals": "fundamentals",
    "end result": "result",
    "future plans": "plans",
    "past history": "history",
    "final outcome": "outcome",
    "completely eliminate": "eliminate",
    "absolutely essential": "essential",
    "advance planning": "planning",
    "close proximity": "proximity",
    "new innovation": "innovation",
    "unexpected surprise": "surprise",
}
lexicon_rule(
    "redundancy",
    "concision",
    REDUNDANT_PAIRS,
    "Redundant pairing; one word will do.",
    source="Strunk",
)

INTENSIFIERS = (
    "very",
    "quite",
    "extremely",
    "really",
    "highly",
    "rather",
    "somewhat",
    "fairly",
    "totally",
    "incredibly",
)
regex_rule(
    "empty_intensifier",
    "concision",
    r"\b(?:" + "|".join(INTENSIFIERS) + r")\b",
    "Empty intensifier; cut it or choose a precise word.",
    suggestion="delete or use a stronger, exact term",
    source="Strunk",
)

BIAS_LEXICON = {
    "the elderly": "older adults",
    "the aged": "older adults",
    "seniors": "older adults",
    "subjects": "participants",
    "the disabled": "people with disabilities",
    "the handicapped": "people with disabilities",
    "addicts": "people with a substance use disorder",
    "the mentally ill": "people with mental illness",
    "schizophrenics": "people with schizophrenia",
    "diabetics": "people with diabetes",
    "the poor": "people with low income",
    "normal people": "people without the condition",
    "manpower": "workforce",
    "mankind": "humanity",
    "man-made": "synthetic",
}
lexicon_rule(
    "bias_free",
    "bias",
    BIAS_LEXICON,
    "Use bias-free, person-first language.",
    severity="major",
    source="APA",
)

# ===========================================================================================
# SENTENCE LEVEL -- clarity, voice, grammar
# ===========================================================================================

# Williams' #1 lesson: actions buried in abstract nouns. flag verb->noun nominalizations that
# pair with a weak verb ("conduct an investigation" -> "investigate", "make a decision" -> "decide").
_NOMINAL_VERB = re.compile(
    r"\b(?:make|made|conduct|conducted|perform|performed|provide|provided|reach|reached|"
    r"carry out|carried out|give|gave|take|took|do|did|have|had)\s+(?:a|an|the)?\s*"
    r"(\w+(?:tion|sion|ment|ance|ence|sis|ision|ment))\b",
    re.IGNORECASE,
)
register(
    Rule(
        name="nominalization",
        category="clarity",
        message="Buried action: turn the noun back into a verb (e.g., 'make a decision' -> 'decide').",
        detect=lambda text: [
            (m.group(0), "use the verb form") for m in _NOMINAL_VERB.finditer(text)
        ],
        severity="major",
        source="Williams",
    )
)

# expletive openings push the real subject away ("There are many studies that show" -> "Many studies show").
regex_rule(
    "expletive",
    "clarity",
    r"(?:^|(?<=[.!?]\s))(?:there (?:is|are|were|was)|it is|it was)\b",
    "Expletive opening delays the real subject; start with the subject.",
    suggestion="rewrite to lead with the actor",
    source="Williams",
)

# passive voice (heuristic)
register(
    Rule(
        name="passive_voice",
        category="voice",
        message="Passive voice; prefer the active unless the receiver is the focus.",
        detect=lambda text: [
            (m.group(0), "name the actor and use an active verb")
            for m in re.finditer(
                r"\b(?:was|were|is|are|been|being|be)\s+(?:\w+ed|shown|found|made|given|taken|done|seen|known)\b",
                text,
                re.IGNORECASE,
            )
        ],
        severity="info",
        source="APA",
    )
)

# weak "to be" main verbs in chains
regex_rule(
    "weak_verb",
    "clarity",
    r"\b(?:there|this|that|it)\s+(?:is|are|was|were)\b",
    "Weak linking construction; consider a vivid verb.",
    suggestion="replace with an action verb",
    severity="info",
    source="Strunk",
)

# contractions are out in formal academic prose
regex_rule(
    "contraction",
    "academic_voice",
    r"\b(?:do|does|did|is|are|was|were|has|have|had|would|should|could|will|ca|wo)n't\b|"
    r"\b(?:it|that|there|he|she|they|we|you|i)'(?:s|re|ve|ll|d|m)\b|\blet's\b",
    "Contraction; spell it out in formal writing.",
    suggestion="write the full form",
    source="APA",
)

# referring to yourself in the third person
regex_rule(
    "third_person_author",
    "academic_voice",
    r"\bthe (?:present )?(?:author|writer|researcher)s?\b",
    "Refer to yourself as 'I' or 'we', not 'the author'.",
    suggestion="use 'I' or 'we'",
    source="APA",
)

# ===========================================================================================
# CLAIMS -- hedging and overclaiming
# ===========================================================================================

regex_rule(
    "overclaiming",
    "claims",
    r"\b(?:prove[sd]?|proven|proof that|definitely|undeniably|always|never|all|none|every)\b",
    "Overclaiming; evidence rarely proves absolutes. Hedge appropriately.",
    suggestion="use 'suggests', 'supports', 'is associated with', or qualify the scope",
    severity="major",
    source="Hyland",
)

regex_rule(
    "causal_overreach",
    "claims",
    r"\b(?:causes?|caused|leads to|results in|due to)\b",
    "Causal language; ensure the design supports causation (correlation does not).",
    suggestion="if correlational, say 'is associated with' or 'predicts'",
    severity="info",
    source="APA",
)

# ===========================================================================================
# TONE / MECHANICS
# ===========================================================================================

COLLOQUIAL = {
    "a lot": "many / much",
    "lots of": "many",
    "kind of": "somewhat",
    "sort of": "somewhat",
    "stuff": "materials / items",
    "things": "elements / factors",
    "big": "large",
    "huge": "substantial",
    "basically": "",
    "pretty much": "largely",
}
lexicon_rule(
    "colloquialism", "tone", COLLOQUIAL, "Colloquial; choose formal, precise wording.", source="APA"
)

regex_rule(
    "rhetorical_question",
    "tone",
    r"\b(?:isn't it|don't you think|who knows|what if)\b|\?\s*$",
    "Rhetorical questions are out of place in formal academic prose.",
    suggestion="state the point directly",
    severity="info",
    source="APA",
)

regex_rule(
    "exclamation",
    "tone",
    r"!",
    "Exclamation marks are too informal for academic writing.",
    suggestion="remove the exclamation mark",
    severity="info",
    source="APA",
)

regex_rule(
    "double_space",
    "mechanics",
    r"\S {2,}\S",
    "Use a single space after punctuation and between words.",
    suggestion="collapse to one space",
    severity="info",
    source="APA",
)

# a low single digit used as a quantity should be spelled out
register(
    Rule(
        name="low_numeral",
        category="mechanics",
        message="Spell out numbers below 10 in prose.",
        detect=lambda text: [
            (m.group(0).strip(), "write the number as a word")
            for m in re.finditer(r"(?<![\d.])\b([1-9])\b\s+(?=[A-Za-z])", text)
        ],
        severity="info",
        source="APA",
    )
)
