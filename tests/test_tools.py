from agent.tools import available_tool_names, build_tools
from agent.tools.calculator import safe_calc
from agent.tools.datetime_tool import _now
from agent.tools.python_repl import run_python


def test_calculator_basic():
    assert safe_calc("2 + 2 * 3") == "8"


def test_calculator_functions_and_constants():
    assert safe_calc("sqrt(16)") == "4.0"
    assert safe_calc("factorial(5)") == "120"


def test_calculator_rejects_garbage():
    out = safe_calc("__import__('os')")
    assert "could not evaluate" in out or "not allowed" in out


def test_python_repl_runs():
    assert run_python("print(sum(range(5)))").strip() == "10"


def test_python_repl_blocks_dangerous():
    assert "blocked" in run_python("import os")
    assert "blocked" in run_python("open('x')")


def test_datetime_returns_something():
    out = _now()
    assert "local:" in out and "utc:" in out


def test_registry_has_expected_tools():
    names = available_tool_names()
    for expected in ("search", "wikipedia", "calculator", "python_repl", "save_text_to_file"):
        assert expected in names


def test_build_offline_subset():
    tools = build_tools(enabled=["calculator", "datetime"])
    assert {t.name for t in tools} == {"calculator", "datetime"}
