from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

from app.models.domain import SourceRecord, USMacroIndicator, USMarketSnapshot
from app.models.errors import PublicDataUnavailableError


class YahooUSMarketClient:
    """yfinance로 미국 대표 종목·ETF의 최근 가격·거래량을 조회한다.

    yfinance는 Yahoo Finance의 비공식 접근 라이브러리이므로, 본 데이터는 미국
    시장 참고 정보에만 사용한다. 조회 실패는 국내 리서치를 중단시키지 않는다.
    """

    def __init__(self, *, ticker_factory: Callable[[str], Any] | None = None) -> None:
        self._ticker_factory = ticker_factory

    def get_recent_snapshot(self, ticker: str) -> USMarketSnapshot:
        normalized = _normalize_ticker(ticker)
        try:
            pd, ticker_factory = _load_yfinance_dependencies(self._ticker_factory)
            security = ticker_factory(normalized)
            history = security.history(period="5d", interval="1d", auto_adjust=True, actions=False)
            info = security.info
        except Exception as error:  # yfinance는 제공처·네트워크 오류 타입을 보장하지 않는다.
            raise PublicDataUnavailableError("Yahoo Finance 시장 데이터를 조회하지 못했습니다.") from error

        if not isinstance(history, pd.DataFrame) or history.empty or "Close" not in history:
            raise PublicDataUnavailableError("Yahoo Finance 가격 데이터를 확인하지 못했습니다.")
        closes = history["Close"].dropna()
        if closes.empty:
            raise PublicDataUnavailableError("Yahoo Finance 가격 데이터를 확인하지 못했습니다.")

        close_price = float(closes.iloc[-1])
        previous_close = float(closes.iloc[-2]) if len(closes) > 1 else None
        daily_change_percent = (
            (close_price / previous_close - 1) * 100
            if previous_close not in (None, 0)
            else None
        )
        volume = None
        volume_change_percent = None
        if "Volume" in history and pd.notna(history["Volume"].iloc[-1]):
            volume = int(history["Volume"].iloc[-1])
            previous_volume = history["Volume"].iloc[-2] if len(history["Volume"]) > 1 else None
            if pd.notna(previous_volume) and previous_volume != 0:
                volume_change_percent = (volume / int(previous_volume) - 1) * 100
        as_of = pd.Timestamp(closes.index[-1]).date()
        name = str(info.get("longName") or info.get("shortName") or normalized)
        instrument_type = str(info.get("quoteType") or "UNKNOWN").upper()
        return USMarketSnapshot(
            ticker=normalized,
            name=name,
            instrument_type=instrument_type,
            close_price=close_price,
            daily_change_percent=daily_change_percent,
            volume=volume,
            volume_change_percent=volume_change_percent,
            as_of=as_of,
            source=SourceRecord(
                source_id=f"yfinance:{normalized}:{as_of}",
                title=f"Yahoo Finance 시세 - {name} ({normalized})",
                publisher="Yahoo Finance / yfinance (비공식)",
                url=f"https://finance.yahoo.com/quote/{normalized}",
                source_type="market_data",
                published_at=as_of,
            ),
        )


class YahooUSMarketValidator:
    """yfinance 가격 이력과 종목 유형으로 미국 상장 보통주를 최소 검증한다."""

    def __init__(self, *, market_client: YahooUSMarketClient | None = None) -> None:
        self._market_client = market_client or YahooUSMarketClient()

    def is_listed_equity(self, ticker: str) -> bool:
        try:
            snapshot = self._market_client.get_recent_snapshot(ticker)
        except PublicDataUnavailableError:
            return False
        return snapshot.instrument_type == "EQUITY"


_MACRO_INDICATOR_SPECS = (
    ("S&P 500", "^GSPC", "미국 대형주 위험선호", "국내 장 초반 KOSPI·외국인 순매수 흐름과 함께 확인"),
    ("필라델피아 반도체 지수", "^SOX", "글로벌 반도체 업종 심리", "국내 반도체 대형주·장비주의 상대 강도와 함께 확인"),
    ("구리 선물", "HG=F", "산업 수요·경기 민감도", "국내 산업재·소재 업종의 장중 수급과 함께 확인"),
    ("금 선물", "GC=F", "안전자산·인플레이션 경계 심리", "원/달러와 위험자산 전반의 변동성 확대 여부를 함께 확인"),
    ("미국 10년물 금리", "^TNX", "장기 금리·할인율 환경", "국내 성장주와 가치주의 상대 흐름, 원/달러를 함께 확인"),
)


def get_us_macro_indicators(client: YahooUSMarketClient) -> tuple[USMacroIndicator, ...]:
    """미국 장 마감 후 국내 장에서 함께 확인할 대표 거시 지표를 수집한다."""
    indicators = []
    for label, ticker, meaning, domestic_check_point in _MACRO_INDICATOR_SPECS:
        try:
            snapshot = client.get_recent_snapshot(ticker)
        except PublicDataUnavailableError:
            continue
        indicators.append(
            USMacroIndicator(
                label=label,
                ticker=ticker,
                snapshot=snapshot,
                interpretation=_interpret_change(snapshot.daily_change_percent, meaning),
                domestic_check_point=domestic_check_point,
            )
        )
    return tuple(indicators)


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789^=.-" for character in normalized):
        raise PublicDataUnavailableError("Yahoo Finance 티커 형식이 올바르지 않습니다.")
    return normalized


def _interpret_change(change_percent: float | None, meaning: str) -> str:
    if change_percent is None:
        return f"{meaning}를 보여주는 지표이나 일간 변동률은 확인하지 못했습니다."
    direction = "상승" if change_percent > 0 else "하락" if change_percent < 0 else "보합"
    return f"최근 거래일 {direction}은 {meaning} 관련 신호로 해석할 수 있으나, 국내 시장과의 동행은 보장되지 않습니다."


def _load_yfinance_dependencies(
    ticker_factory: Callable[[str], Any] | None,
) -> tuple[Any, Callable[[str], Any]]:
    try:
        pandas = import_module("pandas")
        factory = ticker_factory or import_module("yfinance").Ticker
    except ModuleNotFoundError as error:
        raise PublicDataUnavailableError(
            "Yahoo Finance 참고 데이터를 사용하려면 yfinance와 pandas를 설치해야 합니다."
        ) from error
    return pandas, factory
