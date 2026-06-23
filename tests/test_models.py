from agent.models import (
    Citation,
    Confidence,
    DetailedResearchResponse,
    ResearchResponse,
    Source,
)


def test_research_response_shape():
    r = ResearchResponse(topic="t", summary="s", sources=["a"], tools_used=["search"])
    assert r.topic == "t"
    assert r.sources == ["a"]


def test_source_short_prefers_title_and_url():
    s = Source(title="Tea Study", url="https://x.test")
    assert "Tea Study" in s.short()
    assert "https://x.test" in s.short()


def test_detailed_collapses_to_simple():
    d = DetailedResearchResponse(
        topic="Tea",
        summary="good",
        sources=[Source(url="https://x.test")],
        tools_used=["search"],
        confidence=Confidence.high,
    )
    simple = d.to_simple()
    assert isinstance(simple, ResearchResponse)
    assert simple.topic == "Tea"
    assert simple.sources == ["https://x.test"]


def test_citation_confidence_bounds():
    c = Citation(claim="x", source=Source(url="https://x.test"), confidence=0.9)
    assert 0 <= c.confidence <= 1
