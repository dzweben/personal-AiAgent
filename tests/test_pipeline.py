"""tests for the pipeline backbone."""

from __future__ import annotations

from agent.pipeline import Context, Pipeline


def test_context_set_get_note_chain():
    ctx = Context(query="hi").set("a", 1).note("did a thing")
    assert ctx.get("a") == 1
    assert ctx.get("missing", "default") == "default"
    assert ctx.notes == ["did a thing"]


def test_pipeline_runs_steps_in_order():
    def add_one(ctx):
        return ctx.set("n", ctx.get("n", 0) + 1)

    def double(ctx):
        return ctx.set("n", ctx.get("n") * 2)

    pipe = Pipeline().then("add", add_one).then("double", double)
    out = pipe.run(Context(query="x"))
    assert out.get("n") == 2  # (0+1)*2
    assert out.notes == ["ran add", "ran double"]
    assert pipe.names == ["add", "double"]


def test_pipeline_on_error_skip_keeps_going():
    def boom(ctx):
        raise ValueError("nope")

    def ok(ctx):
        return ctx.set("reached", True)

    out = Pipeline().then("boom", boom).then("ok", ok).run(Context(query="x"), on_error="skip")
    assert out.get("reached") is True
    assert any("skipped boom" in n for n in out.notes)


def test_pipeline_on_error_raise_propagates():
    def boom(ctx):
        raise ValueError("nope")

    import pytest

    with pytest.raises(ValueError):
        Pipeline().then("boom", boom).run(Context(query="x"))
