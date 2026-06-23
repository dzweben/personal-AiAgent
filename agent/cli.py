"""the command line interface.

this is the front door for the grown up version of the agent. the classic `python main.py`
flow still exists and still works, but if you install the package you also get an `aiagent`
command with proper subcommands: research, chat, tools, export, memory, config.

built on typer so the help text and arg parsing come for free.
"""

from __future__ import annotations

from typing import Optional

try:
    import typer
except ImportError as exc:  # pragma: no cover
    raise SystemExit("typer is required for the cli. pip install typer rich") from exc

from agent import console
from agent.config import load_settings

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="personal-aiagent, a little research assistant that got out of hand.",
)


def _settings(provider, model, temperature, verbose, config):
    return load_settings(
        config_path=config,
        provider=provider,
        model=model,
        temperature=temperature,
        verbose=verbose,
    )


@app.command()
def research(
    query: str = typer.Argument(..., help="what do you want me to look into?"),
    provider: Optional[str] = typer.Option(None, help="openai | anthropic | groq | google"),
    model: Optional[str] = typer.Option(None, help="override the model name"),
    temperature: Optional[float] = typer.Option(None, help="0 is focused, 1 is loose"),
    detailed: bool = typer.Option(False, help="use the more careful, source heavy prompt"),
    export_as: Optional[str] = typer.Option(None, "--export", help="also save to md/json/html/txt/pdf"),
    remember: bool = typer.Option(False, help="store this turn in conversation memory"),
    config: Optional[str] = typer.Option(None, help="path to a yaml config file"),
    verbose: bool = typer.Option(True, help="show the agent's tool calls"),
):
    """run a one shot research query and print the structured result."""
    from agent.agent import build_agent

    settings = _settings(provider, model, temperature, verbose, config)
    console.banner()
    console.info(f"provider={settings.provider} model={settings.model} temp={settings.temperature}")

    mem = None
    if remember and settings.memory.enabled:
        from agent.memory import ConversationMemory

        mem = ConversationMemory(path=settings.memory.path, max_history=settings.memory.max_history)

    agent = build_agent(settings=settings, detailed=detailed, memory=mem)
    with console.console().status("thinking...") if console.console() else _noop():
        result = agent.research(query)

    console.print_response(result)

    if export_as:
        from agent.exporters import export

        path = export(result, fmt=export_as, directory=settings.export.directory)
        console.success(f"saved export to {path}")


@app.command()
def chat(
    provider: Optional[str] = typer.Option(None),
    model: Optional[str] = typer.Option(None),
    session: str = typer.Option("default", help="name this conversation so memory groups it"),
    config: Optional[str] = typer.Option(None),
):
    """interactive REPL with the agent. type 'exit' or ctrl-d to leave."""
    from agent.agent import build_agent
    from agent.memory import ConversationMemory

    settings = _settings(provider, model, None, True, config)
    mem = ConversationMemory(
        path=settings.memory.path, session=session, max_history=settings.memory.max_history
    )
    agent = build_agent(settings=settings, memory=mem)

    console.banner("aiagent chat")
    console.info("ask me things. 'exit' to quit, 'clear' to wipe this session's memory.")
    while True:
        try:
            query = input("\nyou > ").strip()
        except (EOFError, KeyboardInterrupt):
            console.info("\nbye")
            break
        if not query:
            continue
        if query.lower() in ("exit", "quit", ":q"):
            console.info("bye")
            break
        if query.lower() == "clear":
            mem.clear()
            console.success("memory cleared for this session")
            continue
        result = agent.research(query)
        console.print_response(result)


@app.command(name="tools")
def list_tools():
    """list every tool the agent can load right now."""
    from agent.tools import available_tool_names

    console.tools_table(available_tool_names())


@app.command()
def formats():
    """show the export formats that are available."""
    from agent.exporters import available_formats

    console.info("export formats: " + ", ".join(available_formats()))


@app.command()
def memory(
    action: str = typer.Argument("show", help="show | clear | sessions"),
    session: str = typer.Option("default"),
    config: Optional[str] = typer.Option(None),
):
    """inspect or wipe the conversation memory."""
    from agent.memory import ConversationMemory

    settings = load_settings(config_path=config)
    mem = ConversationMemory(path=settings.memory.path, session=session)
    if action == "clear":
        mem.clear()
        console.success(f"cleared session {session!r}")
    elif action == "sessions":
        console.info("sessions: " + (", ".join(mem.sessions()) or "(none)"))
    else:
        for role, content in mem.history():
            who = "[cyan]you[/cyan]" if role == "user" else "[green]agent[/green]"
            console.markdown(f"**{role}**: {content[:300]}") if console.console() else print(role, content[:300])


@app.command(name="config")
def show_config(config: Optional[str] = typer.Option(None)):
    """print the resolved settings so you can see what the agent will actually do."""
    settings = load_settings(config_path=config)
    console.markdown("```json\n" + settings.model_dump_json(indent=2) + "\n```") if console.console() else print(settings.model_dump_json(indent=2))


@app.command()
def version():
    """print the version."""
    from agent import __version__

    console.info(f"personal-aiagent {__version__}")


class _noop:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def main():  # entry point used by `python -m agent.cli`
    app()


if __name__ == "__main__":
    main()
