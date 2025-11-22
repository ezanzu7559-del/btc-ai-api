import unittest
from datetime import datetime, timezone

from btc_ai_api.data import PricePoint
from btc_ai_api.indicators import moving_average, price_change, volatility


class IndicatorTests(unittest.TestCase):
    def test_moving_average(self):
        self.assertEqual(moving_average([1, 2, 3, 4], 2), 3.5)

    def test_price_change(self):
        pts = [
            PricePoint(datetime(2024, 1, 1, tzinfo=timezone.utc), 100),
            PricePoint(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 110),
        ]
        self.assertEqual(price_change(pts), 10)

    def test_volatility_handles_insufficient_data(self):
        pts = [PricePoint(datetime(2024, 1, 1, tzinfo=timezone.utc), price) for price in [100, 101]]
        self.assertEqual(volatility(pts, window=5), 0)


if __name__ == "__main__":
    unittest.main()
