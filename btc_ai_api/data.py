"""Data fetching helpers for Bitcoin market data."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"


@dataclass
class PricePoint:
    """A single price/time observation."""

    time: datetime
    price: float


class MarketDataError(RuntimeError):
    """Raised when we cannot fetch or parse market data."""


def _http_get(url: str, params: dict) -> str:
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    try:
        with urllib.request.urlopen(full_url, timeout=10) as response:
            return response.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise MarketDataError(f"HTTP request failed: {exc}") from exc


def fetch_price_points(hours: float = 6.0) -> List[PricePoint]:
    """Fetch recent Bitcoin price data from CoinGecko.

    Args:
        hours: Number of past hours of data to request.

    Returns:
        A list of :class:`PricePoint` sorted by time.

    Raises:
        MarketDataError: If the HTTP request fails or the payload is invalid.
    """

    if hours <= 0:
        raise ValueError("hours must be positive")

    params = {"vs_currency": "usd", "days": hours / 24, "interval": "minute"}

    raw_body = _http_get(COINGECKO_URL, params)
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise MarketDataError(f"Failed to decode response: {exc}") from exc

    prices = payload.get("prices")
    if not isinstance(prices, list):
        raise MarketDataError("Unexpected response structure: missing prices list")

    points: List[PricePoint] = []
    for entry in prices:
        if not (isinstance(entry, list) and len(entry) == 2):
            continue
        timestamp_ms, price = entry
        try:
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            points.append(PricePoint(time=dt, price=float(price)))
        except Exception:  # noqa: BLE001
            continue

    if not points:
        raise MarketDataError("No valid price points returned")

    points.sort(key=lambda p: p.time)
    return points
