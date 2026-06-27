# AiAgent

[![CI](https://github.com/dzweben/personal-aiagent/actions/workflows/ci.yml/badge.svg)](https://github.com/dzweben/personal-aiagent/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Built with LangChain](https://img.shields.io/badge/built%20with-LangChain-1c3c3c.svg)](https://www.langchain.com/)

A little research assistant I built for fun. You ask it a question, it goes off and uses real
tools — web search, Wikipedia, arXiv, a calculator, a Python sandbox, and a bunch more — to dig
up an answer and hand it back clean.

It started as a tiny weekend script and I kept poking at it for no real reason, so now it's…
a lot more than that. But the original `python main.py` still works exactly like it did on day one.

## The fun stuff it can do

- Answer questions using ~20 tools, with whatever model you like (OpenAI, Anthropic, Groq,
  Google, Mistral, Cohere, or a local one via Ollama).
- A proper `aiagent` CLI — research, chat, memory, exporting, the works.
- Remember conversations (SQLite), cache results, and do RAG over your own docs.
- **Forge its own tools** at runtime (`aiagent forge`) — the agent writes a new tool as code,
  behind a sandbox so it can't touch your files or network.
- **Write literature reviews** (`aiagent write-review`) from real academic papers (OpenAlex,
  Semantic Scholar, arXiv, etc.), in proper APA style — there's a whole APA writing-rules engine
  behind it, not just APA citations.

It's over-engineered on purpose. That was the whole point.

## Get it running

```bash
git clone https://github.com/dzweben/personal-aiagent.git
cd personal-aiagent
python3 -m venv venv && source venv/bin/activate
pip install -e .
cp .env.example .env   # drop in your API key(s)
```

## Play with it

```bash
python main.py                                       # the original, still works

aiagent research "the history of the espresso machine"
aiagent chat                                         # interactive, remembers the convo
aiagent tools                                        # everything it can use
aiagent forge --name fahrenheit --desc "C to F" --expr "float(x) * 9/5 + 32"
aiagent write-review "caffeine and sleep" --style apa --out review.md
```

Config goes: defaults → `config.yaml` → `AIAGENT_*` env vars → CLI flags (later wins).

## Where things live

```
main.py / tools.py     the original, still-working entry point
agent/                 the actual package (config, llm, tools, memory, cli, ...)
agent/scholar/         the academic writing arm (papers, citations, APA engine)
agent/style/           the writing-rules engine
tests/                 pytest suite — all offline, no API keys needed to run it
```

## Hacking on it

```bash
pip install -e ".[dev]"
pytest
ruff check . && black .
```

The tests never call a real model or hit the network (anything LLM-ish takes a fake function),
so they're fast and free to run.

Heads up: `aiagent forge` runs code the model wrote. It's sandboxed, but it's still a toy —
don't point it at sketchy input on a machine you care about.

MIT licensed. Built for fun. 🤖
