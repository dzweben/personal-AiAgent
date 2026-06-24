"""darwinian prompt optimisation. yes, really.

the agent's system prompt is just a string made of fragments. so: treat a set of fragments as
a genome, mutate and cross-breed a population of prompts, score each with a fitness function,
keep the fittest, repeat. natural selection on the agent's own instructions.

the genetics here are pure python and deterministic under a seeded rng, so the whole thing is
testable offline. the fitness function is injectable -- the default is a cheap heuristic so you
can watch it converge with no api key, but you can pass a real eval-harness-backed fitness to
evolve against actual model behaviour.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# a little gene pool of prompt fragments to draw from.
DEFAULT_POOL = [
    "Be concise and direct.",
    "Cite your sources with urls.",
    "Think step by step before answering.",
    "Prefer primary sources over blogs.",
    "Flag uncertainty explicitly.",
    "Avoid speculation; stick to evidence.",
    "Use plain language a beginner can follow.",
    "Quantify claims with numbers where possible.",
    "List counterarguments before concluding.",
    "End with a one-line takeaway.",
]


def render(genome: list[str]) -> str:
    """turn a genome (ordered fragments) into a usable system prompt string."""
    return " ".join(genome)


def heuristic_fitness(genome: list[str]) -> float:
    """a stand-in fitness with no api needed: reward useful traits, punish bloat and repeats.

    it is obviously not a real measure of prompt quality -- it just gives the genetics something
    to climb so you can see and test the machinery. swap in a real one for actual tuning.
    """
    prompt = render(genome).lower()
    score = 0.0
    for keyword in ("concise", "step by step", "sources", "uncertainty", "takeaway"):
        if keyword in prompt:
            score += 1.0
    score -= 0.15 * max(0, len(genome) - 5)  # bloat penalty
    score -= 0.5 * (len(genome) - len(set(genome)))  # duplicate penalty
    return score


@dataclass
class EvolveResult:
    best: list[str]
    best_fitness: float
    history: list[float] = field(default_factory=list)
    diversity_history: list[float] = field(default_factory=list)

    def prompt(self) -> str:
        return render(self.best)


def _mutate(genome: list[str], pool: list[str], rng: random.Random) -> list[str]:
    g = list(genome)
    roll = rng.random()
    if roll < 0.34 and len(g) < 8:  # insert
        g.insert(rng.randrange(len(g) + 1), rng.choice(pool))
    elif roll < 0.67 and len(g) > 1:  # drop
        del g[rng.randrange(len(g))]
    else:  # swap one out
        g[rng.randrange(len(g))] = rng.choice(pool)
    return g


def _crossover(a: list[str], b: list[str], rng: random.Random) -> list[str]:
    cut_a = rng.randrange(1, len(a)) if len(a) > 1 else 1
    cut_b = rng.randrange(1, len(b)) if len(b) > 1 else 1
    child = a[:cut_a] + b[cut_b:]
    return child or list(a)


def _tournament(pop, fitness, rng: random.Random, k: int = 3):
    contenders = [rng.choice(pop) for _ in range(min(k, len(pop)))]
    return max(contenders, key=fitness)


def _diversity(population: list[list[str]]) -> float:
    """fraction of the population that is genetically unique. 1.0 = no duplicates."""
    if not population:
        return 0.0
    unique = {tuple(g) for g in population}
    return round(len(unique) / len(population), 3)


def evolve(
    pool: list[str] | None = None,
    fitness=heuristic_fitness,
    generations: int = 12,
    pop_size: int = 16,
    seed: int = 0,
    mutate=_mutate,
    crossover=_crossover,
    mutation_rate: float = 0.7,
    keep_diverse: bool = True,
) -> EvolveResult:
    """run a small genetic algorithm over prompt genomes and return the best one found.

    `mutate(genome, pool, rng)` and `crossover(a, b, rng)` are swappable so you can plug in your
    own operators. with keep_diverse, elitism dedupes survivors so the population doesn't collapse
    onto one genome -- which keeps the search from getting stuck in a local optimum too early.
    """
    rng = random.Random(seed)
    pool = pool or DEFAULT_POOL
    population = [rng.sample(pool, k=rng.randint(2, min(5, len(pool)))) for _ in range(pop_size)]
    best = max(population, key=fitness)
    history = [fitness(best)]
    diversity_history = [_diversity(population)]

    for _ in range(generations):
        ranked = sorted(population, key=fitness, reverse=True)
        if keep_diverse:
            # keep the best *distinct* genomes as elites
            survivors, seen = [], set()
            for g in ranked:
                key = tuple(g)
                if key not in seen:
                    seen.add(key)
                    survivors.append(g)
                if len(survivors) >= max(2, pop_size // 4):
                    break
        else:
            survivors = ranked[: max(2, pop_size // 4)]
        children = list(survivors)
        while len(children) < pop_size:
            parent_a = _tournament(population, fitness, rng)
            parent_b = _tournament(population, fitness, rng)
            child = crossover(parent_a, parent_b, rng)
            if rng.random() < mutation_rate:
                child = mutate(child, pool, rng)
            children.append(child)
        population = children
        gen_best = max(population, key=fitness)
        if fitness(gen_best) > fitness(best):
            best = gen_best
        history.append(fitness(best))
        diversity_history.append(_diversity(population))

    return EvolveResult(
        best=best,
        best_fitness=fitness(best),
        history=history,
        diversity_history=diversity_history,
    )


def eval_harness_fitness(agent, cases, settings=None):
    """build a fitness that scores a genome by running the agent (with that prompt) over cases.

    this is the "evolve against real behaviour" hook: each genome becomes a system prompt, the
    agent answers the eval cases, and the fitness is the mean scorecard of its answers. needs a
    live agent + api key, so it's not exercised in the offline test suite.
    """
    from agent.evaluate import EvalCase, run_eval  # noqa: F401 - imported for the caller's clarity
    from agent.scorecard import score as _score

    def fitness(genome: list[str]) -> float:
        prompt = render(genome)
        scores = []
        for case in cases:
            answer = agent.research(case, system_override=prompt).output_text  # type: ignore[call-arg]
            scores.append(_score(answer).overall)
        return round(sum(scores) / len(scores), 4) if scores else 0.0

    return fitness
