# Contributing

Hey, thanks for even looking at this. It started as a bored weekend project and grew
some teeth, so contributions are very welcome but keep things chill.

## Getting set up

```bash
git clone https://github.com/dzweben/personal-aiagent.git
cd personal-aiagent
python3 -m venv venv
source venv/bin/activate
pip install -e ".[all]"
pre-commit install
```

## Before you open a PR

- run the tests: `pytest`
- lint and format: `ruff check .` then `black .`
- if you touched behaviour, add or update a test for it
- keep the casual, human tone in comments and docs, that is kind of the whole vibe

## Adding a tool

Tools live in `agent/tools/`. Each one is a small module that registers itself:

```python
from langchain_core.tools import Tool
from agent.tools import register

@register("my_tool")
def make_my_tool():
    return Tool(name="my_tool", func=..., description="...")
```

If your tool needs an optional dependency or an api key, register it defensively so the
agent just skips it when the thing is not available (look at `news.py` or `weather.py`).

## Adding a provider

Add a branch to `agent/llm.py:build_llm` and a default model in `default_model_for`.

## Reporting bugs

Use the issue templates. Logs and a repro are gold.
