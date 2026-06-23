"""tests for the newer offline tools that do not need the network."""

import pytest

from agent.tools.convert import _convert_temp, _convert_units
from agent.tools.text import _regex_extract, _text_stats


def test_unit_convert_length():
    out = _convert_units("10 km to mi")
    assert "mi" in out and "6.21" in out


def test_unit_convert_mass():
    out = _convert_units("5 lb to kg")
    assert "kg" in out


def test_unit_convert_cross_dimension_fails():
    out = _convert_units("5 kg to m")
    assert "cannot convert" in out


def test_temp_conversions():
    assert _convert_temp(100, "c", "f") == "100C = 212.0F"
    assert _convert_temp(32, "f", "c") == "32F = 0.0C"


def test_text_stats():
    out = _text_stats("This is a simple test. It has two short sentences here.")
    assert "words:" in out
    assert "flesch reading ease" in out


def test_regex_extract():
    out = _regex_extract(r"\d+ ::: there are 3 cats and 12 dogs")
    assert "3" in out and "12" in out


def test_regex_extract_bad_format():
    assert "format is" in _regex_extract("no separator here")


def test_symbolic_math_if_available():
    sympy = pytest.importorskip("sympy")  # noqa: F841
    from agent.tools.symbolic import _symbolic

    assert _symbolic("solve x**2 - 4") == "[-2, 2]"
    assert "cos" in _symbolic("diff sin(x)*x")
