"""export a research result to disk in a few formats.

txt and json and markdown and html need nothing beyond the stdlib. pdf is best effort and
only works if reportlab is installed, otherwise it tells you to pip install it.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agent.models import ResearchResponse


def _as_dict(result: Any) -> dict:
    """accept an AgentResult, a ResearchResponse, or a plain dict and normalise it."""
    structured = getattr(result, "structured", None)
    if structured is not None:
        return structured.model_dump()
    if isinstance(result, ResearchResponse):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return {
        "topic": "unknown",
        "summary": getattr(result, "output_text", str(result)),
        "sources": [],
        "tools_used": [],
    }


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _ensure_dir(directory: str) -> Path:
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    return d


def to_json(result: Any, directory: str = "exports") -> str:
    d = _ensure_dir(directory)
    path = d / f"research-{_stamp()}.json"
    path.write_text(json.dumps(_as_dict(result), indent=2, default=str), encoding="utf-8")
    return str(path)


def to_markdown(result: Any, directory: str = "exports") -> str:
    data = _as_dict(result)
    d = _ensure_dir(directory)
    path = d / f"research-{_stamp()}.md"
    lines = [
        f"# {data.get('topic', 'Research')}",
        "",
        data.get("summary", ""),
        "",
        "## Sources",
    ]
    sources = data.get("sources") or []
    lines += [f"- {s}" for s in sources] or ["- (none)"]
    lines += ["", "## Tools used", ", ".join(data.get("tools_used") or []) or "(none)", ""]
    lines += [f"_generated {datetime.now():%Y-%m-%d %H:%M:%S}_"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def to_txt(result: Any, directory: str = "exports") -> str:
    data = _as_dict(result)
    d = _ensure_dir(directory)
    path = d / f"research-{_stamp()}.txt"
    body = (
        f"Topic: {data.get('topic','')}\n\n"
        f"{data.get('summary','')}\n\n"
        f"Sources:\n" + "\n".join(f"  - {s}" for s in (data.get('sources') or [])) + "\n\n"
        f"Tools: {', '.join(data.get('tools_used') or [])}\n"
    )
    path.write_text(body, encoding="utf-8")
    return str(path)


def to_html(result: Any, directory: str = "exports") -> str:
    data = _as_dict(result)
    d = _ensure_dir(directory)
    path = d / f"research-{_stamp()}.html"
    sources = "".join(f"<li>{s}</li>" for s in (data.get("sources") or [])) or "<li>(none)</li>"
    html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{data.get('topic','Research')}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:3rem auto;padding:0 1rem;line-height:1.6}}
h1{{color:#0b6}}code{{background:#f3f3f3;padding:.1rem .3rem;border-radius:4px}}</style></head>
<body>
<h1>{data.get('topic','Research')}</h1>
<p>{data.get('summary','')}</p>
<h2>Sources</h2><ul>{sources}</ul>
<h2>Tools used</h2><p>{', '.join(data.get('tools_used') or []) or '(none)'}</p>
<hr><small>generated {datetime.now():%Y-%m-%d %H:%M:%S} by personal-aiagent</small>
</body></html>"""
    path.write_text(html, encoding="utf-8")
    return str(path)


def to_pdf(result: Any, directory: str = "exports") -> str:
    data = _as_dict(result)
    d = _ensure_dir(directory)
    path = d / f"research-{_stamp()}.pdf"
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pip install reportlab to export pdf") from exc

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    flow = [
        Paragraph(data.get("topic", "Research"), styles["Title"]),
        Spacer(1, 12),
        Paragraph(data.get("summary", ""), styles["BodyText"]),
        Spacer(1, 12),
        Paragraph("Sources", styles["Heading2"]),
        ListFlowable(
            [ListItem(Paragraph(str(s), styles["BodyText"])) for s in (data.get("sources") or [])]
            or [ListItem(Paragraph("(none)", styles["BodyText"]))],
            bulletType="bullet",
        ),
    ]
    doc.build(flow)
    return str(path)


_EXPORTERS = {
    "json": to_json,
    "markdown": to_markdown,
    "md": to_markdown,
    "txt": to_txt,
    "text": to_txt,
    "html": to_html,
    "pdf": to_pdf,
}


def export(result: Any, fmt: str = "markdown", directory: str = "exports") -> str:
    fn = _EXPORTERS.get(fmt.lower())
    if fn is None:
        raise ValueError(f"unknown export format {fmt!r}. try: {', '.join(sorted(_EXPORTERS))}")
    return fn(result, directory=directory)


def available_formats() -> list[str]:
    return sorted(_EXPORTERS.keys())
