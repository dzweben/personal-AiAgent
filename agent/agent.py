"""the core agent.

this is the grown up version of what used to live at the bottom of main.py. it wires the
llm, the prompt, the tools, the output parser, optional memory, and optional retries into
one object you can just call .research(query) on.

the original flow (ChatOpenAI -> create_tool_calling_agent -> AgentExecutor -> parse) is
still exactly what happens under the hood, i just wrapped it so it is reusable and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from agent.config import Settings, load_settings
from agent.logging_utils import get_logger, setup_logging
from agent.models import ResearchResponse
from agent.prompts import system_prompt

log = get_logger(__name__)


@dataclass
class AgentResult:
    """what .research() hands back. structured is None if parsing failed."""

    query: str
    raw: dict
    structured: Optional[ResearchResponse]
    output_text: str


class ResearchAgent:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        tools: Optional[list] = None,
        memory: Any = None,
        detailed: bool = False,
        persona: Optional[str] = None,
    ):
        self.settings = settings or load_settings()
        self.detailed = detailed
        self.persona = persona
        self.memory = memory
        self._tools = tools
        self._executor = None
        self._parser = None

    # building blocks -------------------------------------------------------

    def _build_parser(self):
        from langchain_core.output_parsers import PydanticOutputParser

        return PydanticOutputParser(pydantic_object=ResearchResponse)

    def _build_tools(self):
        if self._tools is not None:
            return self._tools
        from agent.tools import build_tools

        enabled = None  # let it grab everything that loads
        return build_tools(enabled=enabled)

    def _build_prompt(self, parser):
        from langchain_core.prompts import ChatPromptTemplate

        base_system = system_prompt(self.detailed)
        if self.persona:
            from agent import personas

            try:
                base_system = personas.apply(base_system, self.persona)
            except KeyError as exc:
                log.warning("%s, ignoring persona", exc)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", base_system),
                ("placeholder", "{chat_history}"),
                ("human", "{query}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())
        return prompt

    def build(self) -> "ResearchAgent":
        """assemble the underlying langchain AgentExecutor. lazy, called on first use."""
        if self._executor is not None:
            return self

        from langchain.agents import AgentExecutor, create_tool_calling_agent

        from agent.llm import build_llm

        setup_logging(
            level=self.settings.logging.level,
            file=self.settings.logging.file,
            rich_tracebacks=self.settings.logging.rich_tracebacks,
        )

        llm = build_llm(self.settings)
        self._parser = self._build_parser()
        tools = self._build_tools()
        prompt = self._build_prompt(self._parser)

        agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=tools)
        self._executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=self.settings.verbose,
            handle_parsing_errors=True,
            max_iterations=12,
        )
        log.debug("agent built with %d tools", len(tools))
        return self

    # running ---------------------------------------------------------------

    def _invoke_once(self, query: str) -> dict:
        chat_history = self.memory.as_langchain_messages() if self.memory else []
        return self._executor.invoke({"query": query, "chat_history": chat_history})

    def research(self, query: str) -> AgentResult:
        """run a query and try to parse the structured response.

        retries the invoke a couple of times on transient errors if tenacity is around.
        """
        self.build()

        def _run() -> dict:
            return self._invoke_once(query)

        raw = self._with_retries(_run)
        output_text = raw.get("output", "") if isinstance(raw, dict) else str(raw)

        structured: Optional[ResearchResponse] = None
        try:
            structured = self._parser.parse(output_text)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not parse structured response: %s", exc)

        if self.memory:
            self.memory.add_user(query)
            self.memory.add_assistant(output_text)

        return AgentResult(query=query, raw=raw, structured=structured, output_text=output_text)

    def _with_retries(self, fn):
        try:
            from tenacity import retry, stop_after_attempt, wait_exponential

            wrapped = retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                reraise=True,
            )(fn)
            return wrapped()
        except ImportError:
            return fn()


def build_agent(
    settings: Optional[Settings] = None,
    detailed: bool = False,
    memory: Any = None,
    tools: Optional[list] = None,
    persona: Optional[str] = None,
) -> ResearchAgent:
    """convenience constructor used by main.py, the cli, and the api."""
    return ResearchAgent(
        settings=settings, tools=tools, memory=memory, detailed=detailed, persona=persona
    ).build()
