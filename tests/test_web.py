import unittest
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer
from threading import Thread
from urllib.request import urlopen

from btc_ai_api.data import PricePoint
from btc_ai_api.web import build_signal_payload, create_handler, serve


class WebTestCase(unittest.TestCase):
    def setUp(self):
        self.points = self._sample_points()

    def _sample_points(self):
        base = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        prices = [44000 + i * 5 for i in range(80)]
        return [PricePoint(time=base + timedelta(minutes=i), price=price) for i, price in enumerate(prices)]

    def test_build_signal_payload_contains_expected_keys(self):
        status, data = build_signal_payload(6, lambda hours: self.points)
        self.assertEqual(status, 200)
        self.assertTrue({"price", "short_ma", "long_ma", "volatility", "change_pct", "sentiment", "headline", "caution", "timestamp"} <= data.keys())

    def test_build_signal_payload_handles_error(self):
        status, data = build_signal_payload(6, lambda hours: (_ for _ in ()).throw(ValueError("boom")))
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "boom")

    def test_http_handler_serves_dashboard(self):
        fetcher = lambda hours: self.points
        handler_cls = create_handler(fetcher, 6)
        server = HTTPServer(("127.0.0.1", 0), handler_cls)
        thread = Thread(target=server.handle_request)
        thread.start()
        port = server.server_address[1]
        resp = urlopen(f"http://127.0.0.1:{port}/")
        body = resp.read().decode("utf-8")
        server.server_close()
        thread.join()
        self.assertIn("BTC 观察面板", body)

    def test_serve_starts_background_server(self):
        server = serve(host="127.0.0.1", port=0, fetcher=lambda hours: self.points)
        port = server.server_address[1]
        resp = urlopen(f"http://127.0.0.1:{port}/api/signal")
        self.assertEqual(resp.status, 200)
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    unittest.main()
