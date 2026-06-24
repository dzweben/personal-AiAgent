"""tests for the chaos batch. all offline -- injectable callables stand in for the llm."""

from __future__ import annotations

import pytest

# --- forge --llm path ---------------------------------------------------------------------


def test_forge_from_intent_uses_injected_model(monkeypatch, tmp_path):
    from agent.forge import forge_from_intent

    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    # a fake "model" that returns an expression wrapped in a code fence + chatter
    fake = lambda prompt: "Sure! Here you go:\n```python\nx.upper()\n```"  # noqa: E731
    path, expr = forge_from_intent("shouty", "uppercase text", complete=fake, directory=tmp_path)
    assert expr == "x.upper()"
    from agent.tools import build_tools

    tool = next(t for t in build_tools(enabled=["shouty"]) if t.name == "shouty")
    assert tool.func("hi") == "HI"


def test_forge_from_intent_still_sandboxes(tmp_path):
    from agent.forge import SafetyError, forge_from_intent

    evil = lambda prompt: "__import__('os').system('id')"  # noqa: E731
    with pytest.raises(SafetyError):
        forge_from_intent("evil", "do evil", complete=evil, directory=tmp_path)


# --- debate -------------------------------------------------------------------------------


def test_debate_alternates_and_synthesizes():
    from agent.debate import run_debate

    turns_seen = []

    def respond(speaker, q, so_far):
        turns_seen.append(speaker)
        return f"{speaker} argues about {q}"

    def moderate(q, so_far):
        return "balanced take"

    res = run_debate("is coffee good?", rounds=2, respond=respond, moderate=moderate)
    assert len(res.transcript) == 4  # 2 rounds * 2 speakers
    assert turns_seen == ["optimist", "skeptic", "optimist", "skeptic"]
    assert res.synthesis == "balanced take"
    assert "coffee" in res.pretty()


# --- evolve -------------------------------------------------------------------------------


def test_evolve_improves_or_holds_fitness():
    from agent.evolve import evolve

    res = evolve(generations=15, pop_size=12, seed=42)
    # best fitness must be monotonic non-decreasing (elitism guarantees it)
    assert res.history == sorted(res.history)
    assert res.best_fitness >= res.history[0]
    assert isinstance(res.prompt(), str) and res.prompt()


def test_evolve_is_deterministic_under_seed():
    from agent.evolve import evolve

    a = evolve(generations=8, seed=7)
    b = evolve(generations=8, seed=7)
    assert a.best == b.best and a.best_fitness == b.best_fitness


# --- critique -----------------------------------------------------------------------------


def test_refine_stops_when_judge_is_happy():
    from agent.critique import refine

    calls = {"n": 0}

    def judge(answer, principles):
        calls["n"] += 1
        return ["too vague"] if calls["n"] == 1 else []  # one issue, then clean

    def revise(answer, issues):
        return answer + " (revised)"

    res = refine("draft", judge=judge, revise=revise, max_rounds=5)
    assert res.final == "draft (revised)"
    assert res.rounds == 2
    assert res.changed


def test_parse_issues_handles_ok():
    from agent.critique import _parse_issues

    assert _parse_issues("OK") == []
    assert _parse_issues("- a\n- b") == ["a", "b"]


# --- dream --------------------------------------------------------------------------------


def test_dream_recombines_memory_words():
    from agent.dream import dream

    out = dream(["quantum computing and espresso machines", "sleep affects memory"], n=3, seed=1)
    assert len(out) == 3
    assert all("{" not in d for d in out)  # templates fully filled


def test_dream_empty_when_too_few_words():
    from agent.dream import dream

    assert dream(["a"], n=3) == []


# --- oracle -------------------------------------------------------------------------------


def test_oracle_draws_distinct_cards():
    from agent.oracle import draw

    out = draw("why is the sky blue?", n=3, seed=2)
    assert len(out) == 3
    assert all("why is the sky blue?" in line for line in out)
    assert len(set(out)) == 3  # distinct cards


# --- trace --------------------------------------------------------------------------------


def test_render_trace_draws_tree():
    from agent.trace import TraceStep, render_trace

    steps = [TraceStep("search", "coffee", "lots of results"), TraceStep("calculator", "2+2", "4")]
    out = render_trace(steps, title="demo")
    assert "◆ demo" in out
    assert "search" in out and "calculator" in out
    assert "└─" in out  # last step gets the corner


# --- swarm --------------------------------------------------------------------------------


def test_swarm_runs_each_role_per_round():
    from agent.swarm import run_swarm

    def contribute(role, task, board):
        return f"{role} on {task}"

    res = run_swarm("ai safety", roles=["researcher", "critic"], rounds=2, contribute=contribute)
    assert len(res.board) == 4
    assert res.last_by("critic") == "critic on ai safety"


# --- capsule ------------------------------------------------------------------------------


def test_capsule_roundtrips():
    from agent.capsule import decode, encode

    obj = {"topic": "tea", "sources": ["a", "b"], "n": 3, "nested": {"x": [1, 2]}}
    cap = encode(obj)
    assert cap.startswith("AICAP1:")
    assert decode(cap) == obj


def test_capsule_rejects_garbage():
    from agent.capsule import CapsuleError, decode

    with pytest.raises(CapsuleError):
        decode("not a capsule")


# --- timetravel ---------------------------------------------------------------------------


def test_timetravel_snapshots_and_branches(tmp_path):
    from agent.timetravel import TimeTravel

    tt = TimeTravel(path=str(tmp_path / "tl"))
    tt.snapshot("turn one", "asked about cats")
    tt.snapshot("turn one\nturn two", "asked about dogs")
    timeline = tt.timeline()
    assert len(timeline) == 2
    assert timeline[0].label == "asked about dogs"  # newest first

    tt.branch("alt")
    assert "alt" in tt.branches()
    tt.snapshot("turn one\nturn two\nalt turn", "alternate path")
    assert len(tt.timeline()) == 3


# --- mcp adapter --------------------------------------------------------------------------


def test_mcp_tool_definitions_shape():
    from agent.mcp_server import to_mcp_tools

    defs = to_mcp_tools(enabled=["calculator"])
    assert defs and defs[0]["name"] == "calculator"
    assert defs[0]["inputSchema"]["type"] == "object"
    assert "input" in defs[0]["inputSchema"]["properties"]
