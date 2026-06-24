"""tests for the toolsmith. all offline -- no llm, no network.

the important ones are the sandbox tests: forged code must not be able to reach os/sys/eval/etc.
"""

from __future__ import annotations

import pytest

from agent.forge import (
    SafetyError,
    forge,
    render_plugin,
    validate_source,
)

# ---- the safety sandbox ------------------------------------------------------------------


def test_clean_expression_passes_validation():
    src = render_plugin("double", "doubles a number", "float(x) * 2")
    validate_source(src)  # should not raise


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os').system('echo hi')",
        "open('/etc/passwd').read()",
        "eval('1+1')",
        "exec('x=1')",
        "x.__class__.__bases__",
        "getattr(x, 'foo')",
        "globals()",
    ],
)
def test_dangerous_expressions_are_rejected(expr):
    src = render_plugin("danger", "nope", expr)
    with pytest.raises(SafetyError):
        validate_source(src)


def test_disallowed_import_is_rejected():
    bad = "import os\nos.getcwd()\n"
    with pytest.raises(SafetyError):
        validate_source(bad)


def test_allowed_import_is_fine():
    src = render_plugin("rng", "random number", "random.randint(1, int(x))")
    validate_source(src)
    assert "import random" in src


def test_bad_tool_name_rejected():
    with pytest.raises(SafetyError):
        render_plugin("123 not valid!", "x", "x")


# ---- end to end: forge, hot-load, run ----------------------------------------------------


def test_forge_creates_loadable_working_tool(monkeypatch, tmp_path):
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    path = forge("double", "doubles a number", "float(x) * 2", directory=tmp_path)
    assert path.exists()

    from agent.tools import available_tool_names, build_tools

    assert "double" in available_tool_names()

    tool = next(t for t in build_tools(enabled=["double"]) if t.name == "double")
    assert tool.func("21") == "42.0"


def test_forge_string_tool_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    forge("backwards", "reverse text", "x[::-1]", directory=tmp_path)
    from agent.tools import build_tools

    tool = next(t for t in build_tools(enabled=["backwards"]) if t.name == "backwards")
    assert tool.func("abc") == "cba"


def test_forge_refuses_unsafe_body(tmp_path):
    with pytest.raises(SafetyError):
        forge("evil", "nope", "__import__('os').system('id')", directory=tmp_path)
    assert not (tmp_path / "evil.py").exists()  # nothing written when it's rejected


def test_forge_wont_clobber_without_overwrite(tmp_path):
    forge("once", "first", "x", directory=tmp_path)
    with pytest.raises(FileExistsError):
        forge("once", "second", "x.upper()", directory=tmp_path)
    # overwrite=True is allowed
    forge("once", "second", "x.upper()", directory=tmp_path, overwrite=True)
