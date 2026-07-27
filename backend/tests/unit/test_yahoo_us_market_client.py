import unittest

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

from app.data_sources.us_market import YahooUSMarketClient


class FakeTicker:
    info = {"longName": "Example ETF", "quoteType": "ETF"}

    def history(self, **_kwargs):
        return pd.DataFrame(
            {"Close": [100.0, 110.0], "Volume": [1000, 2500]},
            index=pd.to_datetime(["2026-07-23", "2026-07-24"]),
        )


@unittest.skipIf(pd is None, "pandas가 설치된 환경에서 실행")
class YahooUSMarketClientTests(unittest.TestCase):
    def test_builds_recent_snapshot_from_yfinance_history(self) -> None:
        client = YahooUSMarketClient(ticker_factory=lambda ticker: FakeTicker())

        snapshot = client.get_recent_snapshot("robo")

        self.assertEqual(snapshot.ticker, "ROBO")
        self.assertEqual(snapshot.name, "Example ETF")
        self.assertEqual(snapshot.instrument_type, "ETF")
        self.assertEqual(snapshot.close_price, 110.0)
        self.assertAlmostEqual(snapshot.daily_change_percent, 10.0)
        self.assertEqual(snapshot.volume, 2500)
        self.assertAlmostEqual(snapshot.volume_change_percent, 150.0)
        self.assertEqual(snapshot.as_of.isoformat(), "2026-07-24")
