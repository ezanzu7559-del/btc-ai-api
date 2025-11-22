"""Indicator calculations for Bitcoin market data."""

from __future__ import annotations

from statistics import mean, stdev
from typing import Iterable, List

from .data import PricePoint


def moving_average(prices: Iterable[float], window: int) -> float:
    series: List[float] = list(prices)
    if window <= 0:
        raise ValueError("window must be positive")
    if len(series) < window:
        raise ValueError("not enough data points for the requested window")
    return mean(series[-window:])


def price_change(points: List[PricePoint]) -> float:
    if len(points) < 2:
        return 0.0
    start = points[-2].price
    end = points[-1].price
    if start == 0:
        return 0.0
    return (end - start) / start * 100


def volatility(points: List[PricePoint], window: int = 30) -> float:
    if len(points) < window:
        return 0.0
    prices = [p.price for p in points[-window:]]
    return stdev(prices)
