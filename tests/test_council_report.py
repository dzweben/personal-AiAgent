"""tests for council confidence aggregation and the markdown/capsule report."""

from __future__ import annotations

from agent.council import convene


def _fake(answer):
    def f(prompt):
        if "HOLDS or BREAKS" in prompt:
            return "HOLDS"
        if "supported, refuted" in prompt:
            return "supported"
        if "Reply OK if fine" in prompt:
            return "OK"
        return answer

    return f


def test_confidence_blends_quality_credibility_robustness():
    res = convene("q", complete=_fake("Water boils at 100 C and freezes at 0 C, well documented."))
    assert 0.0 <= res.confidence <= 1.0
    # a clean run (supported claims, survived red team) should be reasonably confident
    assert res.confidence > 0.5


def test_low_confidence_when_claims_refuted():
    def fake(prompt):
        if "HOLDS or BREAKS" in prompt:
            return "BREAKS, weak"
        if "supported, refuted" in prompt:
            return "refuted, this is false"
        if "Reply OK if fine" in prompt:
            return "OK"
        return "The moon is made of cheese and the sun orbits the earth daily."

    good = convene("q", complete=_fake("A solid, supported, well documented factual answer here."))
    bad = convene("q", complete=fake, max_iterations=1)
    assert bad.confidence < good.confidence


def test_markdown_report_has_sections():
    md = convene(
        "q", complete=_fake("A factual statement about the world that is documented.")
    ).to_markdown()
    assert "# Council report" in md
    assert "## Answer" in md and "## Claims checked" in md and "## Red team" in md


def test_capsule_roundtrips_the_run():
    from agent.replay import Recorder

    res = convene("q", complete=_fake("A documented factual statement about reality here."))
    cap = res.to_capsule()
    restored = Recorder.from_capsule(cap)
    assert restored.moves  # the recorded steps survive the roundtrip
