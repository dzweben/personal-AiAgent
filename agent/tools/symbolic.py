"""symbolic math via sympy: solve equations, differentiate, integrate, simplify.

only registers if sympy is installed (it is in the 'tools' extra). the plain calculator
handles arithmetic, this one is for the algebra-and-up stuff.
"""

from __future__ import annotations

from langchain_core.tools import Tool

from agent.tools import register


def _symbolic(spec: str) -> str:
    import sympy

    spec = spec.strip()
    x, y, z, t = sympy.symbols("x y z t")
    local = {"x": x, "y": y, "z": z, "t": t}
    try:
        if spec.lower().startswith("solve "):
            expr = sympy.sympify(spec[6:], locals=local)
            return str(sympy.solve(expr))
        if spec.lower().startswith("diff "):
            expr = sympy.sympify(spec[5:], locals=local)
            return str(sympy.diff(expr, x))
        if spec.lower().startswith("integrate "):
            expr = sympy.sympify(spec[10:], locals=local)
            return str(sympy.integrate(expr, x))
        if spec.lower().startswith("simplify "):
            expr = sympy.sympify(spec[9:], locals=local)
            return str(sympy.simplify(expr))
        # default: just simplify whatever was passed
        return str(sympy.simplify(sympy.sympify(spec, locals=local)))
    except Exception as exc:  # noqa: BLE001
        return f"could not do that symbolically: {exc}"


@register("symbolic_math")
def make_symbolic():
    import sympy  # noqa: F401 - raises if missing, so the tool just will not register

    return Tool(
        name="symbolic_math",
        func=_symbolic,
        description=(
            "Symbolic math with sympy. Prefix with 'solve', 'diff', 'integrate', or "
            "'simplify', e.g. 'solve x**2 - 4' or 'diff sin(x)*x'. Variables x y z t."
        ),
    )
