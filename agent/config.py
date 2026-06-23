"""settings for the agent.

resolution order, lowest priority first:
  1. the defaults baked into this file
  2. config.yaml (or whatever path you point at)
  3. environment variables / .env (prefixed AIAGENT_)
  4. anything you pass in code or via cli flags

i went with pydantic-settings so the env parsing and validation is free.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAS_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover - fallback for a bare install
    from pydantic import BaseModel as BaseSettings  # type: ignore

    SettingsConfigDict = dict  # type: ignore
    _HAS_PYDANTIC_SETTINGS = False


class MemoryConfig(BaseModel):
    enabled: bool = True
    path: str = ".agent_memory.sqlite"
    max_history: int = 20


class RagConfig(BaseModel):
    enabled: bool = False
    backend: str = "chroma"
    collection: str = "research"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 4


class CacheConfig(BaseModel):
    enabled: bool = True
    path: str = ".agent_cache"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str | None = "logs/agent.log"
    rich_tracebacks: bool = True


class ExportConfig(BaseModel):
    default_format: str = "markdown"
    directory: str = "exports"


class Settings(BaseSettings):
    """the one object everything else reads from."""

    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int = 2048

    verbose: bool = True
    stream: bool = True

    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    rag: RagConfig = Field(default_factory=RagConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)

    if _HAS_PYDANTIC_SETTINGS:
        model_config = SettingsConfigDict(
            env_prefix="AIAGENT_",
            env_nested_delimiter="__",
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )


def _read_yaml(path: str | os.PathLike[str]) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        import yaml

        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # if yaml is missing or the file is junk we just fall back to defaults
        return {}


def load_settings(
    config_path: str | os.PathLike[str] | None = None,
    **overrides: Any,
) -> Settings:
    """build a Settings object from yaml + env + explicit overrides.

    pass a config_path to load a yaml file, otherwise we look for config.yaml in the cwd.
    keyword overrides win over everything, which is what the cli flags use.
    """
    path = config_path or os.environ.get("AIAGENT_CONFIG", "config.yaml")
    data = _read_yaml(path)
    data.update({k: v for k, v in overrides.items() if v is not None})
    try:
        return Settings(**data)
    except Exception:
        # never let a bad config file hard crash the agent, just warn and use defaults
        return Settings()


# a module level singleton for the lazy folks (me)
settings = load_settings()
