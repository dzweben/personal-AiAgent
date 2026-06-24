"""render the agent's tool-call trace as a little ascii "thought tree".

the agent already calls tools under the hood; this turns a sequence of those calls into a
readable tree so you can watch what it actually did. it's part debugging aid, part eye candy.
pure string work, no deps, trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TraceStep:
    tool: str
    tool_input: str = ""
    output: str = ""


def _clip(text: str, width: int = 60) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[: width - 1] + "…"


def render_trace(steps: list[TraceStep], title: str = "agent run") -> str:
    """draw the steps as a branch tree. last step gets the corner glyph."""
    lines = [f"◆ {title}"]
    for i, step in enumerate(steps):
        last = i == len(steps) - 1
        elbow = "└─" if last else "├─"
        pipe = "  " if last else "│ "
        lines.append(f"{elbow} 🔧 {step.tool}({_clip(step.tool_input, 40)})")
        if step.output:
            lines.append(f"{pipe}   ↳ {_clip(step.output)}")
    return "\n".join(lines)


def steps_from_intermediate(intermediate_steps) -> list[TraceStep]:
    """adapt langchain's (AgentAction, observation) tuples into TraceSteps."""
    out: list[TraceStep] = []
    for action, observation in intermediate_steps or []:
        tool = getattr(action, "tool", "?")
        tool_input = getattr(action, "tool_input", "")
        out.append(TraceStep(tool=str(tool), tool_input=str(tool_input), output=str(observation)))
    return out
