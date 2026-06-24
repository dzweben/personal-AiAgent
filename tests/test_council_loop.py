"""tests for the council's self-correction loop (offline, stateful fake complete)."""

from __future__ import annotations

from agent.council import convene


def _improving_complete():
    """a fake where the first draft is weak (red team breaks it) but a revision fixes it."""

    def fake(prompt):
        if "Rewrite to fix" in prompt:
            return "IMPROVED: water boils at 100 C and freezes at 0 C, per standard physics."
        if "HOLDS or BREAKS" in prompt:
            return "HOLDS, solid" if "IMPROVED" in prompt else "BREAKS, too vague"
        if "supported, refuted" in prompt:
            return "supported, well established"
        if "Reply OK if fine" in prompt:
            return "OK"
        return "water changes state somehow"

    return fake


def test_loop_revises_until_redteam_survives():
    res = convene("how does water change state?", complete=_improving_complete(), max_iterations=4)
    assert res.iterations == 2  # one weak pass, one fix
    assert res.redteam_survived is True
    assert "IMPROVED" in res.answer
    # score history is non-empty and improved across the loop
    assert len(res.score_history) == 2
    assert res.score_history[-1] > res.score_history[0]
    steps = [m.step for m in res.recorder.moves]
    assert "revise" in steps and "recheck" in steps


def test_single_pass_when_max_iterations_is_one():
    res = convene("anything", complete=_improving_complete(), max_iterations=1)
    assert res.iterations == 1
    steps = [m.step for m in res.recorder.moves]
    assert "revise" not in steps  # no loop on a single pass


def test_loop_stops_early_when_already_good():
    # always-holds fake: nothing to fix, so it should not loop even with room to
    def fake(prompt):
        if "HOLDS or BREAKS" in prompt:
            return "HOLDS"
        if "supported, refuted" in prompt:
            return "supported"
        if "Reply OK if fine" in prompt:
            return "OK"
        return "A solid factual answer about the topic at hand with detail."

    res = convene("q", complete=fake, max_iterations=5, target_score=0.0)
    assert res.iterations == 1  # survived on first pass, target 0.0 already met


def test_loop_stops_when_no_actionable_feedback_remains():
    # even with an unreachable target, the loop halts once the red team survives and every
    # claim is supported -- there's nothing concrete left to feed back, so it stops gracefully.
    res = convene(
        "how does water change state?",
        complete=_improving_complete(),
        max_iterations=5,
        target_score=0.99,
    )
    assert res.iterations == 2
    assert res.redteam_survived is True
