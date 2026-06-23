"""file tools: save research out, read files back in, list a directory.

the save_text_to_file tool keeps the exact same name and behaviour as the original so
the README example still works, i just moved the implementation in here.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from langchain.tools import Tool

from agent.tools import register

DEFAULT_OUTPUT = "research_output.txt"


def save_to_txt(data: str, filename: str = DEFAULT_OUTPUT) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output --- \nTimestamp: {timestamp}\n\n{data}\n\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(formatted_text)
    return f"saved {len(data)} characters to {filename}"


@register("save_text_to_file")
def make_save():
    return Tool(
        name="save_text_to_file",
        func=save_to_txt,
        description="Saves structured research data to a text file (appends with a timestamp).",
    )


def _read_file(path: str) -> str:
    p = Path(path.strip().strip('"').strip("'"))
    if not p.exists():
        return f"no file at {p}"
    if not p.is_file():
        return f"{p} is not a file"
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:8000]
    except Exception as exc:  # noqa: BLE001
        return f"could not read {p}: {exc}"


@register("read_file")
def make_read():
    return Tool(
        name="read_file",
        func=_read_file,
        description="Read a local text file and return its contents (first 8000 chars). Input is a path.",
    )


def _list_dir(path: str = ".") -> str:
    p = Path((path or ".").strip().strip('"').strip("'"))
    if not p.exists():
        return f"no such directory {p}"
    try:
        entries = sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir())
        return "\n".join(entries) if entries else "(empty)"
    except Exception as exc:  # noqa: BLE001
        return f"could not list {p}: {exc}"


@register("list_dir")
def make_list_dir():
    return Tool(
        name="list_dir",
        func=_list_dir,
        description="List the entries in a local directory. Input is a directory path, defaults to cwd.",
    )
