"""BTC AI API: lightweight Bitcoin market assistant."""

from .analysis import Recommendation, render_report, summarize_trend
from .client import MarketDataClient

__all__ = [
    "MarketDataClient",
    "Recommendation",
    "render_report",
    "summarize_trend",
]
"""Lightweight Bitcoin market watcher and signal generator."""

__all__ = ["__version__"]
__version__ = "0.1.0"
