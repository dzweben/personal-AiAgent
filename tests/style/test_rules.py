"""tests for the writing-rules engine and library."""

from __future__ import annotations

from agent.style import all_rules, lint
from agent.style.rules import Finding, Rule, regex_rule


def _rules_hit(text, **kw):
    return {f.rule for f in lint(text, **kw)}


def test_library_is_populated():
    rules = all_rules()
    assert len(rules) >= 15
    cats = {r.category for r in rules}
    assert {"concision", "clarity", "voice", "bias", "claims"} <= cats


def test_wordiness_flagged():
    assert "wordiness" in _rules_hit("This happened due to the fact that it rained.")


def test_redundancy_flagged():
    assert "redundancy" in _rules_hit("The end result was clear.")


def test_nominalization_flagged():
    assert "nominalization" in _rules_hit("The committee made a decision about the policy.")


def test_expletive_flagged():
    assert "expletive" in _rules_hit("There are many studies that show this effect.")


def test_bias_flagged_as_major():
    findings = [f for f in lint("The elderly were tested.") if f.rule == "bias_free"]
    assert findings and findings[0].severity == "major"


def test_overclaiming_flagged():
    assert "overclaiming" in _rules_hit("This proves the theory is always correct.")


def test_contraction_flagged():
    assert "contraction" in _rules_hit("It doesn't replicate and it's unclear.")


def test_filter_by_category():
    hits = _rules_hit("There are very many subjects.", categories=["bias"])
    assert hits == {"bias_free"}


def test_min_severity_filters_out_info():
    text = "There are subjects that were studied."
    all_f = lint(text)
    major = lint(text, min_severity="major")
    assert len(major) <= len(all_f)
    assert all(f.severity == "major" for f in major)


def test_findings_carry_source_authority():
    f = next(f for f in lint("The end result was due to the fact that.") if f.rule == "wordiness")
    assert f.source == "Williams"


def test_register_a_custom_rule():
    before = len(all_rules())
    regex_rule("no_yelling", "tone", r"\bWOW\b", "Too excitable.", source="custom")
    assert len(all_rules()) == before + 1
    assert "no_yelling" in _rules_hit("WOW this is big.")


def test_rule_run_returns_findings():
    rule = Rule(name="t", category="c", message="m", detect=lambda s: [("x", "y")])
    out = rule.run("anything")
    assert len(out) == 1 and isinstance(out[0], Finding) and out[0].suggestion == "y"
