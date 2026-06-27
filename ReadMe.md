# AiAgent

This started as a weekend thing — a tiny Python script that asks an LLM a question, lets it
use a couple of tools, and prints a clean answer. I got bored and kept poking at it, and it
kind of got out of hand. It's now a little research-assistant framework, but the original idea
is the same: ask a question, it goes and uses real tools to answer it.

The original tiny version still works exactly the same — `python main.py` and
`from tools import search_tool` haven't changed. Everything else is layered on top and optional.

## What it does

- **Research agent** — give it a question, it uses tools (web search, Wikipedia, arXiv, a
  calculator, a sandboxed Python REPL, file read/write, and ~20 more) and returns a structured,
  cited answer. Works with OpenAI, Anthropic, Groq, Google, Mistral, Cohere, or a local model
  via Ollama.
- **A CLI** (`aiagent`) with subcommands for research, chat, listing tools, memory, exporting,
  and a bunch of experiments.
- **Memory, caching, RAG** — SQLite conversation memory, a small disk cache, and optional
  retrieval over your own docs.
- **The toolsmith** (`aiagent forge`) — the agent can write its own new tools at runtime, behind
  an AST sandbox so generated code can't touch the filesystem or network.
- **A scholarly writing arm** (`aiagent write-review`) — searches open academic indexes
  (OpenAlex, Semantic Scholar, Crossref, Europe PMC, arXiv), keeps only empirical studies and
  reviews, grades them by evidence strength, and writes a cited literature review *in APA style*
  — with a real APA writing-rules engine behind it, not just APA citations.
- A pile of more experimental stuff — a multi-step "council" that debates and fact-checks its
  own answers, deep-research that plans and cross-checks itself, a writing-rules linter. Fun to
  build, varying degrees of practical.

Fair warning: it's deliberately over-engineered. That was the point.

## Setup

```bash
git clone https://github.com/dzweben/personal-aiagent.git
cd personal-aiagent
python3 -m venv venv && source venv/bin/activate
pip install -e .

cp .env.example .env   # then add your API key(s)
```

## Using it

```bash
# the classic way still works
python main.py

# or the CLI
aiagent research "the history of the espresso machine"
aiagent chat                                  # interactive, remembers the conversation
aiagent tools                                 # list everything it can use
aiagent forge --name fahrenheit --desc "C to F" --expr "float(x) * 9/5 + 32"
aiagent write-review "caffeine and sleep" --style apa --out review.md
```

Config resolves in this order (later wins): defaults → `config.yaml` → `AIAGENT_*` env vars →
CLI flags. See `config.example.yaml`.

## Layout

```
main.py / tools.py     the original, still-working entry point
agent/                 the actual package (config, llm, tools, memory, cli, ...)
agent/scholar/         the academic writing arm (papers, citations, APA engine)
agent/style/           the writing-rules engine
tests/                 pytest suite (all offline — no API keys needed to run them)
```

## Dev

```bash
pip install -e ".[dev]"
pytest          # the whole suite
ruff check . && black .
```

Tests never call a real model or hit the network — anything LLM-shaped takes an injectable
function, so the suite is fast and free to run.

## A note on the LLM-writes-tools bit

`aiagent forge` runs code the model generated. It's sandboxed (allowlisted imports only, no
`os`/`sys`/`eval`/`open`/etc.), but it's still a toy — don't point it at untrusted input on a
machine you care about.

MIT licensed. Built mostly for fun.
