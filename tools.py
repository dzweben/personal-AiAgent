"""backwards compatible tools module.

the original project imported `search_tool`, `wiki_tool`, and `save_tool` straight from
this file. all the real tool code now lives in the `agent.tools` package, but i kept this
shim around so old imports (and muscle memory) keep working exactly like before.

new code should prefer `from agent.tools import build_tools`.
"""

from __future__ import annotations

from agent.tools.files import save_to_txt, make_save
from agent.tools.web import make_search
from agent.tools.wiki import make_wiki

# the three classic tools, built once so importing this module gives you ready objects
save_tool = make_save()
search_tool = make_search()
wiki_tool = make_wiki()

__all__ = ["save_tool", "search_tool", "wiki_tool", "save_to_txt"]
