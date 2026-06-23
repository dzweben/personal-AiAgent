"""streaming callback handlers.

langchain can stream tokens as they are generated. this wires that up to rich (or plain
stdout) so you watch the answer appear instead of staring at a blank screen. it imports the
langchain base handler lazily so importing this module never forces a langchain import.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


def make_stream_handler(on_token: Optional[Callable[[str], None]] = None):
    """build a callback handler that fires on_token for each new chunk.

    returns None if langchain is not importable, so callers can just skip streaming.
    """
    try:
        from langchain_core.callbacks.base import BaseCallbackHandler
    except Exception:  # noqa: BLE001
        return None

    sink = on_token or _default_sink()

    class _StreamHandler(BaseCallbackHandler):
        def on_llm_new_token(self, token: str, **kwargs: Any) -> None:  # noqa: D401
            sink(token)

        def on_llm_end(self, *args: Any, **kwargs: Any) -> None:
            sink("\n")

    return _StreamHandler()


def _default_sink() -> Callable[[str], None]:
    """write tokens straight to the console as they arrive."""
    try:
        from rich.console import Console

        c = Console()

        def _rich_sink(token: str) -> None:
            c.print(token, end="", soft_wrap=True)

        return _rich_sink
    except Exception:  # noqa: BLE001
        import sys

        def _plain_sink(token: str) -> None:
            sys.stdout.write(token)
            sys.stdout.flush()

        return _plain_sink


class CollectingHandler:
    """a tiny non-langchain helper that just accumulates tokens into a string.

    handy in tests and anywhere you want the streamed text back as one piece at the end.
    """

    def __init__(self) -> None:
        self.tokens: list[str] = []

    def __call__(self, token: str) -> None:
        self.tokens.append(token)

    @property
    def text(self) -> str:
        return "".join(self.tokens)
