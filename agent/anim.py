"""a wonky little techno-robot loading animation for when the agent is thinking.

while the model is off writing, the terminal shows a tiny blinking robot, a Cylon-style scanner
eye, a stream of glitchy binary, and a rotating set of self-important techno status words
("OVERCLOCKING THOUGHT CORES", "NEGOTIATING WITH ENTROPY"...). it's pure eye candy -- the frame
composition is deterministic and pure (so it's testable), and a small background thread paints it
to the terminal. it no-ops when output isn't a real terminal or AIAGENT_NO_ANIM is set.
"""

from __future__ import annotations

import hashlib
import os
import sys
import threading

# braille spinner
_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
# little robot faces (they blink / emote as the index advances)
_FACES = ["[◉‿◉]", "[◉_◉]", "[-‿-]", "[◉.◉]", "[¬‿¬]", "[•ᴗ•]", "[◉ω◉]", "[≖_≖]"]
# the self-important techno status words
WORDS = [
    "SYNTHESIZING",
    "OVERCLOCKING THOUGHT CORES",
    "ROUTING NEURONS",
    "COMPILING PROSE",
    "DEFRAGMENTING IDEAS",
    "BUFFERING BRILLIANCE",
    "NEGOTIATING WITH ENTROPY",
    "SPINNING UP THE GHOST",
    "TRANSMUTING CAFFEINE",
    "ALIGNING CITATIONS",
    "RETICULATING SPLINES",
    "WARMING THE TUBES",
]
_GLITCH = "▓▒░█▚▞"


def scanner(i: int, width: int = 6) -> str:
    """a KITT/Cylon bouncing eye: one bright cell sweeping back and forth."""
    period = 2 * (width - 1) if width > 1 else 1
    pos = i % period
    if pos >= width:
        pos = period - pos
    cells = ["▱"] * width
    cells[pos] = "▰"
    return "⟨" + "".join(cells) + "⟩"


def binary(i: int, n: int = 6, seed: int = 0) -> str:
    """a deterministic stream of glitchy bits."""
    h = int(hashlib.md5(f"{seed}:{i}".encode()).hexdigest(), 16)  # noqa: S324 - decorative only
    return "".join(str((h >> k) & 1) for k in range(n))


def _glitch_word(word: str, i: int) -> str:
    """occasionally corrupt a couple of characters for a flickery, broken-signal look."""
    h = int(hashlib.md5(f"g{i}".encode()).hexdigest(), 16)  # noqa: S324 - decorative only
    chars = list(word)
    letters = [j for j, c in enumerate(chars) if c.isalpha()]
    if letters:
        for bump in range(2):
            j = letters[(h >> (bump * 5)) % len(letters)]
            chars[j] = _GLITCH[(h >> (bump * 3)) % len(_GLITCH)]
    return "".join(chars)


def compose_frame(i: int, label: str = "", seed: int = 0) -> str:
    """build one animation frame as plain text. deterministic in i (so it's testable)."""
    spinner = _SPIN[i % len(_SPIN)]
    face = _FACES[(i // 3) % len(_FACES)]
    word = WORDS[(i // 14) % len(WORDS)]
    if i % 17 == 0:  # every so often, glitch the status word
        word = _glitch_word(word, i)
    line = f"{spinner} {face} {word} {scanner(i)} {binary(i, seed=seed)}"
    if label:
        line += f"  · {label}"
    return line


# ANSI niceties (neon cyan/green vibe); kept out of compose_frame so that stays pure text.
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_HIDE = "\033[?25l"
_SHOW = "\033[?25h"
_CLEAR_LINE = "\r\033[2K"


def _neon(frame: str) -> str:
    return f"{_CYAN}{frame}{_RESET}"


class Thinking:
    """context manager that animates the techno-robot loader while a block runs."""

    def __init__(
        self, label: str = "", stream=None, fps: float = 12.0, enabled: bool | None = None
    ):
        self.label = label
        self.stream = stream or sys.stderr
        self.interval = 1.0 / fps
        self.enabled = self._auto_enabled() if enabled is None else enabled
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _auto_enabled(self) -> bool:
        if os.environ.get("AIAGENT_NO_ANIM"):
            return False
        try:
            return bool(self.stream.isatty())
        except Exception:  # noqa: BLE001 - some streams have no isatty
            return False

    def __enter__(self) -> Thinking:
        if self.enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def _run(self) -> None:
        i = 0
        self.stream.write(_HIDE)
        while not self._stop.wait(self.interval):
            self.stream.write(_CLEAR_LINE + _neon(compose_frame(i, self.label)))
            self.stream.flush()
            i += 1

    def __exit__(self, *exc) -> bool:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.enabled:
            self.stream.write(_CLEAR_LINE + _SHOW)
            self.stream.flush()
        return False


def thinking(label: str = "", **kw) -> Thinking:
    """convenience: `with thinking('writing your review'): ...`."""
    return Thinking(label=label, **kw)
