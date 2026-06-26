"""the APA 7th-edition writing-style engine -- the whole point of the writing arm.

this is NOT just citation formatting (that's citations.py). it encodes APA's actual writing
standards -- the substance from Publication Manual chapters 4 (writing style and grammar) and 5
(bias-free language): continuity and flow, conciseness, clarity, verb-tense logic, active voice,
first person, bias-free language across the dimensions APA names, hedging claims, and reporting.

three pieces, all offline and deterministic:
  1. style_prompt() -- the full rule set, fed to the model so it writes in APA style.
  2. check_apa() -- a linter flagging violations: contractions, colloquialisms, wordiness, empty
     intensifiers, biased/dated terms, 'the author', overclaiming, anthropomorphism, number rules.
  3. suggest_revisions() -- applies the unambiguous mechanical fixes (wordiness, biased terms)
     so prose can be moved toward APA without a model in the loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# the rules, grouped by APA's own writing standards (Publication Manual ch. 4-5), so they can be
# shown to a user and folded into the prompt. this is about HOW to write, not just formatting.
APA_RULES = {
    "continuity_and_flow": [
        "Maintain continuity: each sentence should follow logically from the last, and each "
        "paragraph should develop a single idea introduced by a clear topic sentence.",
        "Use transitions to show relationships (e.g., 'however', 'consequently', 'in contrast', "
        "'therefore'); avoid abrupt shifts between ideas.",
        "Order ideas so the argument builds; avoid digressions and tangential detail.",
    ],
    "conciseness": [
        "Say only what needs to be said; delete redundancy and wordiness.",
        "Replace wordy phrases with concise ones (e.g., 'because' for 'due to the fact that', "
        "'to' for 'in order to', 'most' for 'a majority of').",
        "Avoid empty intensifiers ('very', 'quite', 'extremely', 'really') and unnecessary jargon.",
    ],
    "clarity": [
        "Use precise word choice; make pronoun references unambiguous (avoid vague 'this'/'it').",
        "Prefer concrete, specific statements over abstract or roundabout ones.",
        "Define technical terms and abbreviations at first use.",
    ],
    "tone": [
        "Write formally and objectively; avoid colloquialisms, idioms, slang, and contractions.",
        "Avoid rhetorical questions, hyperbole, and editorializing.",
    ],
    "voice": [
        "Prefer the active voice ('researchers measured X') over the passive; use passive only "
        "when the recipient of the action is the legitimate focus.",
        "Use first person ('I', 'we') for your own actions; do not refer to yourself as 'the "
        "author' or 'the present writer'.",
    ],
    "verb_tense": [
        "Use past tense for a study's methods and results and for citing prior work ('Smith (2020) "
        "found').",
        "Use present perfect for a line of research over time ('researchers have shown').",
        "Use present tense to discuss your results, conclusions, and what the evidence implies.",
    ],
    "bias_free_language": [
        "Describe people at the appropriate level of specificity and acknowledge them as "
        "participants, not objects ('the participants', not 'subjects' where avoidable).",
        "Use person-first ('people with schizophrenia') or accepted identity-first language; do not "
        "label people by a condition ('schizophrenics', 'the disabled', 'addicts').",
        "Age: use 'older adults', not 'the elderly' or 'seniors'.",
        "Use the singular 'they' for a person whose gender is unknown or nonbinary; avoid 'he' as "
        "a generic pronoun.",
        "Avoid loaded or pejorative terms for race, ethnicity, gender, sexual orientation, "
        "disability, or socioeconomic status.",
    ],
    "claims_and_evidence": [
        "Do not overstate findings: correlational research does not 'prove' or establish causation; "
        "say it 'suggests', 'supports', or 'is associated with'.",
        "Hedge appropriately and attribute every claim to its source; avoid absolutes ('always', "
        "'never', 'all', 'none') unless the evidence is truly that strong.",
        "Report results with appropriate precision; interpret statistics rather than just listing "
        "them.",
    ],
    "numbers": [
        "Spell out numbers below 10 ('three studies'); use numerals for 10 and above ('12 trials').",
        "Use numerals for exact statistics, ages, sample sizes, percentages, scores, and time.",
    ],
    "citations": [
        "Use author-date citations: narrative ('Smith (2020) argued') or parenthetical "
        "('(Smith, 2020)').",
        "Use 'et al.' for works with three or more authors from the first citation.",
    ],
    "mechanics": [
        "Use the serial (Oxford) comma. Use one space after end punctuation.",
        "Do not anthropomorphise (a 'study' can examine, but it cannot 'believe' or 'want').",
        "Keep parallel structure in lists and comparisons.",
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

# wordy phrase -> concise APA-preferred replacement (Publication Manual, conciseness).
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
    "in the near future": "soon",
    "a total of": "",
    "it is important to note that": "",
    "the present study": "this study",
    "with regard to": "regarding",
    "in terms of": "",
    "as a means of": "to",
}

# empty intensifiers APA tells you to cut.
INTENSIFIERS = ("very", "quite", "extremely", "really", "highly", "rather", "somewhat", "fairly")

# biased / dated term -> APA-preferred term (bias-free language, ch. 5).
BIAS_LEXICON = {
    "the elderly": "older adults",
    "the aged": "older adults",
    "seniors": "older adults",
    "subjects": "participants",
    "the disabled": "people with disabilities",
    "the handicapped": "people with disabilities",
    "addicts": "people with substance use disorder",
    "the mentally ill": "people with mental illness",
    "schizophrenics": "people with schizophrenia",
    "diabetics": "people with diabetes",
    "the poor": "people with low income",
    "normal people": "people without the condition",
    "manpower": "workforce",
    "mankind": "humanity",
}

_THE_AUTHOR_RE = re.compile(r"\bthe (?:present )?(?:author|writer|researcher)s?\b", re.IGNORECASE)
# heuristic passive voice: a form of 'to be' followed by a past participle.
_PASSIVE_RE = re.compile(
    r"\b(?:was|were|is|are|been|being|be)\s+(\w+ed|shown|found|made|given|taken|done|seen|known)\b",
    re.IGNORECASE,
)


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
    # conciseness: wordy phrases
    for phrase, concise in WORDINESS.items():
        if phrase in low:
            fix = f"use '{concise}'" if concise else "delete this filler"
            violations.append(Violation("conciseness", phrase, fix))
    # conciseness: empty intensifiers
    for word in INTENSIFIERS:
        if re.search(rf"\b{word}\b", low):
            violations.append(
                Violation("cut empty intensifier", word, "delete or use a precise term")
            )
    # bias-free language
    for term, preferred in BIAS_LEXICON.items():
        if re.search(rf"\b{re.escape(term)}\b", low):
            violations.append(Violation("bias-free language", term, f"use '{preferred}'"))
    # voice / person: refer to yourself as 'I'/'we', not 'the author'
    for m in _THE_AUTHOR_RE.finditer(text):
        violations.append(
            Violation("first person", m.group(0), "use 'I' or 'we' for your own work")
        )
    return violations


def suggest_revisions(text: str) -> str:
    """apply the safe, mechanical fixes (wordiness, biased terms, double spaces) to a passage.

    this is the deterministic part of moving prose toward APA -- the model handles the rest, but
    these substitutions are unambiguous, so we can just make them.
    """
    out = text
    for phrase, concise in WORDINESS.items():
        out = re.sub(rf"\b{re.escape(phrase)}\b", concise, out, flags=re.IGNORECASE)
    for term, preferred in BIAS_LEXICON.items():
        out = re.sub(rf"\b{re.escape(term)}\b", preferred, out, flags=re.IGNORECASE)
    out = re.sub(r" {2,}", " ", out)
    out = re.sub(r"\s+([.,;:])", r"\1", out)  # tidy spaces left before punctuation
    return out.strip()


def apa_score(text: str) -> float:
    """0..1 APA-compliance score: 1.0 is clean, each violation costs a little."""
    if not text.strip():
        return 0.0
    n_sentences = max(1, len(re.findall(r"[.!?]", text)))
    penalty = len(check_apa(text)) / (n_sentences + 3)
    return round(max(0.0, 1.0 - penalty), 3)
