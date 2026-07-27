import json
import unittest
from datetime import date

from app.data_sources.krx_listed_securities import KRXListedSecuritiesClient
from app.models.errors import PublicDataUnavailableError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class KRXListedSecuritiesClientTests(unittest.TestCase):
    def test_identifies_only_common_stock_from_kospi_and_kosdaq(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append(request)
            if "stk_isu_base_info" in request.full_url:
                return FakeResponse({"OutBlock_1": [_row("005930", "삼성전자", "보통주"), _row("005935", "삼성전자우", "우선주")]})
            return FakeResponse({"OutBlock_1": [_row("123456", "테스트스팩", "보통주", security_group="투자회사")]})

        client = KRXListedSecuritiesClient("test-key", opener=opener, today=lambda: date(2026, 7, 24))

        self.assertTrue(client.is_eligible_common_stock("005930"))
        self.assertFalse(client.is_eligible_common_stock("005935"))
        # SPAC은 KRX 종목기본정보의 보통주 표기만으로는 구분할 수 없어, 명칭·증권구분도 함께 제외한다.
        self.assertFalse(client.is_eligible_common_stock("123456"))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].get_header("Auth_key"), "test-key")
        self.assertIn("basDd=20260724", calls[0].full_url)

    def test_rejects_missing_api_key(self) -> None:
        with self.assertRaises(PublicDataUnavailableError):
            KRXListedSecuritiesClient(" ")


def _row(code: str, name: str, stock_type: str, *, security_group: str = "주권") -> dict[str, str]:
    return {
        "ISU_SRT_CD": code,
        "ISU_ABBRV": name,
        "MKT_TP_NM": "KOSPI",
        "SECUGRP_NM": security_group,
        "KIND_STKCERT_TP_NM": stock_type,
    }
