"""a calculator tool that does not just eval() whatever the model hands it.

i use numexpr if it is installed because it is safe and fast, and fall back to a tiny
ast based evaluator that only allows arithmetic. no builtins, no attribute access, none
of the usual eval footguns.
"""

from __future__ import annotations

import ast
import math
import operator

from langchain.tools import Tool

from agent.tools import register

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

_FUNCS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("only numbers are allowed")
    if isinstance(node, ast.BinOp):
        op = _OPS.get(type(node.op))
        if op is None:
            raise ValueError("operator not allowed")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _OPS.get(type(node.op))
        if op is None:
            raise ValueError("unary operator not allowed")
        return op(_eval_node(node.operand))
    if isinstance(node, ast.Name):
        if node.id in _NAMES:
            return _NAMES[node.id]
        raise ValueError(f"unknown name {node.id!r}")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
            raise ValueError("that function is not available")
        args = [_eval_node(a) for a in node.args]
        return _FUNCS[node.func.id](*args)
    raise ValueError("expression type not allowed")


def safe_calc(expression: str) -> str:
    expression = expression.strip().strip("`")
    # prefer numexpr when it is around, it is both safe and quick
    try:
        import numexpr

        return str(numexpr.evaluate(expression).item())
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        return f"could not evaluate: {exc}"

    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree))
    except Exception as exc:  # noqa: BLE001
        return f"could not evaluate: {exc}"


@register("calculator")
def make_calculator():
    return Tool(
        name="calculator",
        func=safe_calc,
        description=(
            "Evaluate a math expression. Supports + - * / ** %, parentheses, and functions "
            "like sqrt, log, sin, cos, factorial, plus constants pi and e. Input is the expression."
        ),
    )
