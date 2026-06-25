"""tests for the deep-research capstone (offline, fully injected)."""

from __future__ import annotations

from agent.deepresearch import deep_research

_ANSWERS = {
    "How does caffeine affect sleep?": "Caffeine blocks adenosine and delays sleep. See https://nih.gov/a.",
    "What is a safe daily dose?": "Up to 400 mg per day is safe for adults per https://fda.gov/b.",
    "Should you quit caffeine?": "Caffeine does not harm most adults at moderate doses.",
}


def _run(**kw):
    return deep_research(
        "How does caffeine affect sleep and what is a safe dose and should you quit?",
        answer=lambda q: _ANSWERS.get(q, "no data"),
        propose=lambda q: list(_ANSWERS.keys()),
        synthesize=lambda q, parts: "Caffeine delays sleep; 400 mg/day is safe. See https://nih.gov/a.",
        **kw,
    )


def test_pipeline_produces_all_sub_answers():
    res = _run()
    assert len(res.sub_answers) == 3
    assert res.answer.startswith("Caffeine delays sleep")


def test_sources_are_ranked_and_deduped():
    res = _run()
    domains = [s.domain for s in res.sources]
    assert "nih.gov" in domains and "fda.gov" in domains
    auths = [s.authority for s in res.sources]
    assert auths == sorted(auths, reverse=True)


def test_confidence_is_bounded():
    res = _run()
    assert 0.0 <= res.confidence <= 1.0


def test_contradictions_detected_across_sub_answers():
    answers = {
        "Is coffee good?": "Coffee improves focus in adults.",
        "Is coffee bad?": "Coffee does not improve focus in adults.",
    }
    res = deep_research(
        "Is coffee good or bad?",
        answer=lambda q: answers[q],
        propose=lambda q: list(answers.keys()),
        synthesize=lambda q, parts: "It depends.",
    )
    assert len(res.contradictions) >= 1
    # unresolved contradictions should drag confidence down vs a clean run
    assert res.confidence < _run().confidence


def test_markdown_report_has_sections():
    md = _run().to_markdown()
    assert "# Deep research report" in md
    assert "## Answer" in md and "## Sub-questions" in md


def test_knowledge_graph_built_from_answers():
    res = _run()
    assert res.graph is not None
    assert res.graph.entities  # some entities were harvested
