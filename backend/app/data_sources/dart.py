from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import urlopen

from app.config import load_project_env
from app.models.domain import DomesticCandidate, NewsDisclosureItem, SourceRecord
from app.models.errors import DartApiError, PublicDataUnavailableError

_LIST_API_URL = "https://opendart.fss.or.kr/api/list.json"
_FINANCIAL_ACCOUNTS_API_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
_DART_VIEWER_URL = "https://dart.fss.or.kr/dsaf001/main.do"


@dataclass(frozen=True)
class DartDisclosureQuery:
    """OpenDART 공시 목록 API의 선택 요청값."""

    bgn_de: date | None = None
    end_de: date | None = None
    corp_code: str | None = None
    last_reprt_at: bool | None = None
    pblntf_ty: str | None = None
    pblntf_detail_ty: str | None = None
    corp_cls: str | None = None
    sort: str | None = "date"
    sort_mth: str | None = "desc"
    page_no: int = 1
    page_count: int = 100

    def to_params(self) -> dict[str, str]:
        params: dict[str, str] = {
            "page_no": str(self.page_no),
            "page_count": str(self.page_count),
        }
        optional_values = {
            "bgn_de": self.bgn_de.strftime("%Y%m%d") if self.bgn_de else None,
            "end_de": self.end_de.strftime("%Y%m%d") if self.end_de else None,
            "corp_code": self.corp_code,
            "last_reprt_at": "Y" if self.last_reprt_at else None,
            "pblntf_ty": self.pblntf_ty,
            "pblntf_detail_ty": self.pblntf_detail_ty,
            "corp_cls": self.corp_cls,
            "sort": self.sort,
            "sort_mth": self.sort_mth,
        }
        params.update({key: value for key, value in optional_values.items() if value is not None})
        return params


@dataclass(frozen=True)
class DartCompanyOverview:
    corp_code: str
    corp_name: str
    stock_code: str | None
    industry_code: str | None
    homepage_url: str | None
    ir_url: str | None


@dataclass(frozen=True)
class DartFinancialMetrics:
    revenue_growth: float | None
    operating_margin: float | None
    financial_period: str | None
    source: SourceRecord


class DartDisclosureClient:
    """OpenDART 공시 목록 API 어댑터.

    API 키는 환경변수에서만 읽으며, 로그나 응답에 포함하지 않는다.
    """

    def __init__(
        self,
        api_key: str,
        *,
        opener: Callable[..., Any] = urlopen,
        timeout_seconds: int = 10,
    ) -> None:
        if not api_key.strip():
            raise PublicDataUnavailableError("DART_API_KEY 환경변수가 설정되지 않았습니다.")
        self._api_key = api_key
        self._opener = opener
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(cls) -> "DartDisclosureClient":
        load_project_env()
        api_key = os.getenv("DART_API_KEY", "")
        return cls(api_key)

    def list_disclosures(self, query: DartDisclosureQuery) -> Sequence[Mapping[str, Any]]:
        params = {"crtfc_key": self._api_key, **query.to_params()}
        request_url = f"{_LIST_API_URL}?{urlencode(params)}"
        try:
            with self._opener(request_url, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as error:
            raise DartApiError("OpenDART 공시 목록을 조회하지 못했습니다.") from error

        # OpenDART는 조회 조건에 맞는 공시가 없을 때도 HTTP 200과 상태 코드
        # 013을 반환한다. 이는 연결 실패가 아니라 정상적인 빈 조회 결과다.
        if payload.get("status") == "013":
            return ()

        if payload.get("status") != "000":
            message = payload.get("message", "알 수 없는 OpenDART 오류")
            raise DartApiError(f"OpenDART 요청 실패: {message}")

        disclosures = payload.get("list", [])
        if not isinstance(disclosures, list):
            raise DartApiError("OpenDART 응답의 list 형식이 올바르지 않습니다.")
        return disclosures

    def get_company_overview(self, corp_code: str) -> DartCompanyOverview:
        params = {"crtfc_key": self._api_key, "corp_code": corp_code}
        request_url = f"https://opendart.fss.or.kr/api/company.json?{urlencode(params)}"
        try:
            with self._opener(request_url, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as error:
            raise DartApiError("OpenDART 기업개황을 조회하지 못했습니다.") from error

        if payload.get("status") != "000":
            message = payload.get("message", "알 수 없는 OpenDART 오류")
            raise DartApiError(f"OpenDART 요청 실패: {message}")
        return DartCompanyOverview(
            corp_code=corp_code,
            corp_name=str(payload.get("corp_name") or ""),
            stock_code=_blank_to_none(payload.get("stock_code")),
            industry_code=_blank_to_none(payload.get("induty_code")),
            homepage_url=_normalize_url(_blank_to_none(payload.get("hm_url"))),
            ir_url=_normalize_url(_blank_to_none(payload.get("ir_url"))),
        )

    def get_latest_annual_financial_metrics(self, corp_code: str) -> DartFinancialMetrics | None:
        """최근 확정 사업보고서의 연결 기준 매출·영업이익을 사용한다."""
        for business_year in range(date.today().year - 1, date.today().year - 4, -1):
            payload = self._request_json(
                _FINANCIAL_ACCOUNTS_API_URL,
                {"corp_code": corp_code, "bsns_year": str(business_year), "reprt_code": "11011"},
                "OpenDART 재무제표를 조회하지 못했습니다.",
            )
            if payload.get("status") == "013":
                continue
            if payload.get("status") != "000":
                continue

            accounts = payload.get("list", [])
            if not isinstance(accounts, list):
                continue
            revenue = _find_account(accounts, "매출액")
            operating_income = _find_account(accounts, "영업이익")
            if revenue is None or operating_income is None:
                continue
            current_revenue, previous_revenue = revenue
            current_operating_income, _ = operating_income
            if current_revenue is None:
                continue
            period = f"{business_year} 사업연도 (연결 기준)"
            source = SourceRecord(
                source_id=f"dart:financial:{corp_code}:{business_year}",
                title=f"OpenDART 단일회사 주요계정 - {business_year} 사업연도",
                publisher="OpenDART",
                url="https://opendart.fss.or.kr/disclosureinfo/fnltt/singlacnt/main.do",
                source_type="dart",
            )
            return DartFinancialMetrics(
                revenue_growth=(current_revenue / previous_revenue - 1) * 100 if previous_revenue else None,
                operating_margin=current_operating_income / current_revenue * 100,
                financial_period=period,
                source=source,
            )
        return None

    def _request_json(self, base_url: str, params: Mapping[str, str], error_message: str) -> Mapping[str, Any]:
        request_url = f"{base_url}?{urlencode({'crtfc_key': self._api_key, **params})}"
        try:
            with self._opener(request_url, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as error:
            raise DartApiError(error_message) from error
        if not isinstance(payload, dict):
            raise DartApiError("OpenDART 응답 형식이 올바르지 않습니다.")
        return payload

    def get_candidate_disclosures(
        self,
        candidate: DomesticCandidate,
        *,
        query: DartDisclosureQuery,
        limit: int = 3,
    ) -> tuple[NewsDisclosureItem, ...]:
        matching = [
            disclosure
            for disclosure in self.list_disclosures(query)
            if disclosure.get("stock_code") == candidate.code
        ]
        return tuple(self._to_item(candidate.code, disclosure) for disclosure in matching[:limit])

    @staticmethod
    def _to_item(candidate_code: str, disclosure: Mapping[str, Any]) -> NewsDisclosureItem:
        receipt_number = str(disclosure.get("rcept_no", ""))
        if not receipt_number:
            raise DartApiError("OpenDART 응답에 접수번호가 없습니다.")

        receipt_date = _parse_dart_date(disclosure.get("rcept_dt"))
        checked_at = datetime.now()
        title = str(disclosure.get("report_nm", "공시 제목 미확인"))
        publisher = str(disclosure.get("flr_nm") or disclosure.get("corp_name") or "DART")
        viewer_url = f"{_DART_VIEWER_URL}?{urlencode({'rcpNo': receipt_number})}"
        source = SourceRecord(
            source_id=f"dart:{receipt_number}",
            title=title,
            publisher=publisher,
            url=viewer_url,
            source_type="dart",
            published_at=receipt_date,
            checked_at=checked_at,
        )
        return NewsDisclosureItem(
            candidate_code=candidate_code,
            category="disclosure",
            title=title,
            summary=f"{disclosure.get('corp_name', '')} 공시",
            url=viewer_url,
            published_at=receipt_date,
            checked_at=checked_at,
            source=source,
        )


def _parse_dart_date(value: object) -> date | None:
    if not isinstance(value, str) or len(value) != 8:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


def _blank_to_none(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_url(value: str | None) -> str | None:
    if value is None:
        return None
    return value if value.startswith(("http://", "https://")) else f"https://{value}"


def _find_account(accounts: Sequence[Mapping[str, Any]], name: str) -> tuple[float | None, float | None] | None:
    # 연결 재무제표(CFS)를 우선한다. 매출액 명칭이 다른 업종은 이후 확장한다.
    matching = [account for account in accounts if account.get("account_nm") == name]
    account = next((item for item in matching if item.get("fs_div") == "CFS"), None)
    account = account or (matching[0] if matching else None)
    if account is None:
        return None
    return _to_number(account.get("thstrm_amount")), _to_number(account.get("frmtrm_amount"))


def _to_number(value: object) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
