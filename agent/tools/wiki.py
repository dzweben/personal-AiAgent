"""wikipedia lookup tool. straight port of the original, just lives here now."""

from __future__ import annotations

from agent.tools import register


@register("wikipedia")
def make_wiki():
    from langchain_community.tools import WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper

    api_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1500)
    return WikipediaQueryRun(api_wrapper=api_wrapper)
