"""tests that the writer actually writes in APA style, not just APA citations."""

from __future__ import annotations

from agent.scholar.paper import Paper
from agent.scholar.writing import draft_section

_PAPERS = [
    Paper(
        title="Caffeine study",
        abstract="Caffeine delays sleep.",
        authors=["Jane Smith"],
        year=2021,
        doi="10.1/a",
    )
]


def test_apa_style_prompt_is_used():
    seen = {}

    def complete(prompt, system=None, settings=None):
        seen["system"] = system
        return "Smith (2021) found an association."

    draft_section("Introduction", "caffeine", _PAPERS, complete=complete, style="apa")
    assert "APA 7th" in seen["system"]
    assert "active voice" in seen["system"]


def test_apa_violations_trigger_a_rewrite():
    calls = []

    def complete(prompt, system=None, settings=None):
        calls.append(prompt)
        if "Rewrite the passage" in prompt:
            return "Smith (2021) found that caffeine was associated with delayed sleep onset."
        return "The study proves caffeine doesn't work with a lot of huge effects."

    sec = draft_section("Intro", "caffeine", _PAPERS, complete=complete, style="apa")
    assert any("Rewrite the passage" in c for c in calls)  # self-correction happened
    from agent.scholar.apa import check_apa

    assert check_apa(sec.body) == []  # final body is APA-clean


def test_clean_draft_skips_rewrite():
    calls = []

    def complete(prompt, system=None, settings=None):
        calls.append(prompt)
        return "Smith (2021) reported that caffeine was associated with delayed sleep onset."

    draft_section("Intro", "caffeine", _PAPERS, complete=complete, style="apa")
    assert not any("Rewrite the passage" in c for c in calls)  # no violations -> no rewrite


def test_enforce_apa_can_be_disabled():
    calls = []

    def complete(prompt, system=None, settings=None):
        calls.append(prompt)
        return "The study proves it doesn't work."  # violations, but enforcement off

    draft_section("Intro", "caffeine", _PAPERS, complete=complete, style="apa", enforce_apa=False)
    assert len(calls) == 1  # drafted once, no rewrite
