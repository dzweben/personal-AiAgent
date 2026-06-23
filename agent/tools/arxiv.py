"""arxiv search, for when duckduckgo and wikipedia are too pop-science.

uses the langchain community arxiv wrapper if its deps are installed, otherwise it talks
to the arxiv export api directly over http so it still works on a minimal install.
"""

from __future__ import annotations

from langchain.tools import Tool

from agent.tools import register


def _arxiv_http(query: str) -> str:
    import re
    import xml.etree.ElementTree as ET

    import httpx

    params = {"search_query": f"all:{query}", "start": 0, "max_results": 3}
    try:
        resp = httpx.get("http://export.arxiv.org/api/query", params=params, timeout=20)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return f"arxiv request failed: {exc}"

    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        return f"could not parse arxiv response: {exc}"

    out = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
        link = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
        summary = re.sub(r"\s+", " ", summary)[:400]
        out.append(f"{title}\n{link}\n{summary}")
    return "\n\n".join(out) if out else "no arxiv results"


@register("arxiv")
def make_arxiv():
    try:
        from langchain_community.tools import ArxivQueryRun
        from langchain_community.utilities import ArxivAPIWrapper

        wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=1500)
        return ArxivQueryRun(api_wrapper=wrapper)
    except Exception:
        # fall back to the raw http version, which needs nothing but httpx
        return Tool(
            name="arxiv",
            func=_arxiv_http,
            description="Search arxiv.org for academic papers. Input is a search query.",
        )
