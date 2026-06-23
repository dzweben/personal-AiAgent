"""current weather tool via openweathermap. needs OPENWEATHER_API_KEY.

like the news tool it only shows up when the key exists so the model is not tempted to
call something that will just error.
"""

from __future__ import annotations

import os

from langchain.tools import Tool

from agent.tools import register


def _weather(location: str) -> str:
    import httpx

    key = os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        return "no OPENWEATHER_API_KEY set"
    params = {"q": location.strip(), "appid": key, "units": "metric"}
    try:
        resp = httpx.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=15)
        resp.raise_for_status()
        d = resp.json()
    except Exception as exc:  # noqa: BLE001
        return f"weather request failed: {exc}"

    try:
        desc = d["weather"][0]["description"]
        temp = d["main"]["temp"]
        feels = d["main"]["feels_like"]
        humidity = d["main"]["humidity"]
        wind = d["wind"]["speed"]
        name = d.get("name", location)
        return (
            f"{name}: {desc}, {temp}C (feels like {feels}C), "
            f"humidity {humidity}%, wind {wind} m/s"
        )
    except (KeyError, IndexError):
        return "got an unexpected response shape from the weather api"


@register("weather")
def make_weather():
    if not os.environ.get("OPENWEATHER_API_KEY"):
        raise RuntimeError("OPENWEATHER_API_KEY not set, skipping weather tool")
    return Tool(
        name="weather",
        func=_weather,
        description="Get the current weather for a city. Input is a city name, e.g. 'Boston'.",
    )
