"""tests for the newer layers: provider defaults, the plugin loader, and session admin."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.llm import LOCAL_PROVIDERS, default_model_for
from agent.memory import ConversationMemory
from agent.plugins import load_plugins, plugin_dir

# ---- provider defaults -------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,expected",
    [
        ("openai", "gpt-4o"),
        ("anthropic", "claude-3-5-sonnet-latest"),
        ("ollama", "llama3.1"),
        ("mistral", "mistral-large-latest"),
        ("cohere", "command-r-plus"),
    ],
)
def test_default_model_for_known_providers(provider, expected):
    assert default_model_for(provider) == expected


def test_unknown_provider_falls_back_to_openai():
    assert default_model_for("nope") == "gpt-4o"


def test_local_providers_marked():
    assert "ollama" in LOCAL_PROVIDERS and "openai" not in LOCAL_PROVIDERS


# ---- plugin loader -----------------------------------------------------------------------


def test_plugin_dir_respects_env(monkeypatch, tmp_path):
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    assert plugin_dir() == Path(str(tmp_path))


def test_loads_plugin_file_and_registers_tool(monkeypatch, tmp_path):
    plugin = tmp_path / "my_plugin.py"
    plugin.write_text(
        "from langchain.tools import Tool\n"
        "from agent.tools import register\n"
        "@register('shout')\n"
        "def _shout():\n"
        "    return Tool(name='shout', description='upper', func=lambda s: s.upper())\n"
    )
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    loaded = load_plugins()
    assert "my_plugin" in loaded

    from agent.tools import build_tools

    tools = build_tools(enabled=["shout"])
    assert any(t.name == "shout" for t in tools)


def test_bad_plugin_is_skipped_not_fatal(monkeypatch, tmp_path):
    (tmp_path / "broken.py").write_text("this is not valid python ===\n")
    (tmp_path / "_ignored.py").write_text("raise RuntimeError('should never import')\n")
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path))
    # underscore file is skipped, broken file is caught -> no exception bubbles up
    loaded = load_plugins()
    assert "broken" not in loaded and "_ignored" not in loaded


def test_missing_plugin_dir_is_fine(monkeypatch, tmp_path):
    monkeypatch.setenv("AIAGENT_PLUGIN_DIR", str(tmp_path / "does-not-exist"))
    assert load_plugins() == []


# ---- session administration --------------------------------------------------------------


def _mem(tmp_path, session="default"):
    return ConversationMemory(path=str(tmp_path / "mem.sqlite"), session=session)


def test_session_stats_counts_and_orders(tmp_path):
    a = _mem(tmp_path, "alpha")
    a.add_user("hi")
    a.add_assistant("hello")
    b = _mem(tmp_path, "beta")
    b.add_user("yo")

    stats = a.session_stats()
    names = {row["session"] for row in stats}
    assert names == {"alpha", "beta"}
    alpha = next(r for r in stats if r["session"] == "alpha")
    assert alpha["turns"] == 2


def test_rename_session_moves_turns(tmp_path):
    m = _mem(tmp_path, "old")
    m.add_user("remember me")
    moved = m.rename_session("old", "new")
    assert moved == 1
    assert "new" in m.sessions() and "old" not in m.sessions()


def test_delete_session_removes_turns(tmp_path):
    m = _mem(tmp_path, "doomed")
    m.add_user("bye")
    removed = m.delete_session("doomed")
    assert removed == 1
    assert "doomed" not in m.sessions()
