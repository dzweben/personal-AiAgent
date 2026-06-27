"""the rule registry: how a writing rule is defined, found, and applied.

a Rule is a small, self-contained piece of writing knowledge: a name, the category and authority
it comes from, how severe a violation is, a detector that finds offences in text, and a message +
suggestion. rules register themselves into a global library, so adding new writing knowledge is
just writing one more Rule -- the agent's craft grows by accretion.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

SEVERITIES = ("info", "minor", "major")


@dataclass
class Finding:
    rule: str
    category: str
    severity: str
    span: str
    message: str
    suggestion: str = ""
    source: str = ""


@dataclass
class Rule:
    name: str
    category: str
    message: str
    # detect(text) -> list of (offending_span, suggestion) pairs
    detect: Callable[[str], list[tuple[str, str]]]
    severity: str = "minor"
    source: str = ""
    tags: list[str] = field(default_factory=list)

    def run(self, text: str) -> list[Finding]:
        out = []
        for span, suggestion in self.detect(text):
            out.append(
                Finding(
                    rule=self.name,
                    category=self.category,
                    severity=self.severity,
                    span=span,
                    message=self.message,
                    suggestion=suggestion,
                    source=self.source,
                )
            )
        return out


_REGISTRY: dict[str, Rule] = {}


def register(rule: Rule) -> Rule:
    """add a rule to the global library (last writer wins on name clashes)."""
    _REGISTRY[rule.name] = rule
    return rule


def all_rules() -> list[Rule]:
    return list(_REGISTRY.values())


def categories() -> list[str]:
    return sorted({r.category for r in _REGISTRY.values()})


def lint(
    text: str,
    categories: list[str] | None = None,
    rules: list[str] | None = None,
    min_severity: str = "info",
) -> list[Finding]:
    """run the matching rules over text and return all findings.

    filter by `categories` and/or explicit `rules` (names); `min_severity` drops gentler findings.
    """
    floor = SEVERITIES.index(min_severity) if min_severity in SEVERITIES else 0
    findings: list[Finding] = []
    for rule in _REGISTRY.values():
        if categories and rule.category not in categories:
            continue
        if rules and rule.name not in rules:
            continue
        if SEVERITIES.index(rule.severity) < floor:
            continue
        findings.extend(rule.run(text))
    return findings


# ---- helpers for building rules -----------------------------------------------------------


def regex_rule(
    name: str,
    category: str,
    pattern: str,
    message: str,
    suggestion: str = "",
    severity: str = "minor",
    source: str = "",
    flags: int = re.IGNORECASE,
) -> Rule:
    """build (and register) a rule that fires on every match of a regex."""
    compiled = re.compile(pattern, flags)

    def detect(text: str) -> list[tuple[str, str]]:
        return [(m.group(0).strip(), suggestion) for m in compiled.finditer(text)]

    return register(
        Rule(
            name=name,
            category=category,
            message=message,
            detect=detect,
            severity=severity,
            source=source,
        )
    )


def lexicon_rule(
    name: str,
    category: str,
    mapping: dict[str, str],
    message: str,
    severity: str = "minor",
    source: str = "",
) -> Rule:
    """build a rule from a {bad_term: preferred_term} map; suggestion is the preferred term."""

    def detect(text: str) -> list[tuple[str, str]]:
        low = text.lower()
        out = []
        for bad, good in mapping.items():
            if re.search(rf"\b{re.escape(bad)}\b", low):
                out.append((bad, f"use '{good}'" if good else "delete this"))
        return out

    return register(
        Rule(
            name=name,
            category=category,
            message=message,
            detect=detect,
            severity=severity,
            source=source,
        )
    )
