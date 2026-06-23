import pytest

from agent import personas
from agent.usage import count_tokens, estimate_cost, known_models


def test_personas_exist():
    names = personas.names()
    assert "researcher" in names
    assert "skeptic" in names


def test_persona_apply_splices_instructions():
    out = personas.apply("BASE PROMPT", "eli5")
    assert "BASE PROMPT" in out
    assert "Persona (eli5)" in out


def test_unknown_persona_raises():
    with pytest.raises(KeyError):
        personas.get("does-not-exist")


def test_count_tokens_positive():
    assert count_tokens("hello there friend") > 0


def test_estimate_cost():
    est = estimate_cost("a fairly short prompt", expected_output_tokens=200, model="gpt-4o")
    assert est.input_tokens > 0
    assert est.total_cost > 0
    assert "gpt-4o" in est.pretty()


def test_known_models():
    assert "gpt-4o" in known_models()
