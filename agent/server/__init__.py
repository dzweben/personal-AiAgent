"""optional http server for the agent.

needs the `server` extra (fastapi + uvicorn). import is lazy so the rest of the project
does not depend on it. run it with:  python -m agent.server
"""

from agent.server.api import create_app

__all__ = ["create_app"]
