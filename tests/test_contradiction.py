"""tests for the contradiction detector."""

from __future__ import annotations

from agent.contradiction import find_contradictions


def test_detects_negation_conflict():
    answers = [
        "Exercise improves cardiovascular health in adults.",
        "Exercise does not improve cardiovascular health in adults.",
    ]
    cons = find_contradictions(answers)
    assert any("negate" in c.reason for c in cons)


def test_detects_number_conflict():
    answers = [
        "The recommended limit is 400 milligrams daily for healthy adults.",
        "The recommended limit is 200 milligrams daily for healthy adults.",
    ]
    cons = find_contradictions(answers)
    assert any("figures" in c.reason for c in cons)


def test_detects_antonym_conflict():
    answers = [
        "The new policy will increase overall employment across the region.",
        "The new policy will decrease overall employment across the region.",
    ]
    cons = find_contradictions(answers)
    assert any("opposing terms" in c.reason for c in cons)


def test_unrelated_claims_dont_contradict():
    answers = [
        "The Eiffel Tower is located in Paris, France.",
        "Photosynthesis converts sunlight into chemical energy in plants.",
    ]
    assert find_contradictions(answers) == []


def test_injected_checker_can_veto():
    answers = [
        "Coffee increases alertness in most adults.",
        "Coffee does not increase alertness in most adults.",
    ]
    # checker always says "not actually a contradiction" -> nothing reported
    assert find_contradictions(answers, check=lambda a, b: False) == []
