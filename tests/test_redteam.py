"""tests for the adversarial red-team (offline, fake responder)."""

from __future__ import annotations

from agent.redteam import ATTACKS, redteam


def test_all_holds_means_survived():
    res = redteam("solid answer", respond=lambda a, attack: (True, "holds"))
    assert res.survived
    assert res.weaknesses == []
    assert len(res.probes) == len(ATTACKS)


def test_a_break_is_recorded_as_weakness():
    def respond(answer, attack):
        if "counterexample" in attack:
            return False, "here is a counterexample"
        return True, "holds"

    res = redteam("shaky answer", respond=respond)
    assert not res.survived
    assert len(res.weaknesses) == 1
    assert "counterexample" in res.weaknesses[0].attack
    assert "FOUND WEAKNESSES" in res.pretty()


def test_custom_attack_list():
    res = redteam("x", attacks=["only one attack"], respond=lambda a, a2: (True, ""))
    assert len(res.probes) == 1


def test_robustness_is_severity_weighted():
    # break only the lowest-severity attack -> robustness stays high
    low = "What would a domain expert say is oversimplified here?"

    def respond(answer, attack):
        return (attack != low, "breaks" if attack == low else "holds")

    res = redteam("x", respond=respond)
    assert not res.survived
    assert res.robustness > 0.8  # only a small-severity hit


def test_weaknesses_sorted_by_severity():
    def respond(answer, attack):
        return (False, "breaks")  # everything breaks

    res = redteam("x", respond=respond)
    sevs = [p.severity for p in res.weaknesses]
    assert sevs == sorted(sevs, reverse=True)


def test_by_category_reports_per_category_survival():
    res = redteam("x", respond=lambda a, attack: (True, "ok"))
    cats = res.by_category()
    assert all(cats.values())  # all survived
    assert "factual" in cats
