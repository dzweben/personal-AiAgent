# Changelog

All notable changes to this project get jotted down here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/), and the project tries to stick to
semantic versioning.

## [Unreleased]

### Added
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
