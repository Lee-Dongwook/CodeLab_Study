import json
import unittest
from datetime import date
from urllib.parse import parse_qs, urlparse

from app.data_sources.dart import DartDisclosureClient, DartDisclosureQuery
from app.models.domain import DomesticCandidate, SourceRecord
from app.models.errors import DartApiError, PublicDataUnavailableError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class DartDisclosureClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request_url = ""

    def _opener(self, request_url: str, timeout: int) -> FakeResponse:
        self.request_url = request_url
        return FakeResponse(
            {
                "status": "000",
                "message": "정상",
                "list": [
                    {
                        "corp_name": "테스트기업",
                        "stock_code": "005940",
                        "report_nm": "사업 관련 공시",
                        "rcept_no": "20200117000559",
                        "flr_nm": "테스트기업",
                        "rcept_dt": "20200117",
                    },
                    {
                        "corp_name": "다른기업",
                        "stock_code": "000001",
                        "report_nm": "다른 공시",
                        "rcept_no": "20200117000560",
                        "flr_nm": "다른기업",
                        "rcept_dt": "20200117",
                    },
                ],
            }
        )

    def test_sends_required_key_and_optional_query_parameters(self) -> None:
        client = DartDisclosureClient("test-api-key", opener=self._opener)
        client.list_disclosures(DartDisclosureQuery(bgn_de=date(2020, 1, 17), end_de=date(2020, 1, 17), corp_cls="Y"))

        params = parse_qs(urlparse(self.request_url).query)
        self.assertEqual(params["crtfc_key"], ["test-api-key"])
        self.assertEqual(params["bgn_de"], ["20200117"])
        self.assertEqual(params["end_de"], ["20200117"])
        self.assertEqual(params["corp_cls"], ["Y"])

    def test_filters_response_by_candidate_stock_code(self) -> None:
        client = DartDisclosureClient("test-api-key", opener=self._opener)
        candidate = DomesticCandidate(
            "테스트기업", "005940", "KRX", "COMMON_STOCK", "사업", "direct", "근거", (_source(),)
        )

        items = client.get_candidate_disclosures(candidate, query=DartDisclosureQuery(), limit=3)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "사업 관련 공시")
        self.assertEqual(items[0].published_at, date(2020, 1, 17))
        self.assertIn("rcpNo=20200117000559", items[0].url)

    def test_raises_error_for_dart_error_response(self) -> None:
        client = DartDisclosureClient("test-api-key", opener=lambda *_args, **_kwargs: FakeResponse({"status": "010", "message": "등록되지 않은 키"}))

        with self.assertRaises(DartApiError):
            client.list_disclosures(DartDisclosureQuery())

    def test_returns_empty_list_when_dart_has_no_matching_disclosures(self) -> None:
        client = DartDisclosureClient(
            "test-api-key",
            opener=lambda *_args, **_kwargs: FakeResponse(
                {"status": "013", "message": "조회된 데이타가 없습니다."}
            ),
        )

        self.assertEqual(client.list_disclosures(DartDisclosureQuery()), ())

    def test_rejects_empty_api_key(self) -> None:
        with self.assertRaises(PublicDataUnavailableError):
            DartDisclosureClient(" ")


def _source() -> SourceRecord:
    return SourceRecord("test", "테스트", "테스트", "https://example.test", "company_official")
