"""so `python -m agent.server` just works."""

from agent.server.api import run

if __name__ == "__main__":
    import os

    host = os.environ.get("AIAGENT_HOST", "127.0.0.1")
    port = int(os.environ.get("AIAGENT_PORT", "8000"))
    run(host=host, port=port)
