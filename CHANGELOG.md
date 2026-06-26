# Changelog

All notable changes to this project get jotted down here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/), and the project tries to stick to
semantic versioning.

## [Unreleased]

### Added
- a **scholarly research-writing arm** (`agent/scholar/`, `aiagent write-review` /
  `aiagent scholar-search`) that writes from real academic literature, not the model's memory.
  It searches open scholarly indexes (OpenAlex, Semantic Scholar, Crossref, Europe PMC, arXiv),
  keeps only **empirical studies and reviews**, grades each by evidence strength, synthesises the
  body by theme, and drafts a fully-cited document with a real reference list. Pieces:
  - `paper` — one normalised record every index maps onto, with dedup + citation labels
  - `sources` — connectors to five open indexes (injectable fetch; offline-testable)
  - `classify` — empirical vs review, study-design detection, sample-size extraction
  - `quality` — GRADE-style evidence scoring (design × sample × recency × citations)
  - `citations` — APA / MLA / Chicago / Vancouver / BibTeX, in-text + reference lists
  - `corpus` — a persistent, semantically-searchable paper library
  - `synthesis` — themes, consensus vs contradiction, timeline, research gaps
  - `writing` — outlines + grounded section drafting that can't invent references
  - `arm` — the `ResearchWriter` capstone: topic → graded, themed, cited review
  - no new dependencies (it reuses the existing httpx + semantic memory)
- **grounding in reality** — the deep-research brain can now actually go read the web and
  back its answers with real sources, and it runs far faster and learns over time:
  - `grounding` — search → fetch pages (in parallel) → extract → rank passages → cite urls;
    `grounded_answer` makes the agent answer strictly from retrieved sources
  - `parallel` + parallel DAG execution — independent sub-questions are answered concurrently
    (a 4-way fan-out drops from ~4 units of wait to ~1)
  - `semantic_memory` — dependency-free embeddings with persistent, meaning-based recall
  - `experience` — lessons + semantic memory compound across runs, recalled into new prompts
  - grounded `factcheck` — verify claims against *retrieved sources*, not the model's memory
  - `deep-research` gained `--grounded`, `--verify`, `--remember`, and `--no-parallel`
- a **deep-research brain** built on top of the council (`aiagent deep-research`): an autonomous
  pipeline that plans a question into a sub-question DAG, answers each (dependencies first),
  synthesises an overall answer, then cross-checks it — building a knowledge graph, flagging
  contradictions, and ranking sources — before scoring confidence and writing a markdown report.
  The reasoning primitives it chains, each its own offline-testable module:
  - `planner` — decompose a question into a sub-question DAG
  - `dag` — a dependency-aware task-graph executor with cycle detection
  - `sources` — extract, dedupe, and rank citations by domain authority
  - `consistency` — self-consistency sampling with answer clustering
  - `contradiction` — find conflicting claims across answers
  - `knowledge` — build a queryable entity/relation graph from answers
  - `argmap` — structure a debate into support/attack edges
  - `reflect` — a lessons memory that learns across runs

### Changed
- a big hardening pass over every reasoning idea, each taken closer to its max:
  - **council** now *self-corrects in a loop* (`--target`/`--max-iter`), feeding red-team
    weaknesses and unsupported claims back into the reviser; reports an aggregate **confidence**
    (quality × credibility × robustness); and exports a markdown `--report` or a `--capsule`
  - **council `--evolve`** tunes the persona line-up with a genetic search against the scorecard
  - **toolsmith** now forges multi-statement bodies and can `list`/`remove` forged tools safely
  - **scorecard** gained specificity + structure axes, tunable weights, and `compare()`
  - **router** scores every mode and reports a confidence + runner-up
  - **ensemble** added `best` (scorecard) and `longest` merge strategies
  - **factcheck** added claim importance, dedup, and an importance-weighted credibility score
  - **redteam** added attack categories, severities, and a weighted robustness score
  - **debate** went N-party with early-stop convergence detection
  - **swarm** folds the blackboard into a final lead synthesis
  - **evolve** got pluggable operators, diversity preservation, and an eval-harness fitness hook

### Added
- the **council** (`agent/council.py` + `aiagent council`): one chained pipeline that routes a
  question, gathers a multi-persona ensemble answer, fact-checks the claims, runs a
  constitutional critique + rewrite, red-teams the result, and scores it — recording every move
- the reasoning building blocks the council chains together, each its own module + cli where it
  fits and each testable offline via injectable callables:
  - `pipeline`: a composable Context + Step backbone
  - `router` (`aiagent route`): heuristic query → mode classifier
  - `scorecard` (`aiagent score`): offline answer-quality heuristic
  - `summarize`: map-reduce summariser for oversized context
  - `ensemble`: multi-persona answers reconciled by a consensus vote
  - `factcheck`: claim extraction + per-claim verification
  - `redteam`: an adversarial battery that tries to break an answer
  - `budget`: a cost ceiling guard across a chained run
  - `replay`: a run recorder that serialises (and capsule-packs) a whole run
- a whole **chaos cabinet** of experimental modules + cli commands:
  - `forge --llm`: the model writes the tool's body from plain-english intent (still sandboxed)
  - `debate`: two stances argue a question, a moderator synthesises
  - `swarm`: a blackboard "society of agents" with roles collaborating over rounds
  - `evolve`: a genetic algorithm that breeds a better system prompt (offline fitness)
  - `dream`: free-associates over conversation memory into surreal research prompts
  - `oracle`: oblique-strategy cards that reframe a stuck question
  - `critique`: a constitutional self-critique loop that grades and rewrites an answer
  - `trace`: renders the agent's tool calls as an ascii "thought tree"
  - `timetravel`: git-backed conversation snapshots with branchable alternate timelines
  - `capsule`: pack a result into a portable gzip+base64 string (optional qr)
  - `mcp`: expose the whole tool belt over the Model Context Protocol for other agents
- the **toolsmith** (`agent/forge.py` + `aiagent forge`): the agent writes, sandbox-checks,
  and hot-loads brand new tools for itself at runtime. an ast validator refuses anything
  outside a tiny allowlist (no os/sys/subprocess/eval/exec/open/dunders) before a line is
  written or imported, so generated code can't escape the box
- three more llm providers: ollama (local, no api key), mistral, and cohere
- a plugin loader: drop `.py` files in `plugins/` (or ship `aiagent.tools` entry
  points) to register extra tools without touching the package
- richer session admin in memory + cli: `stats`, `rename`, and `delete`
- proper `agent` package: config, logging, memory, cache, prompts, llm factory
- a real tool belt: search, wikipedia, arxiv, calculator, sandboxed python repl,
  datetime, http_get, fetch_url, file read/write/list, news, weather
- `aiagent` cli (typer + rich) with research, chat, tools, memory, config commands
- conversation memory backed by sqlite
- optional RAG: vector store with a chroma backend and a zero-dependency fallback
- optional FastAPI server exposing the agent over REST
- multi-format export: markdown, json, html, txt, pdf
- citation helpers (numbered lists, apa / mla / plain bibliographies)
- pytest suite, ruff + black + mypy config, pre-commit hooks
- Dockerfile, docker-compose, Makefile
- the full github treatment: CI matrix, CodeQL, release workflow, issue/PR templates,
  dependabot, code of conduct, security policy, contributing guide

### Changed
- `main.py` and `tools.py` now sit on top of the package but stay backwards compatible,
  so `python main.py` and `from tools import search_tool` both still work
- pinned langchain to the 0.3 line so the classic agent api keeps working

## [0.1.0] - 2025

### Added
- the original: a single langchain research agent with duckduckgo, wikipedia, and a
  save-to-file tool, plus a pydantic structured output. built for fun on a bored weekend.
