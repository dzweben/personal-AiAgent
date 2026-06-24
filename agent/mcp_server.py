"""expose this agent's whole tool belt over the Model Context Protocol.

the meta one: the weekend toy becomes infrastructure. once this is running, any MCP client
(claude desktop, other agents, ide extensions) can discover and call the tools this project
loads -- search, calculator, the python repl, anything you forged with `aiagent forge`, the lot.
your research assistant turns into a tool server other AIs plug into.

the dict adapter (`to_mcp_tools`) is pure and offline-testable; `run()` needs the optional `mcp`
package and is left untested here since it starts a server.
"""

from __future__ import annotations

from typing import Any

from agent.logging_utils import get_logger

log = get_logger(__name__)


def to_mcp_tools(enabled: list[str] | None = None) -> list[dict[str, Any]]:
    """describe the agent's tools as MCP-style definitions (name, description, input schema).

    every tool here takes a single string input, so the schema is uniform. this is what an MCP
    client would see when it lists available tools.
    """
    from agent.tools import build_tools

    defs: list[dict[str, Any]] = []
    for tool in build_tools(enabled=enabled):
        defs.append(
            {
                "name": getattr(tool, "name", "?"),
                "description": getattr(tool, "description", "") or "",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "the input for this tool"}
                    },
                    "required": ["input"],
                },
            }
        )
    return defs


def run(
    name: str = "personal-aiagent", enabled: list[str] | None = None
) -> None:  # pragma: no cover
    """serve the tool belt over MCP on stdio. needs `pip install mcp`."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("pip install mcp to run the MCP server") from exc

    from agent.tools import build_tools

    server = FastMCP(name)
    for tool in build_tools(enabled=enabled):
        tool_name = getattr(tool, "name", None)
        if not tool_name:
            continue

        def _make(t):
            def _call(input: str) -> str:
                return str(t.func(input))

            return _call

        server.add_tool(
            _make(tool),
            name=tool_name,
            description=getattr(tool, "description", "") or "",
        )
    log.info("serving %d tools over MCP", len(build_tools(enabled=enabled)))
    server.run()
