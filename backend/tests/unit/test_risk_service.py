import unittest
from datetime import date

from app.models.domain import RiskItem, SourceRecord
from app.services.risk_service import validate_risk_items


def source() -> SourceRecord:
    return SourceRecord("risk", "공시", "테스트", "https://example.test/risk", "dart", date(2026, 7, 1))


class RiskItemTests(unittest.TestCase):
    def test_deduplicates_supported_risk_items(self) -> None:
        item = RiskItem("000001", "company", "공급 계약 변동 가능성", (source(),))

        self.assertEqual(validate_risk_items((item, item)), (item,))

    def test_rejects_risk_item_without_source(self) -> None:
        item = RiskItem("000001", "company", "공급 계약 변동 가능성", ())

        with self.assertRaises(ValueError):
            validate_risk_items((item,))

    def test_rejects_recommendation_language(self) -> None:
        item = RiskItem("000001", "company", "매수 기회로 볼 수 있음", (source(),))

        with self.assertRaises(ValueError):
            validate_risk_items((item,))
