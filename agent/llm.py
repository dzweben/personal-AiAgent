"""llm factory.

picks the right chat model based on the provider in settings. openai and anthropic were
in the original project, i added groq and google as optional extras since they use the
same langchain interface and it was basically free to support them.
"""

from __future__ import annotations

from agent.config import Settings
from agent.logging_utils import get_logger

log = get_logger(__name__)


def build_llm(settings: Settings, streaming: bool | None = None):
    """return a langchain chat model configured from settings."""
    provider = (settings.provider or "openai").lower()
    stream = settings.stream if streaming is None else streaming
    common = dict(temperature=settings.temperature, streaming=stream)

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

    raise ValueError(f"unknown provider {provider!r}. try openai, anthropic, groq, or google.")


def default_model_for(provider: str) -> str:
    """a reasonable default model name per provider, used when none is given."""
    return {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-latest",
        "groq": "llama-3.1-70b-versatile",
        "google": "gemini-1.5-pro",
    }.get(provider.lower(), "gpt-4o")
