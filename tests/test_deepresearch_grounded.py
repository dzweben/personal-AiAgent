"""tests for the grounded / parallel / verified / experiential deep-research integration."""

from __future__ import annotations

from agent.deepresearch import deep_research
from agent.experience import Experience
from agent.factcheck import grounded_verifier, summarize_verdicts
from agent.grounding import Passage

_KB = {
    "sleep": [
        Passage("Caffeine blocks adenosine and delays sleep onset.", "https://nih.gov/a", 1.0)
    ],
    "dose": [
        Passage("Up to 400 mg of caffeine per day is safe for adults.", "https://fda.gov/b", 1.0)
    ],
}


def _retrieve(q):
    for k, v in _KB.items():
        if k in q.lower():
            return v
    return [Passage("general background information here", "https://ex.org/c", 0.5)]


def _complete(prompt):
    import re

    urls = " ".join(re.findall(r"https?://[^\s)]+", prompt))
    return f"Grounded answer about caffeine and adenosine. {urls}"


def _propose(q):
    return ["How does caffeine affect sleep?", "What is a safe dose?"]


def test_grounded_answers_cite_real_sources():
    res = deep_research(
        "caffeine sleep and dose",
        propose=_propose,
        retrieve=_retrieve,
        complete=_complete,
        synthesize=lambda q, parts: "Caffeine delays sleep; 400 mg is safe. https://nih.gov/a",
    )
    domains = {s.domain for s in res.sources}
    assert "nih.gov" in domains and "fda.gov" in domains


def test_verification_runs_on_final_answer():
    res = deep_research(
        "caffeine sleep and dose",
        propose=_propose,
        retrieve=_retrieve,
        complete=_complete,
        synthesize=lambda q, parts: "Caffeine delays sleep onset in adults.",
        verify=grounded_verifier(_retrieve),
    )
    assert res.claims
    assert summarize_verdicts(res.claims)["supported"] >= 1


def test_experience_remembers_the_run(tmp_path):
    exp = Experience(str(tmp_path / "exp"))
    deep_research(
        "caffeine sleep and dose",
        propose=_propose,
        retrieve=_retrieve,
        complete=_complete,
        synthesize=lambda q, parts: "An answer.",
        experience=exp,
    )
    assert exp.stats()["notes"] == 1


def test_parallel_and_sequential_agree():
    kw = {
        "propose": _propose,
        "answer": lambda q: f"answer to {q}",
        "synthesize": lambda q, parts: " | ".join(parts.values()),
    }
    par = deep_research("q", parallel=True, **kw)
    seq = deep_research("q", parallel=False, **kw)
    assert par.sub_answers == seq.sub_answers
