"""llm factory.

picks the right chat model based on the provider in settings. openai and anthropic were
in the original project, i added groq and google as optional extras since they use the
same langchain interface and it was basically free to support them. ollama, mistral and
cohere came later in the same spirit -- one more elif and you get another backend.
"""

from __future__ import annotations

import os

from agent.config import Settings
from agent.logging_utils import get_logger

log = get_logger(__name__)


def build_llm(settings: Settings, streaming: bool | None = None):
    """return a langchain chat model configured from settings."""
    provider = (settings.provider or "openai").lower()
    stream = settings.stream if streaming is None else streaming
    common = {"temperature": settings.temperature, "streaming": stream}

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.model, max_tokens=settings.max_tokens, **common)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=settings.model, max_tokens=settings.max_tokens, **common)

    if provider == "groq":
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pip install langchain-groq to use the groq provider") from exc
        return ChatGroq(model=settings.model, **common)

    if provider in ("google", "gemini"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pip install langchain-google-genai to use the google provider"
            ) from exc
        return ChatGoogleGenerativeAI(model=settings.model, temperature=settings.temperature)

    if provider in ("ollama", "local"):
        # runs against a local ollama daemon, so no api key and no cloud round trip.
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pip install langchain-ollama to use the ollama provider") from exc
        base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return ChatOllama(model=settings.model, temperature=settings.temperature, base_url=base_url)

    if provider == "mistral":
        try:
            from langchain_mistralai import ChatMistralAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pip install langchain-mistralai to use the mistral provider"
            ) from exc
        return ChatMistralAI(model=settings.model, max_tokens=settings.max_tokens, **common)

    if provider == "cohere":
        try:
            from langchain_cohere import ChatCohere
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pip install langchain-cohere to use the cohere provider") from exc
        return ChatCohere(model=settings.model, temperature=settings.temperature)

    raise ValueError(
        f"unknown provider {provider!r}. try openai, anthropic, groq, google, "
        "ollama, mistral, or cohere."
    )


# providers that don't need a hosted api key to talk to (handy for the cli to hint about).
LOCAL_PROVIDERS = frozenset({"ollama", "local"})


def complete(prompt: str, settings: Settings | None = None, system: str | None = None) -> str:
    """one-shot text completion. build the chat model, send a message, return the text.

    a lot of the wilder features (forge --llm, debate, critique, swarm) just need "give the
    model a string, get a string back", so this is the small shared door they all knock on.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    from agent.config import load_settings

    settings = settings or load_settings()
    llm = build_llm(settings, streaming=False)
    messages: list = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))
    resp = llm.invoke(messages)
    return getattr(resp, "content", str(resp))


def default_model_for(provider: str) -> str:
    """a reasonable default model name per provider, used when none is given."""
    return {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-latest",
        "groq": "llama-3.1-70b-versatile",
        "google": "gemini-1.5-pro",
        "ollama": "llama3.1",
        "local": "llama3.1",
        "mistral": "mistral-large-latest",
        "cohere": "command-r-plus",
    }.get(provider.lower(), "gpt-4o")
