"""Analysis helpers for Bitcoin market data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Recommendation:
    action: str
    reasons: List[str]

    def format(self) -> str:
        bullets = "\n".join(f"- {reason}" for reason in self.reasons)
        return f"Recommended action: {self.action}\n{bullets}"


def summarize_trend(market_data: Dict[str, float]) -> Recommendation:
    """
    Create a simple recommendation based on short-term and mid-term changes.

    The logic is intentionally conservative: it highlights strength when both
    short-term and daily trends are positive and emphasizes caution when both
    are negative.
    """

    one_hour = market_data.get("price_change_percentage_1h_in_currency", 0.0)
    day = market_data.get("price_change_percentage_24h_in_currency", 0.0)
    week = market_data.get("price_change_percentage_7d_in_currency", 0.0)

    reasons: List[str] = [
        f"1h change: {one_hour:+.2f}%",
        f"24h change: {day:+.2f}%",
        f"7d change: {week:+.2f}%",
    ]

    if one_hour > 0.25 and day > 0.5:
        action = "Consider buying"
        reasons.append("Momentum is positive across multiple timeframes.")
    elif one_hour < -0.25 and day < -0.5:
        action = "Consider reducing exposure"
        reasons.append("Downward pressure visible in short-term and daily moves.")
    else:
        action = "Hold / wait"
        reasons.append("Signals are mixed; waiting for clarity may reduce risk.")

    if week > 5:
        reasons.append("Strong weekly performance suggests upward trend.")
    elif week < -5:
        reasons.append("Sustained weekly drawdown indicates elevated downside risk.")

    return Recommendation(action=action, reasons=reasons)


def render_report(market_data: Dict[str, float], recommendation: Recommendation) -> str:
    """Render a user-friendly report."""

    lines = [
        "BTC Market Snapshot",
        f"Fetched at: {market_data['fetched_at']}",
        f"Price: ${market_data['price']:,.2f}",
        f"24h High / Low: ${market_data['high_24h']:,.2f} / ${market_data['low_24h']:,.2f}",
        f"Market Cap: ${market_data['market_cap']:,.0f}",
        f"24h Volume: ${market_data['total_volume']:,.0f}",
        "",
        recommendation.format(),
    ]
    return "\n".join(lines)
