import json
import io
import urllib.request

import pytest

from btc_ai_api.client import MarketDataClient


class _BytesResponse(io.BytesIO):
    def __init__(self, payload, status: int = 200):
        super().__init__(json.dumps(payload).encode())
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


def test_fetch_snapshot_success(monkeypatch):
    payload = [
        {
            "current_price": 50000,
            "high_24h": 51000,
            "low_24h": 49000,
            "market_cap": 1_000_000,
            "total_volume": 10_000,
            "price_change_percentage_1h_in_currency": 0.5,
            "price_change_percentage_24h_in_currency": 1.0,
            "price_change_percentage_7d_in_currency": 6.0,
        }
    ]

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda request, timeout=10: _BytesResponse(payload)
    )

    client = MarketDataClient()
    snapshot = client.fetch_bitcoin_snapshot()

    assert snapshot["price"] == 50000
    assert snapshot["high_24h"] == 51000
    assert snapshot["low_24h"] == 49000
    assert snapshot["market_cap"] == 1_000_000
    assert snapshot["total_volume"] == 10_000
    assert "fetched_at" in snapshot


def test_fetch_snapshot_missing_field(monkeypatch):
    payload = [
        {
            "current_price": 50000,
            "high_24h": 51000,
            "low_24h": 49000,
            "total_volume": 10_000,
        }
    ]

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda request, timeout=10: _BytesResponse(payload)
    )

    client = MarketDataClient()

    with pytest.raises(ValueError):
        client.fetch_bitcoin_snapshot()


def test_fetch_snapshot_http_error(monkeypatch):
    payload = []
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda request, timeout=10: _BytesResponse(payload, status=500)
    )

    client = MarketDataClient()

    with pytest.raises(ConnectionError):
        client.fetch_bitcoin_snapshot()
