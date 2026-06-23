"""personal-aiagent

started as a little langchain research script, then i kept adding stuff until it
turned into an actual package. this module just exposes the nice top level bits so
you can do `from agent import build_agent, Settings` and get going.
"""

from agent.config import Settings, load_settings
from agent.models import ResearchResponse, Citation, Source

__version__ = "0.2.0"

__all__ = [
    "Settings",
    "load_settings",
    "ResearchResponse",
    "Citation",
    "Source",
    "__version__",
]


def build_agent(*args, **kwargs):
    """lazy wrapper so importing the package does not drag in langchain unless you ask.

    importing langchain at module import time made the cli feel sluggish, so we defer it.
    """
    from agent.agent import build_agent as _build_agent

    return _build_agent(*args, **kwargs)
