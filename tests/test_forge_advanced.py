"""tests for the expanded toolsmith: multi-statement bodies and forged-tool management."""

from __future__ import annotations

import pytest

from agent.forge import (
    SafetyError,
    forge,
    list_forged,
    remove_forged,
    render_plugin_body,
    validate_source,
)


def test_multi_statement_body_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    body = "n = int(x)\nif n % 15 == 0:\n    return 'fizzbuzz'\nif n % 3 == 0:\n    return 'fizz'\nreturn str(n)"
    forge("fizz", "fizzbuzz a number", body=body, directory=tmp_path)
    from agent.tools import build_tools

    tool = next(t for t in build_tools(enabled=["fizz"]) if t.name == "fizz")
    assert tool.func("15") == "fizzbuzz"
    assert tool.func("9") == "fizz"
    assert tool.func("7") == "7"


def test_body_is_still_sandboxed():
    src = render_plugin_body("evil", "nope", "import os\nreturn os.getcwd()")
    with pytest.raises(SafetyError):
        validate_source(src)


def test_forge_requires_exactly_one_of_expr_or_body(tmp_path):
    with pytest.raises(SafetyError):
        forge("x", "both", expr="x", body="return x", directory=tmp_path)
    with pytest.raises(SafetyError):
        forge("x", "neither", directory=tmp_path)


def test_list_and_remove_forged(monkeypatch, tmp_path):
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    forge("alpha", "a", expr="x.upper()", directory=tmp_path)
    forge("beta", "b", expr="x.lower()", directory=tmp_path)
    assert set(list_forged(tmp_path)) == {"alpha", "beta"}
    assert remove_forged("alpha", tmp_path) is True
    assert list_forged(tmp_path) == ["beta"]
    assert remove_forged("nonexistent", tmp_path) is False


def test_remove_refuses_handwritten_plugin(tmp_path):
    # a plugin the toolsmith did NOT generate must not be deletable via remove_forged
    (tmp_path / "handmade.py").write_text("# a human wrote this\n")
    with pytest.raises(SafetyError):
        remove_forged("handmade", tmp_path)
    assert (tmp_path / "handmade.py").exists()
