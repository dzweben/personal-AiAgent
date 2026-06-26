"""the scholarly research-writing arm.

a retrieval-grounded writer whose knowledge comes ONLY from open-access academic literature --
pulled from legitimate scholarly indexes (OpenAlex, Semantic Scholar, arXiv, Crossref, Europe
PMC), filtered to empirical studies and literature reviews. it does not memorise or invent
papers; every citation traces back to a real record it actually retrieved.

(note: Google Scholar has no open api and forbids scraping, so this uses the open indexes that
cover the same literature -- same papers, legitimately accessible.)
"""

from __future__ import annotations

from agent.scholar.paper import Paper

__all__ = ["Paper"]
