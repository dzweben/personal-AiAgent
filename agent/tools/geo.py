"""ip geolocation via a free no-key api. handy for 'where is this ip' style questions."""

from __future__ import annotations

from langchain_core.tools import Tool

from agent.tools import register


def _geolocate(ip: str) -> str:
    import httpx

    ip = ip.strip()
    try:
        resp = httpx.get(f"http://ip-api.com/json/{ip}", timeout=15)
        resp.raise_for_status()
        d = resp.json()
    except Exception as exc:  # noqa: BLE001
        return f"geolocation failed: {exc}"
    if d.get("status") != "success":
        return f"could not locate {ip!r}: {d.get('message', 'unknown error')}"
    return (
        f"{d.get('query')}: {d.get('city')}, {d.get('regionName')}, {d.get('country')} "
        f"(isp: {d.get('isp')}, lat/lon: {d.get('lat')},{d.get('lon')})"
    )


@register("ip_geolocate")
def make_geo():
    return Tool(
        name="ip_geolocate",
        func=_geolocate,
        description="Look up the approximate location of an IP address. Input is an IP.",
    )
