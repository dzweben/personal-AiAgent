"""translation via the mymemory free api. no key, rate limited but fine for casual use."""

from __future__ import annotations

from langchain_core.tools import Tool

from agent.tools import register


def _translate(spec: str) -> str:
    """expects 'TEXT | from:to', e.g. 'hello world | en:es'. defaults to en:es."""
    import httpx

    if "|" in spec:
        text, _, langs = spec.rpartition("|")
        pair = langs.strip()
    else:
        text, pair = spec, "en:es"
    text = text.strip()
    if ":" not in pair:
        pair = "en:es"
    src, _, dst = pair.partition(":")
    try:
        resp = httpx.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{src.strip()}|{dst.strip()}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return f"translation failed: {exc}"
    translated = data.get("responseData", {}).get("translatedText")
    return translated or "no translation came back"


@register("translate")
def make_translate():
    return Tool(
        name="translate",
        func=_translate,
        description=(
            "Translate text between languages. Input format: 'the text | from:to', "
            "e.g. 'good morning | en:fr'. Defaults to en:es if you omit the languages."
        ),
    )
