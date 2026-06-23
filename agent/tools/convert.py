"""conversion tools: units and currency.

unit conversion is pure python with a little lookup table so it needs nothing. currency
hits a free no-key exchange rate api, and degrades to a clear message if it is offline.
"""

from __future__ import annotations

from langchain_core.tools import Tool

from agent.tools import register

# everything is defined relative to a base unit per dimension
_UNITS = {
    # length, base = meter
    "m": ("length", 1.0),
    "meter": ("length", 1.0),
    "km": ("length", 1000.0),
    "cm": ("length", 0.01),
    "mm": ("length", 0.001),
    "mi": ("length", 1609.344),
    "mile": ("length", 1609.344),
    "ft": ("length", 0.3048),
    "foot": ("length", 0.3048),
    "in": ("length", 0.0254),
    "inch": ("length", 0.0254),
    "yd": ("length", 0.9144),
    # mass, base = gram
    "g": ("mass", 1.0),
    "kg": ("mass", 1000.0),
    "mg": ("mass", 0.001),
    "lb": ("mass", 453.592),
    "oz": ("mass", 28.3495),
    # volume, base = liter
    "l": ("volume", 1.0),
    "ml": ("volume", 0.001),
    "gal": ("volume", 3.78541),
    "cup": ("volume", 0.236588),
}


def _convert_units(spec: str) -> str:
    """expects something like '10 km to mi' or '5 lb in kg'."""
    parts = spec.lower().replace(" in ", " to ").split()
    try:
        # find the value, the from unit, the word 'to', and the target unit
        value = float(parts[0])
        from_u = parts[1]
        to_u = parts[-1]
    except (ValueError, IndexError):
        return "give me something like '10 km to mi'"

    # temperature is special, handle it on its own
    if {from_u, to_u} & {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}:
        return _convert_temp(value, from_u, to_u)

    if from_u not in _UNITS or to_u not in _UNITS:
        return f"i do not know how to convert {from_u} or {to_u}"
    dim_a, factor_a = _UNITS[from_u]
    dim_b, factor_b = _UNITS[to_u]
    if dim_a != dim_b:
        return f"cannot convert {dim_a} to {dim_b}"
    result = value * factor_a / factor_b
    return f"{value} {from_u} = {round(result, 6)} {to_u}"


def _convert_temp(value: float, from_u: str, to_u: str) -> str:
    f = from_u[0]
    t = to_u[0]
    # to celsius first
    if f == "c":
        c = value
    elif f == "f":
        c = (value - 32) * 5 / 9
    else:  # kelvin
        c = value - 273.15
    if t == "c":
        out = c
    elif t == "f":
        out = c * 9 / 5 + 32
    else:
        out = c + 273.15
    return f"{value}{from_u.upper()} = {round(out, 4)}{to_u.upper()}"


@register("unit_convert")
def make_unit_convert():
    return Tool(
        name="unit_convert",
        func=_convert_units,
        description=(
            "Convert between units of length, mass, volume, or temperature. "
            "Input like '10 km to mi' or '72 f to c'."
        ),
    )


def _convert_currency(spec: str) -> str:
    """expects '100 usd to eur'. uses a free, no key exchange rate endpoint."""
    import httpx

    parts = spec.lower().replace(" in ", " to ").split()
    try:
        amount = float(parts[0])
        src = parts[1].upper()
        dst = parts[-1].upper()
    except (ValueError, IndexError):
        return "give me something like '100 usd to eur'"
    try:
        resp = httpx.get(
            f"https://open.er-api.com/v6/latest/{src}", timeout=15
        )
        resp.raise_for_status()
        rates = resp.json().get("rates", {})
    except Exception as exc:  # noqa: BLE001
        return f"currency lookup failed: {exc}"
    if dst not in rates:
        return f"no rate available for {dst}"
    converted = amount * rates[dst]
    return f"{amount} {src} = {round(converted, 2)} {dst}"


@register("currency")
def make_currency():
    return Tool(
        name="currency",
        func=_convert_currency,
        description="Convert an amount between currencies, e.g. '100 usd to eur'. Live rates.",
    )
