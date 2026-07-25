from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.models.domain import PriceVolumePoint, SourceRecord
from app.models.errors import PublicDataUnavailableError

_QUOTE_URL = "https://polling.finance.naver.com/api/realtime"
_PRICE_URL = "https://api.finance.naver.com/siseJson.naver"


@dataclass(frozen=True)
class MarketSnapshot:
    close_price: int | None
    market_cap: int | None
    per: float | None
    pbr: float | None
    as_of: date | None
    source: SourceRecord


class NaverMarketDataClient:
    """공개 Naver Finance 응답을 MVP 시장 데이터 어댑터로 사용한다."""

    def __init__(self, *, opener: Callable[..., Any] = urlopen, timeout_seconds: int = 10) -> None:
        self._opener = opener
        self._timeout_seconds = timeout_seconds

    def get_snapshot(self, stock_code: str) -> MarketSnapshot:
        payload = self._get_json(f"{_QUOTE_URL}?{urlencode({'query': f'SERVICE_ITEM:{stock_code}'})}")
        try:
            item = payload["result"]["areas"][0]["datas"][0]
        except (KeyError, IndexError, TypeError) as error:
            raise PublicDataUnavailableError("시장 요약 데이터를 확인하지 못했습니다.") from error
        close = _to_int(item.get("nv"))
        shares = _to_int(item.get("countOfListedStock"))
        eps = _to_float(item.get("eps"))
        bps = _to_float(item.get("bps"))
        # 실시간 폴링 시각은 마지막 거래일과 다를 수 있으므로, 실제 기준일은
        # 일별 시계열의 마지막 거래일을 사용하는 호출부에서 설정한다.
        as_of = _parse_iso_date(item.get("localTradedAt"))
        return MarketSnapshot(
            close_price=close,
            market_cap=close * shares if close is not None and shares is not None else None,
            per=close / eps if close is not None and eps and eps > 0 else None,
            pbr=close / bps if close is not None and bps and bps > 0 else None,
            as_of=as_of,
            source=_market_source(stock_code, "종목 요약", as_of),
        )

    def get_price_volume_points(self, stock_code: str, *, trading_days: int = 60) -> tuple[PriceVolumePoint, ...]:
        end_date = date.today()
        start_date = end_date - timedelta(days=trading_days * 2)
        params = {
            "symbol": stock_code,
            "requestType": "1",
            "startTime": start_date.strftime("%Y%m%d"),
            "endTime": end_date.strftime("%Y%m%d"),
            "timeframe": "day",
        }
        raw = self._get_text(f"{_PRICE_URL}?{urlencode(params)}")
        try:
            rows = ast.literal_eval(raw.strip())
        except (SyntaxError, ValueError) as error:
            raise PublicDataUnavailableError("가격·거래량 시계열을 해석하지 못했습니다.") from error
        points = []
        for row in rows[1:] if isinstance(rows, list) else []:
            if not isinstance(row, list) or len(row) < 6:
                continue
            try:
                points.append(PriceVolumePoint(datetime.strptime(str(row[0]), "%Y%m%d").date(), float(row[4]), int(row[5])))
            except (TypeError, ValueError):
                continue
        return tuple(points[-trading_days:])

    def _get_json(self, url: str) -> dict[str, Any]:
        try:
            return json.loads(self._get_text(url))
        except (ValueError, TypeError) as error:
            raise PublicDataUnavailableError("시장 데이터 응답을 해석하지 못했습니다.") from error

    def _get_text(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (research-mvp)"})
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                body = response.read()
        except OSError as error:
            raise PublicDataUnavailableError("공개 시장 데이터를 조회하지 못했습니다.") from error
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            # 일부 공개 Naver Finance 응답은 한글 종목명 때문에 CP949로 인코딩된다.
            try:
                return body.decode("cp949")
            except UnicodeDecodeError as error:
                raise PublicDataUnavailableError("공개 시장 데이터를 해석하지 못했습니다.") from error


def _market_source(stock_code: str, title: str, as_of: date | None) -> SourceRecord:
    return SourceRecord(f"naver:market:{stock_code}:{title}", f"Naver Finance {title} - {stock_code}", "Naver Finance", f"https://finance.naver.com/item/main.naver?code={stock_code}", "market_data", published_at=as_of)


def _to_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_date(value: object) -> date | None:
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None

