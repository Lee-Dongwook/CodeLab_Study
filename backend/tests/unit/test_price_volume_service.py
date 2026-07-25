import unittest
from datetime import date

from app.models.domain import PriceVolumePoint
from app.services.price_volume_service import calculate_price_volume_metrics


class PriceVolumeMetricsTests(unittest.TestCase):
    def test_calculates_metrics_using_caller_supplied_policy(self) -> None:
        result = calculate_price_volume_metrics(
            "000001",
            [
                PriceVolumePoint(date(2026, 7, 1), 100, 10),
                PriceVolumePoint(date(2026, 7, 2), 110, 10),
                PriceVolumePoint(date(2026, 7, 3), 121, 30),
                PriceVolumePoint(date(2026, 7, 4), 133.1, 30),
            ],
            analysis_period="테스트 4거래일",
            annualization_days=252,
            volume_surge_threshold=2,
        )

        self.assertAlmostEqual(result.period_return, 33.1)
        self.assertAlmostEqual(result.volume_change, 200.0)
        self.assertTrue(result.volume_surge)
        self.assertIsNotNone(result.volatility)

    def test_marks_insufficient_series_as_unavailable(self) -> None:
        result = calculate_price_volume_metrics(
            "000001",
            [PriceVolumePoint(date(2026, 7, 1), 100, 10)],
            analysis_period="테스트",
            annualization_days=252,
            volume_surge_threshold=2,
        )

        self.assertIsNone(result.period_return)
        self.assertIsNone(result.volume_surge)
