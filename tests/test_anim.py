"""tests for the techno-robot loading animation (pure frame logic + safe no-op behavior)."""

from __future__ import annotations

import io

from agent.anim import Thinking, binary, compose_frame, scanner, thinking


def test_compose_frame_is_nonempty_and_has_label():
    frame = compose_frame(0, "writing your review")
    assert frame
    assert "writing your review" in frame


def test_frames_change_over_time():
    frames = {compose_frame(i) for i in range(20)}
    assert len(frames) > 5  # it actually animates


def test_compose_frame_is_deterministic():
    assert compose_frame(7, "x", seed=3) == compose_frame(7, "x", seed=3)


def test_scanner_bounces():
    positions = [scanner(i, 5) for i in range(8)]
    # the bright cell should reach both ends and come back
    assert positions[0] != positions[4]
    assert positions[0] == positions[8 - 8] and positions[1] == positions[7]


def test_binary_is_bits_and_deterministic():
    b = binary(5, n=6, seed=1)
    assert len(b) == 6 and set(b) <= {"0", "1"}
    assert b == binary(5, n=6, seed=1)


def test_thinking_is_noop_when_not_a_tty():
    buf = io.StringIO()  # not a tty
    t = Thinking("label", stream=buf)
    assert t.enabled is False
    with t:
        pass
    assert buf.getvalue() == ""  # nothing painted, no crash


def test_thinking_can_be_force_enabled_and_cleans_up():
    buf = io.StringIO()
    with thinking("go", stream=buf, enabled=True, fps=200):
        import time

        time.sleep(0.05)
    out = buf.getvalue()
    assert out  # it painted something
    assert out.endswith("\033[?25h")  # cursor restored on exit


def test_env_var_disables_animation(monkeypatch):
    monkeypatch.setenv("AIAGENT_NO_ANIM", "1")

    class FakeTTY(io.StringIO):
        def isatty(self):
            return True

    t = Thinking("x", stream=FakeTTY())
    assert t.enabled is False  # env var wins even on a tty
