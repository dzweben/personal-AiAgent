"""deep research: the capability capstone that puts the whole brain together.

given a gnarly question, it:

  1. plans  -- decomposes it into a sub-question DAG (agent.planner)
  2. executes -- answers each sub-question, dependencies first (agent.dag)
  3. synthesises -- folds the sub-answers into one overall answer
  4. cross-checks -- builds a knowledge graph, flags contradictions, ranks sources
  5. reports -- a confidence score and a full markdown writeup

every model-touching part is injectable, so the entire pipeline runs offline in tests with a
couple of fakes. point it at a real `complete` (or let each sub-question go through the council)
and it becomes an actual autonomous research loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.contradiction import find_contradictions
from agent.dag import Node, run_dag
from agent.knowledge import KnowledgeGraph
from agent.planner import decompose
from agent.scorecard import score
from agent.sources import extract_sources, sourcing_score


@dataclass
class DeepResult:
    question: str
    plan: object
    sub_answers: dict[str, str] = field(default_factory=dict)
    answer: str = ""
    contradictions: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    graph: KnowledgeGraph | None = None
    claims: list = field(default_factory=list)

    @property
    def confidence(self) -> float:
        """blend answer quality, sourcing, and a penalty for unresolved contradictions."""
        quality = score(self.answer, n_sources=len(self.sources)).overall
        srcs = sourcing_score(self.answer) if self.answer else 0.0
        penalty = min(0.4, 0.1 * len(self.contradictions))
        return round(max(0.0, 0.6 * quality + 0.4 * srcs - penalty), 3)

    def to_markdown(self) -> str:
        lines = [
            "# Deep research report\n",
            f"**Question:** {self.question}  ",
            f"**Confidence:** {self.confidence:.2f}  "
            f"**Sub-questions:** {len(self.sub_answers)}  "
            f"**Contradictions:** {len(self.contradictions)}\n",
            "## Answer\n",
            self.answer,
            "\n## Sub-questions\n",
        ]
        for q, a in self.sub_answers.items():
            lines.append(f"### {q}\n\n{a}\n")
        if self.contradictions:
            lines.append("## ⚠️ Contradictions found\n")
            for c in self.contradictions:
                lines.append(f"- {c.reason}: _{c.a}_ vs _{c.b}_")
        if self.sources:
            lines.append("\n## Sources (ranked)\n")
            for s in self.sources:
                lines.append(f"- [{s.authority:.2f}] {s.url}")
        return "\n".join(lines)


def _default_answer(complete, settings):
    """answer a single sub-question via the council, returning just the answer text."""
    from agent.council import convene

    def answer(subq: str) -> str:
        return convene(subq, complete=complete, settings=settings).answer

    return answer


def deep_research(
    question: str,
    answer=None,
    propose=None,
    synthesize=None,
    complete=None,
    settings=None,
    max_subs: int = 5,
    retrieve=None,
    parallel: bool = True,
    workers: int = 4,
    experience=None,
    verify=None,
) -> DeepResult:
    """run the full deep-research pipeline and return a cross-checked, scored result.

    the capability knobs:
      - retrieve: a grounding retriever -> sub-answers read real sources and cite them
      - parallel: answer independent sub-questions concurrently (on by default)
      - experience: an Experience store -> recall relevant past work, remember this run
      - verify: a claim verifier (e.g. grounded) -> fact-check the final answer
    """
    # compounding memory: let prior runs inform this one
    if experience is not None:
        prior = experience.recall_context(question)
        if prior and complete is not None:
            base_complete = complete

            def complete(prompt, **kw):  # noqa: A001 - wrap to inject recalled context
                return base_complete(f"{prior}\n\n{prompt}", **kw)

    if answer is None:
        if retrieve is not None and complete is not None:
            from agent.grounding import grounded_answer

            answer = grounded_answer(retrieve, complete, settings=settings)
        else:
            answer = _default_answer(complete, settings)
    if synthesize is None:
        if complete is not None:

            def synthesize(q: str, parts: dict[str, str]) -> str:
                joined = "\n\n".join(f"Q: {k}\nA: {v}" for k, v in parts.items())
                return complete(f"Combine these into one answer to '{q}':\n{joined}")

        else:

            def synthesize(q: str, parts: dict[str, str]) -> str:
                return " ".join(parts.values())

    plan = decompose(question, propose=propose, max_subs=max_subs, synthesize=False)
    subqs = [sq.text for sq in plan.subquestions]

    # one DAG node per sub-question, plus a synthesis node that depends on all of them
    nodes = [Node(key=f"s{i}", run=(lambda dq, q=q: answer(q))) for i, q in enumerate(subqs)]
    sub_keys = [n.key for n in nodes]
    nodes.append(
        Node(
            key="synthesis",
            deps=sub_keys,
            run=lambda deps: synthesize(question, {subqs[int(k[1:])]: deps[k] for k in deps}),
        )
    )

    dag_result = run_dag(nodes, parallel=parallel, workers=workers)
    sub_answers = {subqs[int(k[1:])]: v for k, v in dag_result.results.items() if k != "synthesis"}
    final = dag_result.results.get("synthesis", " ".join(sub_answers.values()))

    # cross-check across every answer produced
    all_text = [final, *sub_answers.values()]
    graph = KnowledgeGraph()
    for t in all_text:
        graph.ingest(t)
    contradictions = find_contradictions(list(sub_answers.values()))
    sources = extract_sources(" ".join(all_text))

    # optionally verify the final answer's claims against sources
    claims = []
    if verify is not None:
        from agent.factcheck import factcheck

        claims = factcheck(final, verify=verify)

    result = DeepResult(
        question=question,
        plan=plan,
        sub_answers=sub_answers,
        answer=final,
        contradictions=contradictions,
        sources=sources,
        graph=graph,
        claims=claims,
    )

    # remember this run so future questions benefit
    if experience is not None:
        experience.remember(question, final)
    return result
