from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.config import load_project_env
from app.models.domain import SourceRecord
from app.models.errors import PublicDataUnavailableError

_API_BASE_URL = "https://data-dbg.krx.co.kr/svc/apis/sto"
_MARKET_ENDPOINTS = {
    "KOSPI": "stk_isu_base_info",
    "KOSDAQ": "ksq_isu_base_info",
}


@dataclass(frozen=True)
class KRXListedSecurity:
    """KRX 종목기본정보에서 확인한 상장 증권의 최소 식별 정보."""

    code: str
    name: str
    market: str
    security_group: str
    stock_certificate_type: str

    @property
    def is_common_stock(self) -> bool:
        normalized_name = self.name.replace(" ", "").upper()
        normalized_group = self.security_group.replace(" ", "")
        return (
            self.stock_certificate_type == "보통주"
            and "스팩" not in normalized_name
            and "SPAC" not in normalized_name
            and "투자회사" not in normalized_group
        )


class KRXListedSecuritiesClient:
    """KRX 종목기본정보 API로 KOSPI·KOSDAQ 상장 보통주를 판별한다.

    ETF·ETN은 별도 증권상품 API 대상이고, 우선주·SPAC 등은 종목기본정보의
    주식종류 또는 증권구분으로 제외한다. API 키는 요청 헤더에만 담는다.
    """

    def __init__(
        self,
        api_key: str,
        *,
        opener: Callable[..., Any] = urlopen,
        timeout_seconds: int = 20,
        today: Callable[[], date] = date.today,
    ) -> None:
        if not api_key.strip():
            raise PublicDataUnavailableError("KRX_API_KEY 환경변수가 설정되지 않았습니다.")
        self._api_key = api_key.strip()
        self._opener = opener
        self._timeout_seconds = timeout_seconds
        self._today = today
        self._securities: dict[str, KRXListedSecurity] | None = None
        self._loaded_as_of: date | None = None

    @classmethod
    def from_environment(cls) -> "KRXListedSecuritiesClient":
        load_project_env()
        return cls(os.getenv("KRX_API_KEY", ""))

    def find_by_code(self, stock_code: str) -> KRXListedSecurity | None:
        return self._load_securities().get(stock_code.strip())

    def is_eligible_common_stock(self, stock_code: str) -> bool:
        security = self.find_by_code(stock_code)
        return security is not None and security.is_common_stock

    def source_for(self, stock_code: str) -> SourceRecord:
        security = self.find_by_code(stock_code)
        if security is None:
            raise PublicDataUnavailableError("KRX 상장 종목 목록에서 종목을 확인하지 못했습니다.")
        return SourceRecord(
            source_id=f"krx:listed-security:{security.code}:{self._loaded_as_of}",
            title=f"KRX 종목기본정보 - {security.name} ({security.market})",
            publisher="한국거래소(KRX)",
            url="https://data.krx.co.kr/",
            source_type="krx",
            published_at=self._loaded_as_of,
        )

    def _load_securities(self) -> dict[str, KRXListedSecurity]:
        if self._securities is not None:
            return self._securities

        latest_error: PublicDataUnavailableError | None = None
        # 휴장일에는 직전 영업일 데이터가 필요하므로 최근 10일을 순차적으로 시도한다.
        for offset in range(10):
            base_date = self._today() - timedelta(days=offset)
            try:
                rows = [
                    security
                    for market in _MARKET_ENDPOINTS
                    for security in self._request_market(market, base_date)
                ]
            except PublicDataUnavailableError as error:
                latest_error = error
                continue
            if rows:
                self._securities = {security.code: security for security in rows}
                self._loaded_as_of = base_date
                return self._securities

        raise latest_error or PublicDataUnavailableError("KRX 상장 종목 목록을 조회하지 못했습니다.")

    def _request_market(self, market: str, base_date: date) -> tuple[KRXListedSecurity, ...]:
        endpoint = _MARKET_ENDPOINTS[market]
        request = Request(
            f"{_API_BASE_URL}/{endpoint}?{urlencode({'basDd': base_date.strftime('%Y%m%d')})}",
            headers={"AUTH_KEY": self._api_key, "Accept": "application/json"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 401:
                raise PublicDataUnavailableError(
                    "KRX API 인증 또는 서비스 이용 권한을 확인하지 못했습니다. "
                    "유가증권·코스닥 종목기본정보 API의 이용 신청 및 승인 상태를 확인해 주세요."
                ) from error
            raise PublicDataUnavailableError(f"KRX 종목기본정보 요청 실패(HTTP {error.code})") from error
        except (OSError, ValueError, UnicodeDecodeError) as error:
            raise PublicDataUnavailableError("KRX 종목기본정보를 조회하지 못했습니다.") from error

        if not isinstance(payload, Mapping):
            raise PublicDataUnavailableError("KRX 종목기본정보 응답 형식이 올바르지 않습니다.")
        if payload.get("respCode") not in (None, "000", "0", 0):
            raise PublicDataUnavailableError(
                f"KRX 종목기본정보 요청 실패: {payload.get('respMsg', '알 수 없는 오류')}"
            )
        raw_rows = payload.get("OutBlock_1", [])
        if not isinstance(raw_rows, list):
            raise PublicDataUnavailableError("KRX 종목기본정보의 OutBlock_1 형식이 올바르지 않습니다.")
        return tuple(
            security
            for row in raw_rows
            if isinstance(row, Mapping)
            if (security := _to_security(row, market)) is not None
        )


def _to_security(row: Mapping[str, object], market: str) -> KRXListedSecurity | None:
    code = str(row.get("ISU_SRT_CD") or "").strip()
    name = str(row.get("ISU_ABBRV") or row.get("ISU_NM") or "").strip()
    if not code or not name:
        return None
    return KRXListedSecurity(
        code=code,
        name=name,
        market=str(row.get("MKT_TP_NM") or market).strip(),
        security_group=str(row.get("SECUGRP_NM") or "").strip(),
        stock_certificate_type=str(row.get("KIND_STKCERT_TP_NM") or "").strip(),
    )
