"""HTTP client for fetching Bitcoin market data."""

from __future__ import annotations

import datetime as _dt
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable


class MarketDataClient:
    """Simple client for retrieving Bitcoin market data from CoinGecko."""

    def __init__(self, base_url: str | None = None, user_agent: str | None = None):
        self._base_url = base_url or "https://api.coingecko.com/api/v3"
        self._user_agent = user_agent or "btc-ai-assistant/1.0"

    def fetch_bitcoin_snapshot(self) -> Dict[str, Any]:
        """
        Fetch a snapshot of Bitcoin market data.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing price, high/low, volume, and change metrics.
        """

        query = urllib.parse.urlencode(
            {
                "vs_currency": "usd",
                "ids": "bitcoin",
                "price_change_percentage": "1h,24h,7d",
            }
        )
        url = f"{self._base_url}/coins/markets?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if getattr(response, "status", 200) >= 400:  # pragma: no cover - network dependent
                    raise ConnectionError(
                        f"Market data provider returned HTTP {response.status}"
                    )
                payload = json.load(response)
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise ConnectionError(f"Failed to reach market data provider: {exc}") from exc

        if not payload:
            raise ValueError("Empty response from market data provider")

        record = payload[0]
        self._validate_record(record)

        return {
            "fetched_at": _dt.datetime.utcnow().isoformat() + "Z",
            "price": float(record["current_price"]),
            "high_24h": float(record["high_24h"]),
            "low_24h": float(record["low_24h"]),
            "market_cap": float(record["market_cap"]),
            "total_volume": float(record["total_volume"]),
            "price_change_percentage_1h_in_currency": float(
                record.get("price_change_percentage_1h_in_currency", 0.0)
            ),
            "price_change_percentage_24h_in_currency": float(
                record.get("price_change_percentage_24h_in_currency", 0.0)
            ),
            "price_change_percentage_7d_in_currency": float(
                record.get("price_change_percentage_7d_in_currency", 0.0)
            ),
        }

    def _validate_record(self, record: Dict[str, Any]) -> None:
        missing = [
            field
            for field in self._required_fields()
            if field not in record or record[field] is None
        ]
        if missing:
            raise ValueError(f"Market data missing required fields: {', '.join(missing)}")

    @staticmethod
    def _required_fields() -> Iterable[str]:
        return (
            "current_price",
            "high_24h",
            "low_24h",
            "market_cap",
            "total_volume",
        )
