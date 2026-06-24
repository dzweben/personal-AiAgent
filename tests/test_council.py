"""tests for the council capstone -- the whole chain driven by one fake complete()."""

from __future__ import annotations

from agent.council import convene


def _fake_complete(answer_text):
    """build a complete() that returns sensible canned replies for each stage of the chain."""

    def fake(prompt):
        if "HOLDS or BREAKS" in prompt:
            return "HOLDS, the answer is solid"
        if "supported, refuted, or unclear" in prompt:
            return "supported, this is well established"
        if "Reply OK if fine" in prompt:
            return "OK"
        return answer_text

    return fake


def test_council_runs_full_chain():
    answer = "The heart pumps blood through the body. It beats about 100000 times a day."
    res = convene("how does the heart work?", complete=_fake_complete(answer), personas=["a", "b"])
    assert res.answer
    assert res.mode in ("research", "define", "debate", "swarm", "calc")
    assert 0.0 <= res.scorecard.overall <= 1.0
    # every stage left a move in the recorder
    steps = [m.step for m in res.recorder.moves]
    assert steps == ["route", "ensemble", "factcheck", "critique", "redteam", "score"]


def test_council_records_claims_and_redteam():
    answer = "Mount Everest is the tallest mountain above sea level at 8849 meters high."
    res = convene("how tall is everest?", complete=_fake_complete(answer))
    assert res.claims  # at least one claim extracted + checked
    assert all(c.verdict == "supported" for c in res.claims)
    assert res.redteam_survived is True


def test_council_result_is_pretty_printable():
    res = convene("q", complete=_fake_complete("A clear factual statement about the world here."))
    out = res.pretty()
    assert "route:" in out and "red team:" in out and "score" in out


def test_council_routes_debate_question():
    res = convene(
        "should we switch to typescript?",
        complete=_fake_complete("Yes, types catch bugs early in large codebases."),
    )
    assert res.mode == "debate"
