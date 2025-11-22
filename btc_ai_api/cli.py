"""Command-line interface for the Bitcoin market assistant."""
"""Command line interface for the Bitcoin watcher."""

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
import time
from datetime import datetime

from .analyzer import generate_signal
from .data import MarketDataError, fetch_price_points


def format_output(signal):
    details = signal.details
    lines = [
        f"[{datetime.utcnow().isoformat()}Z] 现价: ${details['price']:.2f}",
        f"短均(20): ${details['short_ma']:.2f} | 长均(60): ${details['long_ma']:.2f}",
        f"变动: {details['change_pct']:.2f}% | 波动率(近60): {details['volatility']:.2f}",
        f"信号: {signal.sentiment} — {signal.headline}",
        signal.caution,
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="实时观察比特币行情并给出简单信号")
    parser.add_argument("--hours", type=float, default=6.0, help="请求过去多少小时的数据 (默认6小时)")
    parser.add_argument("--interval", type=int, default=60, help="轮询间隔，单位秒 (默认60)")
    parser.add_argument("--iterations", type=int, default=1, help="循环次数，为0时持续运行")
    args = parser.parse_args()

    iteration = 0
    while True:
        try:
            points = fetch_price_points(hours=args.hours)
            signal = generate_signal(points)
            print(format_output(signal))
        except MarketDataError as exc:
            print(f"数据获取失败: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"处理数据失败: {exc}")

        iteration += 1
        if args.iterations and iteration >= args.iterations:
            break

        time.sleep(max(10, args.interval))


if __name__ == "__main__":
    main()
