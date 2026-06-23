"""crypto price lookups via the coingecko free api. no key needed."""

from __future__ import annotations

from langchain_core.tools import Tool

from agent.tools import register

# a few friendly aliases so the model can say 'btc' instead of 'bitcoin'
_ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "doge": "dogecoin",
    "ada": "cardano",
    "xrp": "ripple",
}


def _price(spec: str) -> str:
    import httpx

    coin = spec.strip().lower()
    coin = _ALIASES.get(coin, coin)
    try:
        resp = httpx.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": coin, "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return f"crypto price lookup failed: {exc}"
    if coin not in data:
        return f"no price found for {coin!r}, try the full name like 'bitcoin'"
    price = data[coin].get("usd")
    change = data[coin].get("usd_24h_change")
    change_str = f"{change:+.2f}%" if change is not None else "?"
    return f"{coin}: ${price:,} ({change_str} over 24h)"


@register("crypto_price")
def make_crypto():
    return Tool(
        name="crypto_price",
        func=_price,
        description="Get the current USD price of a cryptocurrency, e.g. 'btc' or 'ethereum'.",
    )
