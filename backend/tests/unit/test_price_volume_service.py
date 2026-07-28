import unittest
from datetime import date

from app.models.domain import PriceVolumePoint
from app.services.price_volume_service import (
    calculate_price_volume_metrics,
    calculate_recent_daily_change_rates,
    calculate_recent_weekly_monthly_change_rates,
)


class PriceVolumeMetricsTests(unittest.TestCase):
    def test_calculates_weekly_and_monthly_change_rates_from_trading_days(self) -> None:
        points = [
            PriceVolumePoint(date(2026, 7, day), 100 + index * 10, 10)
            for index, day in enumerate(range(1, 22))
        ]

        weekly_change, monthly_change = calculate_recent_weekly_monthly_change_rates(points)

        self.assertAlmostEqual(weekly_change, (300 / 250 - 1) * 100)
        self.assertAlmostEqual(monthly_change, 200.0)

    def test_marks_weekly_and_monthly_changes_unavailable_with_short_series(self) -> None:
        weekly_change, monthly_change = calculate_recent_weekly_monthly_change_rates(
            [PriceVolumePoint(date(2026, 7, day), 100, 10) for day in range(1, 6)]
        )

        self.assertIsNone(weekly_change)
        self.assertIsNone(monthly_change)

    def test_calculates_previous_and_current_trading_day_change_rates(self) -> None:
        previous_day_change, current_day_change = calculate_recent_daily_change_rates(
            [
                PriceVolumePoint(date(2026, 7, 1), 100, 10),
                PriceVolumePoint(date(2026, 7, 2), 110, 10),
                PriceVolumePoint(date(2026, 7, 3), 99, 10),
            ]
        )

        self.assertAlmostEqual(previous_day_change, 10.0)
        self.assertAlmostEqual(current_day_change, -10.0)

    def test_marks_previous_day_change_unavailable_when_series_is_too_short(self) -> None:
        previous_day_change, current_day_change = calculate_recent_daily_change_rates(
            [
                PriceVolumePoint(date(2026, 7, 1), 100, 10),
                PriceVolumePoint(date(2026, 7, 2), 110, 10),
            ]
        )

        self.assertIsNone(previous_day_change)
        self.assertAlmostEqual(current_day_change, 10.0)

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
