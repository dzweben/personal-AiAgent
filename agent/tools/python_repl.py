"""a small python repl tool with the dangerous bits taken out.

this is not a hardened sandbox and i would not expose it to the public internet, but for
a personal agent running on my own machine it is fine. i block the obvious nasties
(imports of os/sys/subprocess, dunder access, open, eval/exec) before running anything.
"""

from __future__ import annotations

import contextlib
import io
import math
import statistics

from langchain.tools import Tool

from agent.tools import register

_BLOCKLIST = (
    "import os",
    "import sys",
    "import subprocess",
    "import shutil",
    "import socket",
    "__import__",
    "__builtins__",
    "__globals__",
    "open(",
    "eval(",
    "exec(",
    "compile(",
    "input(",
    "os.system",
)

_SAFE_GLOBALS = {
    "math": math,
    "statistics": statistics,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "round": round,
    "sorted": sorted,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "print": print,
}


def run_python(code: str) -> str:
    code = code.strip().strip("`")
    if code.startswith("python"):
        code = code[len("python"):].lstrip()

    lowered = code.lower()
    for bad in _BLOCKLIST:
        if bad in lowered:
            return f"blocked: code contains {bad!r} which is not allowed in this sandbox"

    buf = io.StringIO()
    sandbox: dict = {"__builtins__": {}}
    sandbox.update(_SAFE_GLOBALS)
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, sandbox)  # noqa: S102 - intentional, guarded above
    except Exception as exc:  # noqa: BLE001
        return f"error: {type(exc).__name__}: {exc}\n{buf.getvalue()}"
    out = buf.getvalue().strip()
    return out if out else "(ran with no output, assign to a variable and print it to see results)"


@register("python_repl")
def make_python_repl():
    return Tool(
        name="python_repl",
        func=run_python,
        description=(
            "Run a short snippet of Python and get whatever it prints. math and statistics "
            "modules are preloaded. No file, network, or os access. Great for quick calculations "
            "and data wrangling. Remember to print() the thing you want to see."
        ),
    )
