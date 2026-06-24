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
```

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
│   ├── prompts.py          # system prompts
│   ├── agent.py            # the ResearchAgent orchestrator
│   ├── memory.py           # sqlite conversation memory
│   ├── cache.py            # small ttl disk cache
│   ├── exporters.py        # md / json / html / txt / pdf export
│   ├── citations.py        # numbered refs + bibliographies
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
