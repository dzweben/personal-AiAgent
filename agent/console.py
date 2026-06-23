"""pretty terminal output helpers built on rich.

everything in here degrades to plain print() if rich is not installed, so the agent never
hard depends on it. the goal is just to make the cli feel nice.
"""

from __future__ import annotations

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table

    _console: Console | None = Console()
    _HAS_RICH = True
except ImportError:  # pragma: no cover
    _console = None
    _HAS_RICH = False


def console():
    return _console


def banner(text: str = "personal-aiagent") -> None:
    if _HAS_RICH and _console:
        _console.print(Panel.fit(f"[bold cyan]{text}[/bold cyan]", border_style="cyan"))
    else:
        print(f"=== {text} ===")


def info(msg: str) -> None:
    if _HAS_RICH and _console:
        _console.print(f"[dim]{msg}[/dim]")
    else:
        print(msg)


def success(msg: str) -> None:
    if _HAS_RICH and _console:
        _console.print(f"[bold green]{msg}[/bold green]")
    else:
        print(msg)


def warn(msg: str) -> None:
    if _HAS_RICH and _console:
        _console.print(f"[bold yellow]{msg}[/bold yellow]")
    else:
        print(msg)


def error(msg: str) -> None:
    if _HAS_RICH and _console:
        _console.print(f"[bold red]{msg}[/bold red]")
    else:
        print(msg)


def markdown(md: str) -> None:
    if _HAS_RICH and _console:
        _console.print(Markdown(md))
    else:
        print(md)


def print_response(result) -> None:
    """render an AgentResult nicely. falls back to a plain repr without rich."""
    structured = getattr(result, "structured", None)
    if structured is None:
        warn("could not parse a structured response, here is the raw output:")
        print(getattr(result, "output_text", str(result)))
        return

    if not (_HAS_RICH and _console):
        print(structured)
        return

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[bold]topic[/bold]", structured.topic)
    table.add_row("[bold]summary[/bold]", structured.summary)
    table.add_row("[bold]tools[/bold]", ", ".join(structured.tools_used) or "(none)")
    sources = "\n".join(f"- {s}" for s in structured.sources) or "(none)"
    table.add_row("[bold]sources[/bold]", sources)
    _console.print(Panel(table, title="research result", border_style="green"))


def tools_table(names: list[str]) -> None:
    if not (_HAS_RICH and _console):
        print("tools:", ", ".join(names))
        return
    table = Table(title="available tools")
    table.add_column("#", style="dim", width=3)
    table.add_column("tool", style="cyan")
    for i, name in enumerate(names, 1):
        table.add_row(str(i), name)
    _console.print(table)
