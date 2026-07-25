import json
import unittest
from datetime import date

from app.data_sources.naver_market import NaverMarketDataClient


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class NaverMarketDataClientTests(unittest.TestCase):
    def _opener(self, request, timeout):
        if "realtime" in request.full_url:
            payload = {
                "result": {
                    "time": 1784964056292,
                    "areas": [{"datas": [{"nv": 10000, "eps": 1000, "bps": 5000, "countOfListedStock": 100}]}],
                }
            }
            return FakeResponse(json.dumps(payload, ensure_ascii=False).encode("cp949"))
        return FakeResponse(
            "[['날짜', '시가', '고가', '저가', '종가', '거래량'], ['20260721', 1, 1, 1, 10000, 100], ['20260722', 1, 1, 1, 11000, 300]]".encode()
        )

    def test_builds_market_snapshot_from_public_response(self) -> None:
        snapshot = NaverMarketDataClient(opener=self._opener).get_snapshot("000001")

        self.assertEqual(snapshot.close_price, 10000)
        self.assertEqual(snapshot.market_cap, 1000000)
        self.assertEqual(snapshot.per, 10)
        self.assertEqual(snapshot.pbr, 2)
        self.assertIsNone(snapshot.as_of)

    def test_parses_price_and_volume_series(self) -> None:
        points = NaverMarketDataClient(opener=self._opener).get_price_volume_points("000001", trading_days=60)

        self.assertEqual([(point.close_price, point.volume) for point in points], [(10000.0, 100), (11000.0, 300)])
