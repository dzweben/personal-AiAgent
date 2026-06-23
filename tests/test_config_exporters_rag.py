import os

from agent.citations import bibliography, numbered
from agent.config import load_settings
from agent.exporters import available_formats, export
from agent.models import ResearchResponse
from agent.rag import VectorStore, simple_chunk


def test_settings_defaults():
    s = load_settings()
    assert s.provider in ("openai", "anthropic", "groq", "google")
    assert s.memory.enabled in (True, False)


def test_settings_overrides_win():
    s = load_settings(provider="anthropic", temperature=0.9)
    assert s.provider == "anthropic"
    assert s.temperature == 0.9


def test_export_formats(tmp_dir):
    r = ResearchResponse(
        topic="Tea", summary="good", sources=["https://x.test"], tools_used=["search"]
    )
    for fmt in ("json", "markdown", "txt", "html"):
        path = export(r, fmt=fmt, directory=tmp_dir)
        assert os.path.exists(path)
    assert "json" in available_formats()


def test_citations():
    out = numbered(["https://a.test", "Some Book"])
    assert "[1]" in out and "[2]" in out
    apa = bibliography(["https://a.test"], style="apa")
    assert "Retrieved" in apa


def test_chunking():
    chunks = simple_chunk("word " * 400, chunk_size=200, overlap=20)
    assert len(chunks) > 1


def test_vector_store_retrieval():
    vs = VectorStore(backend="memory")
    vs.add("Green tea has antioxidants good for the heart and brain.", {"source": "a"})
    vs.add("Paris is the capital of France.", {"source": "b"})
    hits = vs.search("heart health antioxidants", top_k=1)
    assert hits and "antioxidants" in hits[0]["text"]
