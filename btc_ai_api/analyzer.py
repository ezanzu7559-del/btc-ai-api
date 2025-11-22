"""Signal generation utilities for Bitcoin price data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .data import PricePoint
from .indicators import moving_average, price_change, volatility


@dataclass
class Signal:
    sentiment: str
    headline: str
    details: Dict[str, float]
    caution: str


def generate_signal(points: List[PricePoint], short_window: int = 20, long_window: int = 60) -> Signal:
    if len(points) < long_window:
        raise ValueError("Not enough data to compute signals")

    prices = [p.price for p in points]
    short_ma = moving_average(prices, short_window)
    long_ma = moving_average(prices, long_window)
    vol = volatility(points, window=min(len(points), 60))
    change_pct = price_change(points)

    sentiment = "中性"
    headline = "价格信号不明显"

    if short_ma > long_ma * 1.002 and change_pct > 0:
        sentiment = "偏多"
        headline = "短期均线上穿长期均线，动能向上"
    elif short_ma < long_ma * 0.998 and change_pct < 0:
        sentiment = "偏空"
        headline = "短期均线下穿长期均线，注意回调"

    if vol > (0.01 * long_ma):
        headline += "；波动率升高，需控制仓位"

    caution = (
        "⚠️ 以上信号基于公开数据与简单指标，仅供参考，不构成投资建议；"
        "数字资产波动大，请自行评估风险。"
    )

    return Signal(
        sentiment=sentiment,
        headline=headline,
        details={
            "price": prices[-1],
            "short_ma": short_ma,
            "long_ma": long_ma,
            "volatility": vol,
            "change_pct": change_pct,
        },
        caution=caution,
    )
