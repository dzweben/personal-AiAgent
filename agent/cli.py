"""the command line interface.

this is the front door for the grown up version of the agent. the classic `python main.py`
flow still exists and still works, but if you install the package you also get an `aiagent`
command with proper subcommands: research, chat, tools, export, memory, config.

built on typer so the help text and arg parsing come for free.
"""

from __future__ import annotations

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
    provider: str | None = typer.Option(
        None, help="openai | anthropic | groq | google | ollama | mistral | cohere"
    ),
    model: str | None = typer.Option(None, help="override the model name"),
    temperature: float | None = typer.Option(None, help="0 is focused, 1 is loose"),
    detailed: bool = typer.Option(False, help="use the more careful, source heavy prompt"),
    persona: str | None = typer.Option(
        None, help="researcher | skeptic | eli5 | journalist | tutor | devils_advocate"
    ),
    export_as: str | None = typer.Option(
        None, "--export", help="also save to md/json/html/txt/pdf"
    ),
    remember: bool = typer.Option(False, help="store this turn in conversation memory"),
    config: str | None = typer.Option(None, help="path to a yaml config file"),
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

    agent = build_agent(settings=settings, detailed=detailed, memory=mem, persona=persona)
    with console.console().status("thinking...") if console.console() else _noop():
        result = agent.research(query)

    console.print_response(result)

    if export_as:
        from agent.exporters import export

        path = export(result, fmt=export_as, directory=settings.export.directory)
        console.success(f"saved export to {path}")


@app.command()
def chat(
    provider: str | None = typer.Option(None),
    model: str | None = typer.Option(None),
    session: str = typer.Option("default", help="name this conversation so memory groups it"),
    config: str | None = typer.Option(None),
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


@app.command(name="personas")
def list_personas():
    """list the personas you can run the agent as."""
    from agent import personas

    for name in personas.names():
        p = personas.get(name)
        console.info(f"{name}: {p.blurb}")


@app.command()
def cost(
    prompt: str = typer.Argument(..., help="the text you plan to send"),
    model: str = typer.Option("gpt-4o", help="which model to price against"),
    output_tokens: int = typer.Option(500, help="rough guess at the response length"),
):
    """estimate the token count and dollar cost of a prompt before you send it."""
    from agent.usage import estimate_cost

    est = estimate_cost(prompt, expected_output_tokens=output_tokens, model=model)
    console.info(est.pretty())


@app.command()
def memory(
    action: str = typer.Argument("show", help="show | clear | sessions | stats | rename | delete"),
    session: str = typer.Option("default"),
    to: str | None = typer.Option(None, "--to", help="new name when action is rename"),
    config: str | None = typer.Option(None),
):
    """inspect, organise, or wipe the conversation memory."""
    from agent.memory import ConversationMemory

    settings = load_settings(config_path=config)
    mem = ConversationMemory(path=settings.memory.path, session=session)
    if action == "clear":
        mem.clear()
        console.success(f"cleared session {session!r}")
    elif action == "sessions":
        console.info("sessions: " + (", ".join(mem.sessions()) or "(none)"))
    elif action == "stats":
        rows = mem.session_stats()
        if not rows:
            console.info("no sessions yet")
        for row in rows:
            console.info(
                f"- {row['session']}: {row['turns']} turns, last active {row['last_active']}"
            )
    elif action == "rename":
        if not to:
            console.error("rename needs --to <new-name>")
            raise typer.Exit(code=1)
        moved = mem.rename_session(session, to)
        console.success(f"renamed {session!r} -> {to!r} ({moved} turns)")
    elif action == "delete":
        removed = mem.delete_session(session)
        console.success(f"deleted session {session!r} ({removed} turns)")
    else:
        for role, content in mem.history():
            (
                console.markdown(f"**{role}**: {content[:300]}")
                if console.console()
                else print(role, content[:300])
            )


@app.command(name="plugins")
def list_plugins():
    """discover and list any third-party tool plugins on this machine."""
    from agent.plugins import load_plugins, plugin_dir

    loaded = load_plugins()
    console.info(f"plugin dir: {plugin_dir()}")
    if loaded:
        console.success("loaded plugins: " + ", ".join(loaded))
    else:
        console.info("no plugins found (drop .py files in the plugin dir to add some)")


@app.command()
def forge(
    name: str = typer.Option(..., help="what to call the new tool"),
    desc: str = typer.Option(..., help="description, or the intent to hand the model with --llm"),
    expr: str | None = typer.Option(
        None,
        help="python expression for the body, with `x` as the input string, "
        'e.g. "float(x) * 2". omit when using --llm.',
    ),
    llm: bool = typer.Option(False, help="let the model write the expression from --desc"),
    provider: str | None = typer.Option(None, help="provider to use when --llm is set"),
    model: str | None = typer.Option(None),
    overwrite: bool = typer.Option(False, help="replace an existing tool of the same name"),
):
    """grow the agent a brand new tool at runtime and hot-load it into the belt.

    the expression is sandbox-checked (allowlisted imports only, no os/sys/eval/open/...) before
    anything is written or imported, whether you wrote it or the model did. examples:

        aiagent forge --name double --desc "doubles a number" --expr "float(x) * 2"
        aiagent forge --name slugify --desc "make text url-safe" --llm
    """
    from agent.forge import SafetyError
    from agent.forge import forge as _forge

    try:
        if llm:
            from agent.forge import forge_from_intent

            settings = _settings(provider, model, None, False, None)
            path, written = forge_from_intent(name, desc, settings=settings, overwrite=overwrite)
            console.info(f"the model wrote: {written}")
        else:
            if not expr:
                console.error("pass --expr, or use --llm to have the model write it")
                raise typer.Exit(code=1)
            path = _forge(name, desc, expr, overwrite=overwrite)
    except SafetyError as exc:
        console.error(f"refused to forge: {exc}")
        raise typer.Exit(code=1) from exc
    except (FileExistsError, RuntimeError) as exc:
        console.error(str(exc))
        raise typer.Exit(code=1) from exc
    console.success(f"forged {name!r} -> {path}")
    console.info("it's live now; run `aiagent tools` to see it in the belt.")


@app.command()
def debate(
    question: str = typer.Argument(..., help="the question to argue out"),
    rounds: int = typer.Option(2, help="how many back-and-forth rounds"),
    sides: str = typer.Option("optimist,skeptic", help="two comma-separated stances"),
    provider: str | None = typer.Option(None),
    model: str | None = typer.Option(None),
):
    """make two voices argue a question, then a moderator synthesises. (needs an api key)"""
    from agent.debate import run_debate

    settings = _settings(provider, model, None, False, None)
    a, _, b = sides.partition(",")
    res = run_debate(
        question, speakers=(a.strip(), b.strip() or "skeptic"), rounds=rounds, settings=settings
    )
    console.markdown(res.pretty()) if console.console() else print(res.pretty())


@app.command()
def swarm(
    task: str = typer.Argument(..., help="what the team should work on"),
    roles: str = typer.Option("researcher,critic,synthesizer", help="comma-separated roles"),
    rounds: int = typer.Option(1, help="how many passes over the blackboard"),
    provider: str | None = typer.Option(None),
    model: str | None = typer.Option(None),
):
    """run a little society of role-playing agents over a shared blackboard. (needs an api key)"""
    from agent.swarm import run_swarm

    settings = _settings(provider, model, None, False, None)
    res = run_swarm(
        task, roles=[r.strip() for r in roles.split(",")], rounds=rounds, settings=settings
    )
    console.markdown(res.pretty()) if console.console() else print(res.pretty())


@app.command()
def evolve(
    generations: int = typer.Option(12, help="how many generations to run"),
    pop: int = typer.Option(16, help="population size"),
    seed: int = typer.Option(0, help="rng seed for reproducibility"),
):
    """evolve a system prompt with a genetic algorithm (offline heuristic fitness)."""
    from agent.evolve import evolve as _evolve

    res = _evolve(generations=generations, pop_size=pop, seed=seed)
    console.info(f"best fitness: {res.best_fitness:.2f} (from {res.history[0]:.2f})")
    console.success("evolved prompt:")
    console.markdown(f"> {res.prompt()}") if console.console() else print(res.prompt())


@app.command()
def dream(
    n: int = typer.Option(5, help="how many dreams to generate"),
    seed: int = typer.Option(0),
    session: str = typer.Option("default"),
    config: str | None = typer.Option(None),
):
    """free-associate over your conversation memory into surreal research prompts."""
    from agent.dream import dream_from_memory
    from agent.memory import ConversationMemory

    settings = load_settings(config_path=config)
    mem = ConversationMemory(path=settings.memory.path, session=session)
    dreams = dream_from_memory(mem, n=n, seed=seed)
    if not dreams:
        console.info("not enough memory to dream on yet; go have some conversations first.")
        return
    for d in dreams:
        console.info(f"  💭 {d}")


@app.command()
def oracle(
    query: str = typer.Argument(..., help="the question you're stuck on"),
    n: int = typer.Option(3, help="how many cards to draw"),
    seed: int = typer.Option(0),
):
    """draw oblique-strategy cards to reframe a question from weird angles."""
    from agent.oracle import draw

    for line in draw(query, n=n, seed=seed):
        console.info(f"  🔮 {line}")


@app.command()
def council(
    question: str = typer.Argument(..., help="the question to put to the council"),
    personas: str = typer.Option("researcher,skeptic,eli5", help="comma-separated personas"),
    rounds: int = typer.Option(2, help="max critique/revision rounds"),
    target: float = typer.Option(
        0.0, help="loop, self-correcting, until the score clears this (0..1); 0 = single pass"
    ),
    max_iter: int = typer.Option(1, "--max-iter", help="cap on self-correction iterations"),
    evolve: bool = typer.Option(
        False, help="first evolve the best persona line-up against the scorecard"
    ),
    provider: str | None = typer.Option(None),
    model: str | None = typer.Option(None),
    show_run: bool = typer.Option(False, "--show-run", help="also print the recorded run"),
):
    """convene the whole cabinet: route, ensemble, fact-check, critique, red-team, score, loop.

    needs an api key. raise --target/--max-iter to turn on the self-correction loop, or pass
    --evolve to let a genetic search pick the persona line-up first.
    """
    settings = _settings(provider, model, None, False, None)
    persona_list = [p.strip() for p in personas.split(",")]

    if evolve:
        from agent.council_evolve import convene_evolved

        console.info("evolving the persona line-up against the scorecard...")
        res, search = convene_evolved(
            question,
            settings=settings,
            refine_rounds=rounds,
            target_score=target,
            max_iterations=max_iter,
        )
        console.success(f"evolved line-up: {', '.join(search.personas)} (fit {search.fitness:.2f})")
    else:
        from agent.council import convene

        res = convene(
            question,
            personas=persona_list,
            refine_rounds=rounds,
            target_score=target,
            max_iterations=max_iter,
            settings=settings,
        )

    console.markdown(res.pretty()) if console.console() else print(res.pretty())
    if show_run:
        console.info("")
        console.info(res.recorder.pretty())


@app.command()
def route(query: str = typer.Argument(..., help="the query to classify")):
    """show which mode the router would pick for a query (offline, instant)."""
    from agent.router import route as _route

    r = _route(query)
    console.info(f"mode: {r.mode}  ({r.reason})")


@app.command(name="score")
def score_cmd(text: str = typer.Argument(..., help="an answer to grade")):
    """grade an answer with the offline heuristic scorecard."""
    from agent.scorecard import score as _score

    console.info(_score(text).pretty())


@app.command()
def capsule(
    path: str = typer.Argument(..., help="a json file to pack, or a capsule string to unpack"),
    decode: bool = typer.Option(False, help="decode a capsule back into json instead of encoding"),
    qr: str | None = typer.Option(None, help="also write the capsule as a qr png to this path"),
):
    """pack a json result into a tiny portable capsule string (or --decode one back)."""
    import json
    from pathlib import Path

    from agent.capsule import CapsuleError, encode, to_qr
    from agent.capsule import decode as _decode

    try:
        if decode:
            text = Path(path).read_text() if Path(path).exists() else path
            obj = _decode(text.strip())
            out = json.dumps(obj, indent=2)
            console.markdown(f"```json\n{out}\n```") if console.console() else print(out)
        else:
            obj = json.loads(Path(path).read_text())
            cap = encode(obj)
            console.success(cap)
            if qr:
                to_qr(cap, qr)
                console.info(f"wrote qr to {qr}")
    except (CapsuleError, FileNotFoundError, json.JSONDecodeError) as exc:
        console.error(str(exc))
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:  # qr extra missing
        console.error(str(exc))
        raise typer.Exit(code=1) from exc


@app.command(name="mcp")
def mcp(
    list_only: bool = typer.Option(False, "--list", help="just print the tool definitions"),
):
    """serve the whole tool belt over the Model Context Protocol (needs `pip install mcp`)."""
    from agent.mcp_server import to_mcp_tools

    if list_only:
        for d in to_mcp_tools():
            console.info(f"- {d['name']}: {d['description'][:70]}")
        return
    try:
        from agent.mcp_server import run

        console.banner("aiagent mcp")
        console.info("serving tools over MCP on stdio... (ctrl-c to stop)")
        run()
    except RuntimeError as exc:
        console.error(str(exc))
        raise typer.Exit(code=1) from exc


@app.command(name="config")
def show_config(config: str | None = typer.Option(None)):
    """print the resolved settings so you can see what the agent will actually do."""
    settings = load_settings(config_path=config)
    (
        console.markdown("```json\n" + settings.model_dump_json(indent=2) + "\n```")
        if console.console()
        else print(settings.model_dump_json(indent=2))
    )


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="host to bind"),
    port: int = typer.Option(8000, help="port to listen on"),
):
    """run the http api (needs the server extra: pip install 'personal-aiagent[server]')."""
    try:
        from agent.server.api import run
    except RuntimeError as exc:
        console.error(str(exc))
        raise typer.Exit(code=1) from exc
    console.banner("aiagent api")
    console.info(f"serving on http://{host}:{port} (docs at /docs)")
    run(host=host, port=port)


@app.command(name="eval")
def run_eval_cmd(
    queries: list[str] = typer.Argument(..., help="one or more queries to benchmark"),
    provider: str | None = typer.Option(None),
    model: str | None = typer.Option(None),
):
    """run a quick benchmark over some queries and print summary metrics."""
    from agent.agent import build_agent
    from agent.evaluate import EvalCase, run_eval

    settings = _settings(provider, model, None, False, None)
    agent = build_agent(settings=settings)
    report = run_eval(agent, [EvalCase(q) for q in queries])
    for r in report.results:
        status = "ok" if r.parsed else "no structured output"
        console.info(f"- {r.query[:50]} -> {status}, {r.n_sources} sources, {r.seconds}s")
    console.success(report.summary())


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
