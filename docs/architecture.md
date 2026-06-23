# Architecture

A quick tour of how the pieces fit together, for future me and anyone curious.

## The big picture

```
                 +------------------+
   you  ---->    |  main.py / cli   |   <-- entry points
                 +--------+---------+
                          |
                          v
                 +------------------+
                 |  ResearchAgent   |   agent/agent.py
                 |  (orchestrator)  |
                 +--+----+-----+----+
                    |    |     |
        +-----------+    |     +-------------+
        v                v                   v
   +---------+     +-----------+       +-----------+
   |  LLM    |     |  Tools    |       |  Memory   |
   | factory |     |  registry |       |  (sqlite) |
   +---------+     +-----------+       +-----------+
        |                |
        v                v
  openai/anthropic   search, wiki, arxiv,
  groq/google        calculator, python repl,
                     files, http, news, weather
```

## Modules

| Module | What it does |
| ------ | ------------ |
| `agent/config.py` | resolves settings from defaults, yaml, env, and overrides |
| `agent/models.py` | the pydantic schemas, including the original `ResearchResponse` |
| `agent/llm.py` | builds the right chat model for the chosen provider |
| `agent/prompts.py` | the system prompts (original one kept verbatim) |
| `agent/tools/` | the tool belt, each tool self registers via `@register` |
| `agent/agent.py` | wires llm + tools + prompt + parser into an executor |
| `agent/memory.py` | rolling conversation history in sqlite |
| `agent/cache.py` | small ttl disk cache |
| `agent/exporters.py` | save results as md / json / html / txt / pdf |
| `agent/citations.py` | numbered lists and bibliographies |
| `agent/rag/` | optional vector store + ingestion |
| `agent/server/` | optional fastapi app |
| `agent/cli.py` | the typer cli |
| `agent/console.py` | rich powered pretty printing |

## Design choices worth noting

- **everything optional degrades gracefully.** if a dependency or api key is missing, the
  relevant tool just does not register, instead of crashing the whole agent. that is the
  single most important rule in this codebase.
- **the original behaviour is preserved.** `python main.py` and
  `from tools import search_tool` both still work exactly like the first version.
- **lazy imports everywhere.** importing the package should be fast, so heavy stuff
  (langchain, fastapi, chromadb) is imported inside functions, not at module top.
