"""tests for claim extraction + fact-checking (offline, fake verifier)."""

from __future__ import annotations

from agent.factcheck import extract_claims, factcheck, summarize_verdicts


def test_extract_claims_drops_questions_and_advice():
    text = (
        "The Eiffel Tower is in Paris. You should visit it someday. "
        "Is it tall? It was completed in 1889."
    )
    claims = extract_claims(text)
    assert "The Eiffel Tower is in Paris." in claims
    assert "It was completed in 1889." in claims
    assert all("?" not in c for c in claims)
    assert not any(c.lower().startswith("you ") for c in claims)


def test_extract_claims_respects_max():
    text = " ".join(f"Fact number {i} is a real statement here." for i in range(20))
    assert len(extract_claims(text, max_claims=5)) == 5


def test_factcheck_applies_verifier_and_tallies():
    text = "Honey almost never spoils over time. The sun is cold. Bees make honey from nectar."

    def verify(claim):
        return ("refuted", "no") if "cold" in claim else ("supported", "yes")

    checks = factcheck(text, verify=verify)
    tally = summarize_verdicts(checks)
    assert tally["refuted"] == 1
    assert tally["supported"] == 2
    assert all(c.verdict in ("supported", "refuted", "unclear") for c in checks)


def test_factcheck_coerces_unknown_verdicts_to_unclear():
    checks = factcheck("Cats have whiskers everywhere on their bodies.", verify=lambda c: ("???", ""))
    assert checks[0].verdict == "unclear"
