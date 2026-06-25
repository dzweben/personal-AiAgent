"""tests for the question planner."""

from __future__ import annotations

from agent.planner import Plan, decompose, naive_decompose


def test_naive_decompose_splits_compound_questions():
    subs = naive_decompose("How does X work and what causes Y and when did Z happen?")
    assert len(subs) >= 2
    assert all(s.endswith("?") for s in subs)


def test_simple_question_stays_whole():
    subs = naive_decompose("Why is the sky blue?")
    assert subs == ["Why is the sky blue?"]


def test_decompose_adds_synthesis_node():
    plan = decompose("How does A work and what is B and why does C happen?")
    assert not plan.is_trivial
    last = plan.subquestions[-1]
    assert last.deps == list(range(len(plan.subquestions) - 1))
    assert "Synthesise" in last.text


def test_roots_are_dependency_free():
    plan = decompose("What is A and what is B and what is C?")
    roots = plan.roots()
    assert all(not plan.subquestions[i].deps for i in roots)
    # the synthesis node is not a root
    assert (len(plan.subquestions) - 1) not in roots


def test_injected_proposer_is_used():
    plan = decompose("anything", propose=lambda q: ["sub one here", "sub two here"])
    texts = [sq.text for sq in plan.subquestions]
    assert "sub one here" in texts and "sub two here" in texts


def test_trivial_plan_has_no_synthesis():
    plan = decompose("Why is the sky blue?")
    assert plan.is_trivial
    assert isinstance(plan, Plan)
