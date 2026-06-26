# AiAgent - a project for fun!

[![CI](https://github.com/dzweben/personal-aiagent/actions/workflows/ci.yml/badge.svg)](https://github.com/dzweben/personal-aiagent/actions/workflows/ci.yml)
[![CodeQL](https://github.com/dzweben/personal-aiagent/actions/workflows/codeql.yml/badge.svg)](https://github.com/dzweben/personal-aiagent/actions/workflows/codeql.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Built with LangChain](https://img.shields.io/badge/built%20with-LangChain-1c3c3c.svg)](https://www.langchain.com/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

This started as a **personal project** I built for fun to explore how to create a simple
AI-powered research assistant in Python. I got bored and did this for literally no reason.
Then I kept poking at it on and off, added a tool here, a feature there, and somewhere
along the way it turned into an actual little framework. Same heart, way more bells and
whistles.

The core idea is still the same: ask a question, the agent goes off and uses real tools
(web search, Wikipedia, arxiv, a calculator, a sandboxed Python REPL, and more) to dig up
an answer, then hands you back a clean structured result and can save it wherever you want.

> Heads up: the original tiny version still works exactly like it always did. `python main.py`
> and `from tools import search_tool` have not changed. Everything below is stuff layered on
> top, all optional.

---

## Table of contents

- [Features](#-features-that-i-used-to-build-a-lil-llm-cause-why-not)
- [The tool belt](#-the-tool-belt)
- [Quick start](#-quick-start)
- [The CLI](#-the-cli)
- [The HTTP API](#-the-http-api)
- [Configuration](#-configuration)
- [RAG over your own docs](#-rag-over-your-own-docs)
- [Project structure](#-project-structure)
- [Development](#-development)
- [Requirements](#-requirements)
- [Notes](#-notes)

---

## Features that I used to build a lil' LLM, cause why not!?

- Uses **LangChain** with:
  - `langchain-openai` -> access to OpenAI's GPT models.
  - `langchain-anthropic` -> access to Anthropic's models.
  - `langchain-community` -> DuckDuckGo + Wikipedia integrations.
  - optional `groq`, `google`, `mistral` and `cohere` providers, plus `ollama` for
    fully local models with no api key, since they were basically free to add.
- A **plugin loader**: drop a `.py` file in `plugins/` (or ship an `aiagent.tools`
  entry point) and your own tools join the belt automatically — see `plugins/example_tool.py`.
- A **Pydantic schema** enforces structured outputs (topic, summary, sources, tools used).
- A whole **tool belt** the agent can reach for (see below).
- **Conversation memory** backed by SQLite, so it can remember earlier turns in a chat.
- **Optional RAG**: drop in your own documents and let the agent search over them.
- **Optional FastAPI server** so you can hit the agent over HTTP.
- **Multi-format export**: save a result as markdown, json, html, txt, or pdf.
- **Citation helpers**: numbered reference lists and APA / MLA / plain bibliographies.
- A proper **`aiagent` CLI** built with Typer and Rich, so it actually looks nice.
- The full **GitHub treatment**: CI across Python 3.10-3.12, CodeQL, dependabot, issue and
  PR templates, pre-commit hooks, a Dockerfile, the works.
- Everything **degrades gracefully**. Missing an API key or an optional package? That tool
  just quietly sits out instead of blowing up the whole agent.

## The tool belt

| Tool | What it does | Needs |
| ---- | ------------ | ----- |
| `search` | web search via DuckDuckGo | nothing |
| `wikipedia` | quick Wikipedia lookups | nothing |
| `arxiv` | search academic papers on arxiv | nothing (falls back to raw http) |
| `calculator` | safe math, no raw `eval` | nothing |
| `python_repl` | run a snippet of Python, sandboxed | nothing |
| `datetime` | tell the model what day it actually is | nothing |
| `http_get` | fetch the raw contents of a URL | nothing |
| `fetch_url` | fetch a page and strip it to readable text | nothing |
| `read_file` | read a local text file | nothing |
| `save_text_to_file` | save results to a file (the original tool) | nothing |
| `list_dir` | list a local directory | nothing |
| `news` | recent headlines on a topic | `NEWSAPI_KEY` |
| `weather` | current weather for a city | `OPENWEATHER_API_KEY` |

## Quick start

```bash
# clone it
git clone https://github.com/dzweben/personal-aiagent.git
cd personal-aiagent

# the lazy one liner
./scripts/setup.sh

# or do it by hand
python3 -m venv venv
source venv/bin/activate          # mac/linux
# venv\Scripts\activate           # windows
pip install -e .                  # or: pip install -r requirements.txt

# add your keys
cp .env.example .env              # then edit .env

# run the classic flow
python3 main.py
```

Example interaction:

```
What can I help you research? The health benefits of drinking green tea
```

Output (printed nicely to the console, and optionally saved):

```json
{
  "topic": "Green Tea Health Benefits",
  "summary": "Green tea is rich in antioxidants and may reduce the risk of heart disease, improve brain function, and support weight loss.",
  "sources": [
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6520897/",
    "https://www.healthline.com/nutrition/top-10-evidence-based-health-benefits-of-green-tea"
  ],
  "tools_used": ["search", "wikipedia", "save_text_to_file"]
}
```

## The CLI

Once it is installed you get an `aiagent` command with proper subcommands:

```bash
aiagent research "the history of the espresso machine" --export markdown
aiagent research "quantum error correction" --provider anthropic --detailed
aiagent chat --session espresso        # interactive, remembers the conversation
aiagent tools                          # list every loadable tool
aiagent config                         # show the resolved settings
aiagent memory show                    # peek at conversation history

# the unhinged one: grow the agent a brand new tool at runtime
aiagent forge --name fahrenheit --desc "celsius to fahrenheit" --expr "float(x) * 9/5 + 32"
aiagent tools                          # ...and fahrenheit is now in the belt
```

## The toolsmith (the agent writes its own tools)

`aiagent forge` takes a name, a description, and a one-line python expression (`x` is the
input), generates a real plugin module, runs it through an AST sandbox, writes it into the
plugin dir, and hot-loads it — so the new tool is live immediately, no restart.

The sandbox is deliberately paranoid: generated code may only import from a tiny allowlist
(`math`, `random`, `datetime`, `json`, `re`, `statistics`, `textwrap`, `string`) and may not
touch `os` / `sys` / `subprocess` / sockets, call `eval` / `exec` / `open` / `__import__`, or
poke at dunder attributes. Anything outside that raises `SafetyError` *before* a single line
is written to disk or imported. It is still a toy — don't point it at hostile input — but it
is a toy with a seatbelt. See `agent/forge.py`.

## The council (everything, chained)

The capstone. `aiagent council "<question>"` runs one question through the whole cabinet as a
single pipeline:

```
route → ensemble (several personas answer) → fact-check the merged draft
      → constitutional critique + rewrite → adversarial red-team → score it
```

Every move is recorded so the run is inspectable (`--show-run`) and the final answer comes back
graded, fact-checked, and hardened. Under the hood it chains a set of small, individually useful
building blocks — all offline-testable via injectable callables:

| Module | Command | What it adds |
|---|---|---|
| `router` | `aiagent route` | picks the mode that fits a query (debate / swarm / research / …) |
| `ensemble` | — | several personas answer, reconciled by a consensus vote |
| `factcheck` | — | extracts claims and verifies each one |
| `critique` | — | constitutional self-critique + rewrite loop |
| `redteam` | — | an adversarial battery that tries to break the answer |
| `scorecard` | `aiagent score` | an offline answer-quality heuristic |
| `summarize` | — | map-reduce summariser for oversized context |
| `budget` | — | a cost ceiling so a chained run can't run away |
| `replay` | — | records the whole run (and can pack it into a capsule) |
| `pipeline` | — | the composable Context + Step backbone they all ride on |

```bash
aiagent council "should we migrate to kubernetes?" --show-run
```

## The scholarly research-writing arm

A specialised arm for writing actual research, grounded **only in real academic literature**.
`aiagent write-review "<topic>"` searches open scholarly indexes (OpenAlex, Semantic Scholar,
Crossref, Europe PMC, arXiv), keeps **only empirical studies and literature reviews**, grades
each paper by evidence strength, synthesises the body by theme, and drafts a fully-cited
document with a real reference list — so every `(Author, Year)` traces back to a paper it
actually retrieved, not a hallucination.

```bash
aiagent scholar-search "caffeine and sleep quality"     # ranked, evidence-graded reading list
aiagent write-review "caffeine and sleep" --style apa --out review.md
```

> Note: Google Scholar has no open API and forbids scraping, so the arm uses the open indexes
> that cover the same literature — same papers, legitimately accessible. Citation styles: APA,
> MLA, Chicago, Vancouver, BibTeX. It adds **no new dependencies**.

### Writing *in* APA style (not just APA citations)

The point isn't the reference list — it's the prose. The arm ships an **APA 7th-edition writing
engine** (`agent/scholar/apa.py`) that encodes APA's actual writing standards from the
Publication Manual (ch. 4–5): continuity and flow, conciseness, clarity, verb-tense logic,
active voice, first person, **bias-free language**, and hedging of claims. Every section is
drafted under that style prompt and then **self-corrected** — mechanical fixes first (wordiness,
biased/dated terms like "the elderly" → "older adults", "subjects" → "participants"), then a
model rewrite for tense/voice/overclaiming. You can lint any text directly:

```bash
aiagent apa-check "The study proves the elderly subjects didn't improve." --fix
# → flags: overclaiming ("proves"), bias ("the elderly", "subjects"), contraction ("didn't")
```

## Deep research (the autonomous brain)

`aiagent deep-research "<big question>"` is the capability capstone. It plans the question into
a sub-question DAG, answers each one (dependencies first, via the council), synthesises an
overall answer, then **cross-checks itself**: it builds a knowledge graph from the answers,
flags contradictions between sub-answers, ranks the sources by domain authority, scores a
confidence, and writes a full markdown report.

```bash
aiagent deep-research "How does caffeine affect sleep, what's a safe dose, and should I quit?" \
  --grounded --verify --remember --report caffeine.md
```

`--grounded` reads the **live web** and cites real urls, `--verify` fact-checks the answer
against those sources (not the model's memory), `--remember` makes runs **compound** over time,
and independent sub-questions are answered **in parallel** by default.

The primitives it chains are each their own small, offline-testable module: `planner` (DAG
decomposition), `dag` (topological executor with cycle detection), `sources`, `consistency`
(self-consistency sampling), `contradiction`, `knowledge` (entity/relation graph), `argmap`,
and `reflect` (a lessons memory that learns across runs).

## The chaos cabinet

A drawer of deliberately over-the-top experiments. Each is its own small module with an
offline, deterministic core (the LLM-backed ones take an injectable callable, so the test
suite never needs a key):

```bash
aiagent forge --name slugify --desc "make text url-safe" --llm   # the model writes the tool
aiagent debate "is remote work better?" --rounds 3               # two stances argue, mod synthesises
aiagent swarm "should we rewrite it in rust?" --rounds 2         # a society of role agents
aiagent evolve --generations 20                                  # genetic algorithm breeds a prompt
aiagent dream                                                    # free-associate over your memory
aiagent oracle "why is my model overfitting?"                    # oblique-strategy reframes
aiagent capsule result.json                                      # pack a result into a portable blob
aiagent mcp --list                                               # expose the tool belt over MCP
```

Plus two library-only toys: `agent.critique.refine()` (a constitutional self-critique loop
that grades and rewrites an answer) and `agent.timetravel.TimeTravel` (git-backed conversation
snapshots you can branch into alternate timelines and diff). Install the optional bits with
`pip install 'personal-aiagent[chaos]'`.

## The HTTP API

```bash
python -m agent.server
# docs at http://localhost:8000/docs

curl -X POST localhost:8000/research \
  -H "content-type: application/json" \
  -d '{"query": "what is retrieval augmented generation", "detailed": true}'
```

Or with Docker:

```bash
docker compose up
```

## Configuration

Settings resolve in this order, later wins:

1. the defaults baked into the code
2. `config.yaml` (copy from `config.example.yaml`)
3. environment variables prefixed `AIAGENT_` (and `.env`)
4. command line flags

So `AIAGENT_PROVIDER=anthropic aiagent research "..."` works, and so does
`aiagent research "..." --provider anthropic`. See `config.example.yaml` for everything you
can tweak.

## RAG over your own docs

```python
from agent.rag import VectorStore
from agent.rag.ingest import load_directory

store = VectorStore(backend="chroma", collection="my_notes")
load_directory(store, "./notes")
print(store.as_context("what did i write about sleep", top_k=4))
```

If you have not installed the RAG extras, it transparently falls back to a small pure
Python vector store so the flow still works for a quick demo.

## Project structure

```
personal-aiagent/
├── main.py                 # classic entry point (still works exactly like before)
├── tools.py                # backwards compatible shim for the original tools
├── agent/                  # the actual package
│   ├── config.py           # settings (defaults -> yaml -> env -> flags)
│   ├── models.py           # pydantic schemas, including the original ResearchResponse
│   ├── llm.py              # provider factory (openai/anthropic/groq/google/ollama/mistral/cohere)
│   ├── plugins.py          # discovers third-party tools from plugins/ + entry points
│   ├── forge.py            # the toolsmith: agent writes + hot-loads its own sandboxed tools
│   ├── debate.py           # dialectic mode: two stances argue, a moderator synthesises
│   ├── swarm.py            # a blackboard society of role-playing agents
│   ├── evolve.py           # genetic algorithm that breeds a better system prompt
│   ├── critique.py         # constitutional self-critique + rewrite loop
│   ├── dream.py            # free-association over memory into surreal prompts
│   ├── oracle.py           # oblique-strategy cards to reframe a question
│   ├── trace.py            # ascii "thought tree" of the agent's tool calls
│   ├── timetravel.py       # git-backed conversation snapshots + alternate timelines
│   ├── capsule.py          # portable gzip+base64 result capsules (optional qr)
│   ├── mcp_server.py       # expose the tool belt over the Model Context Protocol
│   ├── prompts.py          # system prompts
│   ├── agent.py            # the ResearchAgent orchestrator
│   ├── memory.py           # sqlite conversation memory
│   ├── cache.py            # small ttl disk cache
│   ├── exporters.py        # md / json / html / txt / pdf export
│   ├── citations.py        # numbered refs + bibliographies
│   ├── council.py          # the capstone: chains everything into one graded answer
│   ├── pipeline.py         # composable Context + Step backbone
│   ├── router.py           # heuristic query → mode classifier
│   ├── ensemble.py         # multi-persona answers + consensus vote
│   ├── factcheck.py        # claim extraction + verification
│   ├── redteam.py          # adversarial self-attack on an answer
│   ├── scorecard.py        # offline answer-quality heuristic
│   ├── summarize.py        # map-reduce summariser
│   ├── budget.py           # cost ceiling guard
│   ├── replay.py           # run recorder (capsule-packable)
│   ├── deepresearch.py     # autonomous capstone: plan → execute → cross-check → report
│   ├── grounding.py        # live web: search → fetch → extract → cite real sources
│   ├── parallel.py         # order-preserving concurrent map (fan-out speed)
│   ├── semantic_memory.py  # embeddings + meaning-based recall across sessions
│   ├── experience.py       # lessons + memory that compound run over run
│   ├── planner.py          # decompose a question into a sub-question DAG
│   ├── dag.py              # dependency-aware task-graph executor
│   ├── sources.py          # citation extraction, dedup, authority ranking
│   ├── consistency.py      # self-consistency sampling + clustering
│   ├── contradiction.py    # find conflicting claims across answers
│   ├── knowledge.py        # entity/relation graph with path queries
│   ├── argmap.py           # structure a debate into support/attack edges
│   ├── reflect.py          # lessons memory that learns across runs
│   ├── console.py          # rich pretty printing
│   ├── cli.py              # the typer cli
│   ├── tools/              # the tool belt, one module per tool
│   ├── rag/                # optional vector store + ingestion
│   └── server/             # optional fastapi app
├── tests/                  # pytest suite
├── docs/                   # architecture + usage notes
├── .github/                # ci, codeql, templates, dependabot
├── Dockerfile / compose    # containerized runs
├── Makefile                # handy shortcuts (make help)
├── requirements.txt        # core deps
└── pyproject.toml          # packaging + extras + tooling config
```

## Development

```bash
pip install -e ".[all]"
pre-commit install

make test        # run the suite
make lint        # ruff
make fmt         # black + ruff --fix
make check       # lint + typecheck + test
make help        # see everything
```

The tests are all offline, they never call a real model or hit the network, so they are
fast and need no API keys.

## Requirements

Core (see `requirements.txt`):

- langchain, langchain-core, langchain-community, langchain-openai, langchain-anthropic
- wikipedia, ddgs, httpx
- pydantic, pydantic-settings, python-dotenv, pyyaml
- rich, typer, tenacity

Optional extras (install with `pip install -e ".[rag,server,export,tools,dev]"`):

- **rag**: chromadb, faiss-cpu, sentence-transformers, tiktoken
- **server**: fastapi, uvicorn, sse-starlette
- **export**: markdown, reportlab, weasyprint, jinja2
- **tools**: arxiv, wolframalpha, numexpr, pandas, matplotlib
- **dev**: pytest, ruff, black, mypy, pre-commit

## Notes

- This is still, at its heart, a **sandbox project** to play with AI agent design. I guess
  this is what I do when I get bored. It just got a lot more ambitious.
- Virtual environments are intentionally ignored (`venv/` in `.gitignore`).
- The output file appends new research queries with timestamps.
- The `python_repl` tool is sandboxed with a blocklist, not a real jail, so do not point
  this at untrusted input on a machine you care about. See `SECURITY.md`.
- Original boring example, kept for nostalgia: "The health benefits of drinking green tea"
  (sorry, I was burnt out of this project by the time I got there the first time!).
