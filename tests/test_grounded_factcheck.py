"""tests for source-grounded fact verification (offline, fake retrieval)."""

from __future__ import annotations

from agent.factcheck import factcheck, grounded_verifier, summarize_verdicts
from agent.grounding import Passage

_KB = {
    "caffeine": [
        Passage(
            "Caffeine blocks adenosine and delays sleep onset in adults.", "https://nih.gov/a", 1.0
        )
    ],
    "moon": [
        Passage("The moon is a rocky body and is not made of cheese.", "https://nasa.gov/b", 1.0)
    ],
}


def _retrieve(claim):
    for k, v in _KB.items():
        if k in claim.lower():
            return v
    return []


def test_supported_claim_matches_source():
    verify = grounded_verifier(_retrieve)
    verdict, note = verify("Caffeine delays sleep onset in adults significantly")
    assert verdict == "supported"
    assert "nih.gov" in note


def test_refuted_claim_clashes_with_source():
    verify = grounded_verifier(_retrieve)
    verdict, _ = verify("The moon is made of cheese entirely")
    assert verdict == "refuted"


def test_unclear_when_no_sources():
    verify = grounded_verifier(_retrieve)
    verdict, _ = verify("Dark matter is definitely composed of axions")
    assert verdict == "unclear"


def test_grounded_verifier_plugs_into_factcheck():
    text = "Caffeine delays sleep onset in adults. The moon is made of cheese entirely."
    checks = factcheck(text, verify=grounded_verifier(_retrieve))
    tally = summarize_verdicts(checks)
    assert tally["supported"] >= 1 and tally["refuted"] >= 1


def test_complete_backed_verifier_uses_passages():
    seen = {}

    def complete(prompt):
        seen["prompt"] = prompt
        return "supported, per the source"

    verify = grounded_verifier(_retrieve, complete=complete)
    verdict, _ = verify("Caffeine delays sleep")
    assert verdict == "supported"
    assert "nih.gov" in seen["prompt"]  # the passage text/url reached the model
