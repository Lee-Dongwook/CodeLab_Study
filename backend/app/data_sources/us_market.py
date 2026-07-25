from __future__ import annotations

import json
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class YahooUSMarketValidator:
    """공개 Yahoo Finance 차트 응답으로 미국 상장 보통주 티커를 최소 검증한다."""

    def __init__(self, *, opener: Callable[..., Any] = urlopen, timeout_seconds: int = 10) -> None:
        self._opener, self._timeout_seconds = opener, timeout_seconds

    def is_listed_equity(self, ticker: str) -> bool:
        normalized = ticker.strip().upper()
        if not normalized or not normalized.replace("-", "").isalnum():
            return False
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{normalized}?{urlencode({'range': '5d', 'interval': '1d'})}"
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (research-mvp)"})
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
            meta = payload["chart"]["result"][0]["meta"]
        except (OSError, ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError):
            return False
        return meta.get("instrumentType") == "EQUITY" and str(meta.get("exchangeName", "")).upper() not in {"KSC", "KOSDAQ"}
