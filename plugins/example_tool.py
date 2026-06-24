"""an example plugin so the loader has something real to find.

copy this file, rename it, and change the body to make your own tool. anything in the
plugin dir that registers via @register shows up in the agent's tool belt automatically.
delete this file if you don't want the demo tool loaded.
"""

from __future__ import annotations

from langchain.tools import Tool

from agent.tools import register


@register("reverse")
def _reverse():
    """a deliberately trivial tool: hand it text, get it back reversed."""
    return Tool(
        name="reverse",
        description="Reverse a string. Input: the text to reverse.",
        func=lambda text: text[::-1],
    )
