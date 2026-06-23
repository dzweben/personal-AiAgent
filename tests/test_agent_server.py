"""tests that build the agent and hit the api without ever calling a real model."""

import pytest

from agent.agent import AgentResult, build_agent
from agent.config import load_settings
from agent.models import ResearchResponse


def test_agent_builds_with_tools():
    agent = build_agent(settings=load_settings())
    assert agent._executor is not None
    assert len(agent._executor.tools) > 0


def test_agent_result_dataclass():
    r = AgentResult(query="q", raw={"output": "x"}, structured=None, output_text="x")
    assert r.query == "q"
    assert r.structured is None


def test_research_parses_structured(monkeypatch):
    """fake the executor so we exercise the parse path without an llm."""
    agent = build_agent(settings=load_settings())
    good = ResearchResponse(
        topic="Tea", summary="good", sources=["https://x.test"], tools_used=["search"]
    ).model_dump_json()
    monkeypatch.setattr(agent, "_invoke_once", lambda q: {"output": good})
    result = agent.research("tell me about tea")
    assert result.structured is not None
    assert result.structured.topic == "Tea"


def test_server_endpoints():
    fastapi = pytest.importorskip("fastapi")  # noqa: F841
    from fastapi.testclient import TestClient

    from agent.server import create_app

    client = TestClient(create_app())
    assert client.get("/health").json() == {"status": "ok"}
    assert "version" in client.get("/version").json()
    assert len(client.get("/tools").json()["tools"]) > 0
