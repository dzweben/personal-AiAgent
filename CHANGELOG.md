# Changelog

All notable changes to this project get jotted down here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/), and the project tries to stick to
semantic versioning.

## [Unreleased]

### Added
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
