# Usage

## The classic way

```bash
python main.py
# What can I help you research? the health benefits of green tea
```

## The cli

After `pip install -e .` you get an `aiagent` command.

```bash
# one shot research, with an export
aiagent research "the history of the espresso machine" --export markdown

# pick a provider and model on the fly
aiagent research "quantum error correction" --provider anthropic --model claude-3-5-sonnet-latest --detailed

# interactive chat with memory
aiagent chat --session espresso

# see what tools are loadable right now
aiagent tools

# inspect resolved config
aiagent config

# look at or wipe conversation memory
aiagent memory show
aiagent memory clear --session espresso
```

## The http api

```bash
python -m agent.server
# then in another terminal:
curl -X POST localhost:8000/research -H "content-type: application/json" \
  -d '{"query": "what is retrieval augmented generation", "detailed": true}'
```

Interactive docs live at `http://localhost:8000/docs`.

## RAG over your own docs

```python
from agent.rag import VectorStore
from agent.rag.ingest import load_directory

store = VectorStore(backend="chroma", collection="my_notes")
load_directory(store, "./notes")
print(store.as_context("what did i write about sleep", top_k=4))
```

## Configuration

Settings resolve in this order (later wins): built in defaults, then `config.yaml`, then
environment variables prefixed `AIAGENT_`, then anything you pass on the command line.

Copy `config.example.yaml` to `config.yaml` and `.env.example` to `.env` to get started.
