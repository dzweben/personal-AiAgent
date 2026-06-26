"""tests for the APA writing-style engine."""

from __future__ import annotations

from agent.scholar.apa import APA_RULES, apa_score, check_apa, style_prompt, suggest_revisions


def test_style_prompt_covers_the_rules():
    prompt = style_prompt("Introduction")
    assert "APA 7th" in prompt
    assert "active voice" in prompt
    assert "Introduction" in prompt
    # every rule group contributes
    assert prompt.count("- ") >= sum(len(v) for v in APA_RULES.values())


def test_checker_flags_contractions():
    v = check_apa("The result doesn't replicate and it's unclear.")
    assert any(x.rule == "no contractions" for x in v)


def test_checker_flags_colloquialisms():
    v = check_apa("There were a lot of really huge effects.")
    rules = [x.rule for x in v]
    assert rules.count("formal tone") >= 2


def test_checker_flags_overclaiming():
    v = check_apa("This study proves caffeine always causes insomnia.")
    assert any(x.rule == "no overclaiming" for x in v)


def test_checker_flags_anthropomorphism():
    v = check_apa("The study believes the effect is real.")
    assert any(x.rule == "no anthropomorphism" for x in v)


def test_checker_flags_low_numerals():
    v = check_apa("We examined 3 trials in total.")
    assert any(x.rule == "spell out numbers < 10" for x in v)


def test_clean_apa_prose_passes():
    good = (
        "Smith (2020) found that caffeine was associated with delayed sleep onset. "
        "The results suggest a dose-response relationship across three trials."
    )
    assert check_apa(good) == []
    assert apa_score(good) == 1.0


def test_apa_score_penalises_violations():
    bad = "The study proves it doesn't work and there were a lot of huge effects."
    assert apa_score(bad) < 0.6


def test_empty_text_scores_zero():
    assert apa_score("") == 0.0


def test_checker_flags_wordiness():
    v = check_apa("Due to the fact that funding was limited, in order to proceed, we waited.")
    rules = [x.rule for x in v]
    assert rules.count("conciseness") >= 2


def test_checker_flags_bias_language():
    v = check_apa("The elderly subjects and the disabled were tested.")
    flagged = {x.snippet for x in v if x.rule == "bias-free language"}
    assert "the elderly" in flagged and "subjects" in flagged and "the disabled" in flagged


def test_checker_flags_the_author():
    v = check_apa("The author found a strong effect. The present authors agree.")
    assert sum(1 for x in v if x.rule == "first person") >= 1


def test_checker_flags_intensifiers():
    v = check_apa("The effect was extremely large and highly significant.")
    assert any(x.rule == "cut empty intensifier" for x in v)


def test_suggest_revisions_applies_mechanical_fixes():
    out = suggest_revisions(
        "Due to the fact that the elderly were studied, a majority of subjects improved."
    )
    assert "because" in out
    assert "older adults" in out and "participants" in out
    assert "a majority of" not in out


def test_suggest_revisions_collapses_double_spaces():
    assert "  " not in suggest_revisions("too   many    spaces here")


def test_rules_cover_writing_substance_not_just_format():
    # APA writing standards, not formatting: these categories must be present
    for cat in (
        "continuity_and_flow",
        "conciseness",
        "clarity",
        "bias_free_language",
        "claims_and_evidence",
    ):
        assert cat in APA_RULES
