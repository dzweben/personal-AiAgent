"""tune the council's persona line-up with a genetic algorithm.

which personas you put on the council changes the answer. so instead of guessing, evolve the
line-up: treat a set of personas as a genome, score each candidate by the quality of the
ensemble answer it produces (via the offline scorecard), and let agent.evolve breed the best
mix. then convene the real council with that line-up.

the answer-generating callable is injectable, so the search is fully testable offline.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.ensemble import ensemble
from agent.evolve import evolve
from agent.scorecard import score

# a roomy pool of personas the search can draw a line-up from.
CANDIDATE_PERSONAS = [
    "researcher",
    "skeptic",
    "eli5",
    "journalist",
    "tutor",
    "devils_advocate",
    "pragmatist",
    "historian",
]


@dataclass
class PersonaSearchResult:
    personas: list[str]
    fitness: float
    history: list[float]


def evolve_personas(
    question: str,
    answer=None,
    pool: list[str] | None = None,
    generations: int = 8,
    pop_size: int = 12,
    seed: int = 0,
    settings=None,
) -> PersonaSearchResult:
    """search for the persona line-up that yields the best-scoring ensemble answer.

    `answer(persona, q) -> str` is injectable; by default it routes through the llm. the fitness
    of a line-up is the scorecard of the ensemble's merged answer (with a tiny penalty per extra
    persona, so it doesn't just pile everyone on).
    """
    pool = pool or CANDIDATE_PERSONAS

    if answer is None:
        from agent.llm import complete

        def answer(persona, q):
            return complete(
                q, settings=settings, system=f"Answer as a {persona}, in 3-4 sentences."
            )

    # cache so the same line-up isn't re-scored repeatedly during the search
    cache: dict[tuple[str, ...], float] = {}

    def fitness(genome: list[str]) -> float:
        key = tuple(genome)
        if key not in cache:
            merged = ensemble(question, personas=list(genome), answer=answer).merged
            penalty = 0.03 * max(0, len(genome) - 3)
            cache[key] = round(score(merged).overall - penalty, 4)
        return cache[key]

    result = evolve(
        pool=pool, fitness=fitness, generations=generations, pop_size=pop_size, seed=seed
    )
    return PersonaSearchResult(
        personas=result.best, fitness=result.best_fitness, history=result.history
    )


def convene_evolved(question: str, complete=None, settings=None, seed: int = 0, **convene_kwargs):
    """find the best persona line-up, then convene the council with it.

    returns (CouncilResult, PersonaSearchResult). when `complete` is given, the same callable
    drives both the persona search and the council, so it's testable offline.
    """
    from agent.council import convene

    answer_fn = None
    if complete is not None:

        def answer_fn(persona, q):
            return complete(f"As a {persona}, answer: {q}")

    search = evolve_personas(question, answer=answer_fn, seed=seed, settings=settings)
    result = convene(
        question, complete=complete, personas=search.personas, settings=settings, **convene_kwargs
    )
    return result, search
