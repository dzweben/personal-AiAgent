"""pydantic schemas for the stuff the agent passes around.

the original project had a single ResearchResponse model. i kept that exact shape so
nothing downstream breaks, then added a few richer models for when i want more detail.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResearchResponse(BaseModel):
    """the original structured output. do not change these four fields, other code and
    the README examples both depend on them."""

    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]


class Source(BaseModel):
    """a single source the agent leaned on, with a bit more structure than a bare url."""

    title: str | None = None
    url: str | None = None
    snippet: str | None = None
    accessed_at: datetime = Field(default_factory=datetime.now)

    def short(self) -> str:
        if self.title and self.url:
            return f"{self.title} ({self.url})"
        return self.url or self.title or "unknown source"


class Citation(BaseModel):
    """a claim tied back to the source it came from. handy for the citations report."""

    claim: str
    source: Source
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DetailedResearchResponse(BaseModel):
    """the fancier output i use when i want the agent to really show its work."""

    topic: str
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.medium
    follow_up_questions: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)

    def to_simple(self) -> ResearchResponse:
        """squash back down to the original shape when something needs the old format."""
        return ResearchResponse(
            topic=self.topic,
            summary=self.summary,
            sources=[s.url or s.short() for s in self.sources],
            tools_used=self.tools_used,
        )
