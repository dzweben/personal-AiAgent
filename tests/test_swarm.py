"""tests for the expanded swarm (final synthesis)."""

from __future__ import annotations

from agent.swarm import run_swarm


def test_swarm_synthesizes_a_final_answer():
    res = run_swarm(
        "design a caching layer",
        roles=["researcher", "critic"],
        rounds=1,
        contribute=lambda role, task, board: f"{role} contributes",
        synthesize=lambda task, board: "the consolidated final answer",
    )
    assert res.final == "the consolidated final answer"
    assert len(res.board) == 2
    assert "[final]" in res.pretty()


def test_swarm_without_synthesizer_stays_offline():
    # injecting contribute but not synthesize must not trigger any llm call
    res = run_swarm("task", roles=["a", "b"], contribute=lambda r, t, b: "x")
    assert res.final == ""
    assert len(res.board) == 2


def test_synthesizer_sees_the_whole_board():
    seen = {}

    def synthesize(task, board_text):
        seen["board"] = board_text
        return "done"

    run_swarm("t", roles=["a", "b"], contribute=lambda r, t, b: f"{r}!", synthesize=synthesize)
    assert "a!" in seen["board"] and "b!" in seen["board"]
