"""Minimal HTTP server with a web UI for viewing Bitcoin market signals."""

from __future__ import annotations

import argparse
import json
import threading
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, List, Tuple

from .analyzer import Signal, generate_signal
from .data import MarketDataError, PricePoint, fetch_price_points

# Simple HTML template with inline styling/JS to keep dependencies minimal.
TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>BTC 观察面板</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #0d1117; color: #e6edf3; }
    header { padding: 1rem 1.5rem; background: #161b22; border-bottom: 1px solid #21262d; }
    main { padding: 1.5rem; max-width: 900px; margin: 0 auto; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1.25rem; box-shadow: 0 8px 24px rgba(0,0,0,0.25); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem; }
    .metric { padding: 0.75rem; border-radius: 10px; background: #0d1117; border: 1px solid #30363d; }
    .metric h3 { margin: 0 0 0.35rem; font-size: 0.95rem; color: #8b949e; }
    .metric p { margin: 0; font-size: 1.15rem; font-weight: 600; }
    .sentiment { display: inline-block; padding: 0.35rem 0.65rem; border-radius: 8px; font-weight: 700; letter-spacing: 0.02em; }
    .sentiment.bull { background: rgba(46, 160, 67, 0.2); color: #3fb950; }
    .sentiment.bear { background: rgba(248, 81, 73, 0.2); color: #f85149; }
    .sentiment.neutral { background: rgba(201, 148, 0, 0.2); color: #e3b341; }
    .muted { color: #8b949e; }
    .error { color: #f85149; margin-top: 0.75rem; }
    footer { margin-top: 1.5rem; font-size: 0.9rem; color: #8b949e; }
    button { background: #238636; color: white; border: none; padding: 0.55rem 1rem; border-radius: 8px; cursor: pointer; font-weight: 600; }
    button:hover { background: #2ea043; }
  </style>
</head>
<body>
  <header>
    <h1>BTC 观察面板</h1>
    <p class="muted">基于公开数据与简易指标的参考提示，非投资建议。</p>
  </header>
  <main>
    <div class="card">
      <div id="status" class="muted">正在加载数据…</div>
      <div style="display:flex; align-items:center; gap:0.75rem; margin-top: 0.75rem; flex-wrap: wrap;">
        <span id="sentiment" class="sentiment neutral">—</span>
        <div id="headline"></div>
        <button id="refresh">手动刷新</button>
      </div>
      <div class="grid">
        <div class="metric"><h3>现价</h3><p id="price">—</p></div>
        <div class="metric"><h3>短均 (20)</h3><p id="ma_short">—</p></div>
        <div class="metric"><h3>长均 (60)</h3><p id="ma_long">—</p></div>
        <div class="metric"><h3>波动率</h3><p id="volatility">—</p></div>
        <div class="metric"><h3>近两笔变动</h3><p id="change_pct">—</p></div>
        <div class="metric"><h3>最近更新时间</h3><p id="timestamp">—</p></div>
      </div>
      <p id="caution" class="muted" style="margin-top:1rem;"></p>
      <div id="error" class="error" aria-live="polite"></div>
    </div>
    <footer>⚠️ 以上内容基于公开数据与简单指标，仅供参考，不构成投资建议；数字资产波动大，请自行评估风险。</footer>
  </main>
  <script>
    async function loadSignal() {
      const status = document.getElementById('status');
      const errorBox = document.getElementById('error');
      status.textContent = '正在更新…';
      errorBox.textContent = '';
      try {
        const res = await fetch('/api/signal');
        if (!res.ok) {
          const message = await res.text();
          throw new Error(message || '请求失败');
        }
        const data = await res.json();
        updateView(data);
        status.textContent = '最近一次成功刷新';
      } catch (err) {
        status.textContent = '刷新失败';
        errorBox.textContent = err.message;
      }
    }

    function updateView(data) {
      const sentimentEl = document.getElementById('sentiment');
      sentimentEl.textContent = data.sentiment;
      sentimentEl.className = 'sentiment ' + (data.sentiment === '偏多' ? 'bull' : data.sentiment === '偏空' ? 'bear' : 'neutral');
      document.getElementById('headline').textContent = data.headline;
      document.getElementById('price').textContent = '$' + data.price.toFixed(2);
      document.getElementById('ma_short').textContent = '$' + data.short_ma.toFixed(2);
      document.getElementById('ma_long').textContent = '$' + data.long_ma.toFixed(2);
      document.getElementById('volatility').textContent = data.volatility.toFixed(2);
      document.getElementById('change_pct').textContent = data.change_pct.toFixed(2) + '%';
      document.getElementById('timestamp').textContent = data.timestamp;
      document.getElementById('caution').textContent = data.caution;
    }

    document.getElementById('refresh').addEventListener('click', loadSignal);
    loadSignal();
    setInterval(loadSignal, 60_000);
  </script>
</body>
</html>
"""


FetchFunc = Callable[[float], List[PricePoint]]


def _serialize_signal(signal: Signal) -> dict:
    details = signal.details
    return {
        "price": details["price"],
        "short_ma": details["short_ma"],
        "long_ma": details["long_ma"],
        "volatility": details["volatility"],
        "change_pct": details["change_pct"],
        "sentiment": signal.sentiment,
        "headline": signal.headline,
        "caution": signal.caution,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def build_signal_payload(hours_param: float | str, fetcher: FetchFunc) -> Tuple[int, dict]:
    """Generate JSON payload for /api/signal."""

    try:
        hours = float(hours_param)
    except (TypeError, ValueError):
        return 400, {"error": "hours 参数必须是数字"}

    try:
        points = fetcher(hours=hours)
        signal = generate_signal(points)
    except (MarketDataError, ValueError) as exc:
        return 400, {"error": str(exc)}

    return 200, _serialize_signal(signal)


def create_handler(fetcher: FetchFunc, default_hours: float):
    """Create a request handler class bound to the provided fetcher."""

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/signal":
                query = urllib.parse.parse_qs(parsed.query)
                hours_param = query.get("hours", [default_hours])[0]
                status, payload = build_signal_payload(hours_param, fetcher)
                self._send_json(payload, status)
                return

            if parsed.path == "/":
                self._send_html(TEMPLATE)
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args):  # noqa: A003
            # Quieter logging for CLI usage
            return

        def _send_json(self, payload: dict, status: int = 200):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str):
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return DashboardHandler


def serve(host: str = "127.0.0.1", port: int = 8000, hours: float = 6.0, fetcher: FetchFunc | None = None):
    """Start the dashboard HTTP server."""

    fetch_prices = fetcher or fetch_price_points
    handler_cls = create_handler(fetch_prices, hours)
    server = ThreadingHTTPServer((host, port), handler_cls)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main():
    parser = argparse.ArgumentParser(description="启动 BTC 观察面板 Web 服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--hours", type=float, default=6.0, help="请求过去多少小时的数据 (默认6小时)")
    args = parser.parse_args()

    server = serve(host=args.host, port=args.port, hours=args.hours)
    print(f"BTC 观察面板已启动: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止服务器…")
        server.shutdown()


if __name__ == "__main__":
    main()
