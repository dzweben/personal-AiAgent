"""load documents into a VectorStore.

handles plain text and markdown out of the box. pdf and docx are best effort and only kick
in if the relevant optional library is installed. point it at a file or a directory.
"""

from __future__ import annotations

from pathlib import Path

from agent.logging_utils import get_logger
from agent.rag.vectorstore import VectorStore

log = get_logger(__name__)

_TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".py", ".json", ".csv"}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        log.warning("pip install pypdf to ingest pdf files, skipping %s", path)
        return ""
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def load_file(store: VectorStore, path: str | Path) -> int:
    p = Path(path)
    if not p.exists() or not p.is_file():
        log.warning("not a file: %s", p)
        return 0
    if p.suffix.lower() in _TEXT_SUFFIXES:
        text = _read_text(p)
    elif p.suffix.lower() == ".pdf":
        text = _read_pdf(p)
    else:
        log.debug("unsupported file type %s, skipping", p.suffix)
        return 0
    if not text.strip():
        return 0
    return store.add(text, meta={"source": str(p), "name": p.name})


def load_directory(store: VectorStore, directory: str | Path, recursive: bool = True) -> int:
    d = Path(directory)
    if not d.is_dir():
        log.warning("not a directory: %s", d)
        return 0
    pattern = "**/*" if recursive else "*"
    total = 0
    for path in d.glob(pattern):
        if path.is_file():
            total += load_file(store, path)
    log.info("ingested %d chunks from %s", total, d)
    return total
