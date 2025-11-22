"""Command-line interface for the Bitcoin market assistant."""

from __future__ import annotations

import argparse
import sys

from .analysis import render_report, summarize_trend
from .client import MarketDataClient


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time Bitcoin market assistant")
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in the output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    client = MarketDataClient()

    try:
        snapshot = client.fetch_bitcoin_snapshot()
    except Exception as exc:  # noqa: BLE001 - top-level CLI entry point
        print(f"Failed to retrieve market data: {exc}", file=sys.stderr)
        return 1

    recommendation = summarize_trend(snapshot)
    report = render_report(snapshot, recommendation)

    if args.no_color:
        print(report)
    else:
        print(_add_color(report))

    return 0


def _add_color(report: str) -> str:
    """Add minimal highlighting for better readability."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    lines = []
    for line in report.splitlines():
        if line.startswith("Price") or line.startswith("24h High"):
            lines.append(f"{CYAN}{line}{RESET}")
        elif line.startswith("Recommended action"):
            if "buy" in line.lower():
                color = GREEN
            elif "reduce" in line.lower():
                color = RED
            else:
                color = CYAN
            lines.append(f"{color}{line}{RESET}")
        else:
            lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
