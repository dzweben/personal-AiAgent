"""a small fastapi app that puts the agent behind a rest api.

endpoints:
  GET  /            -> a friendly hello + links
  GET  /health      -> liveness check
  GET  /version     -> package version
  GET  /tools       -> list loadable tools
  POST /research    -> run a query, get the structured result back as json

kept deliberately thin. auth, rate limiting, etc are left as an exercise because this is a
personal project and i run it on localhost.
"""

from __future__ import annotations


def create_app():
    """build and return the FastAPI app. imported lazily so fastapi stays optional."""
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pip install 'personal-aiagent[server]' to run the api") from exc

    from agent import __version__
    from agent.config import load_settings

    app = FastAPI(
        title="personal-aiagent",
        version=__version__,
        description="a little research agent that got out of hand, now with an http api.",
    )

    class ResearchRequest(BaseModel):
        query: str
        provider: str | None = None
        model: str | None = None
        detailed: bool = False
        export_as: str | None = None

    @app.get("/")
    def root():
        return {
            "name": "personal-aiagent",
            "version": __version__,
            "docs": "/docs",
            "endpoints": ["/health", "/version", "/tools", "/research"],
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/version")
    def version():
        return {"version": __version__}

    @app.get("/tools")
    def tools():
        from agent.tools import available_tool_names

        return {"tools": available_tool_names()}

    @app.post("/research")
    def research(req: ResearchRequest):
        from agent.agent import build_agent

        settings = load_settings(provider=req.provider, model=req.model)
        try:
            agent = build_agent(settings=settings, detailed=req.detailed)
            result = agent.research(req.query)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        payload = {
            "query": result.query,
            "output": result.output_text,
            "structured": result.structured.model_dump() if result.structured else None,
        }
        if req.export_as and result.structured is not None:
            from agent.exporters import export

            payload["export_path"] = export(
                result, fmt=req.export_as, directory=settings.export.directory
            )
        return payload

    return app


def run(host: str = "127.0.0.1", port: int = 8000):  # pragma: no cover - needs uvicorn
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    run()
