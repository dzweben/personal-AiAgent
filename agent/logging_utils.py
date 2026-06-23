"""logging setup.

uses rich for pretty console logs when it is installed, and quietly degrades to the
plain stdlib logging when it is not. also tees to a file so i can dig through old runs.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

_CONFIGURED = False


def get_logger(name: str = "aiagent") -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(
    level: str = "INFO",
    file: str | None = "logs/agent.log",
    rich_tracebacks: bool = True,
) -> logging.Logger:
    """configure the root-ish 'aiagent' logger once. safe to call repeatedly."""
    global _CONFIGURED
    logger = logging.getLogger("aiagent")
    if _CONFIGURED:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    # console handler, pretty if rich is around
    try:
        from rich.logging import RichHandler

        console_handler: logging.Handler = RichHandler(
            rich_tracebacks=rich_tracebacks,
            show_path=False,
            markup=True,
        )
        console_handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    except ImportError:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s | %(message)s")
        )
    logger.addHandler(console_handler)

    # file handler, best effort. if we cannot make the dir we just skip it.
    if file:
        try:
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)-8s %(name)s | %(message)s")
            )
            logger.addHandler(file_handler)
        except OSError:
            pass

    logger.propagate = False
    _CONFIGURED = True
    return logger


def disable_noisy_loggers() -> None:
    """the http libraries love to spam at INFO, turn them down a notch."""
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "anthropic"):
        logging.getLogger(noisy).setLevel(os.environ.get("AIAGENT_DEP_LOG_LEVEL", "WARNING"))
