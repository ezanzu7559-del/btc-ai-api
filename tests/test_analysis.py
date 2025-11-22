from btc_ai_api.analysis import Recommendation, render_report, summarize_trend


def test_summarize_trend_positive_signal():
    data = {
        "fetched_at": "2024-01-01T00:00:00Z",
        "price": 50000,
        "high_24h": 51000,
        "low_24h": 49000,
        "market_cap": 1_000_000,
        "total_volume": 10_000,
        "price_change_percentage_1h_in_currency": 0.5,
        "price_change_percentage_24h_in_currency": 1.0,
        "price_change_percentage_7d_in_currency": 6.0,
    }
    rec = summarize_trend(data)
    assert rec.action == "Consider buying"
    assert any("weekly performance" in reason for reason in rec.reasons)


def test_render_report_contains_key_lines():
    rec = Recommendation(action="Hold", reasons=["Test reason"])
    data = {
        "fetched_at": "2024-01-01T00:00:00Z",
        "price": 50000,
        "high_24h": 51000,
        "low_24h": 49000,
        "market_cap": 1_000_000,
        "total_volume": 10_000,
    }
    report = render_report(data, rec)
    assert "BTC Market Snapshot" in report
    assert "Recommended action" in report
    assert "Test reason" in report
