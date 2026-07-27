from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Sequence
from urllib.request import Request, urlopen

from app.config import load_project_env
from app.models.domain import AssetManagerReference, DomesticCandidate, SourceRecord, USMarketReference, USPeerCompany
from app.models.errors import PublicDataUnavailableError
from app.data_sources.us_market import YahooUSMarketClient, YahooUSMarketValidator, get_us_macro_indicators

_RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class ReferenceBundle:
    us_market: USMarketReference | None
    peers: tuple[USPeerCompany, ...]
    asset_managers: tuple[AssetManagerReference, ...]


class OpenAIReferenceResearcher:
    """OpenAI 웹 검색을 사용해 국내 분석을 보완하는 참고 자료만 수집한다."""

    def __init__(self, api_key: str, *, model: str = "gpt-4o-mini", opener: Callable[..., Any] = urlopen, timeout_seconds: int = 45, us_market_validator: YahooUSMarketValidator | None = None, us_market_client: YahooUSMarketClient | None = None) -> None:
        if not api_key.strip():
            raise PublicDataUnavailableError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        self._api_key, self._model, self._opener, self._timeout_seconds = api_key, model, opener, timeout_seconds
        self._us_market_validator = us_market_validator or YahooUSMarketValidator()
        self._us_market_client = us_market_client or YahooUSMarketClient()

    @classmethod
    def from_environment(cls) -> "OpenAIReferenceResearcher":
        load_project_env()
        return cls(
            os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv(
                "OPENAI_REFERENCE_MODEL",
                os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            ),
        )

    def research(self, theme: str, candidates: Sequence[DomesticCandidate]) -> ReferenceBundle:
        schema = _schema()
        domestic_names = ", ".join(f"{candidate.name}({candidate.code})" for candidate in candidates)
        prompt = (
            f"국내 테마: {theme}\n국내 후보: {domestic_names}\n"
            "웹 검색으로 다음 참고 정보를 작성하라. 국내 분석을 대체하거나 투자 추천을 해서는 안 된다. "
            "전일 또는 가장 최근 미국 거래일만 사용하고 날짜를 명시한다. 근거가 불충분한 항목은 빈 배열 또는 '확인 가능한 공개자료 없음'으로 작성한다. "
            "Peer는 미국 상장 기업만, 운용사 정보는 공개 ETF 구성·13F·공개 리포트로 확인된 경우만 포함한다. URL은 검색으로 실제 확인한 공개 페이지여야 한다."
            "각 Peer의 종가 영향 뉴스는 당일 또는 최근 거래일 종가에 영향을 줬다고 공개 기사·공시에서 명시된 경우에만 한 줄로 요약하고, 그렇지 않으면 '확인 가능한 공개자료 없음'으로 작성한다."
        )
        payload = {
            "model": self._model,
            "tools": [{"type": "web_search_preview", "search_context_size": "low"}],
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "text": {"format": {"type": "json_schema", "name": "krx_reference_information", "strict": True, "schema": schema}},
        }
        request = Request(_RESPONSES_URL, data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            parsed = json.loads(_output_text(response_payload))
        except (OSError, ValueError, UnicodeDecodeError, KeyError, TypeError) as error:
            raise PublicDataUnavailableError("OpenAI 참고 정보 검색을 완료하지 못했습니다.") from error
        sources = _sources_from_response(response_payload, parsed)
        return _to_bundle(theme, parsed, sources, self._us_market_validator, self._us_market_client)


def _to_bundle(theme: str, value: dict[str, Any], sources: tuple[SourceRecord, ...], validator: YahooUSMarketValidator, market_client: YahooUSMarketClient) -> ReferenceBundle:
    # 검색 출처가 없으면 참고 정보도 표시하지 않는다.
    if not sources:
        return ReferenceBundle(None, (), ())
    market = value.get("us_market") or {}
    us_market = None
    if market.get("trend"):
        snapshots = []
        for ticker in _extract_tickers(
            [*market.get("representative_companies", []), *market.get("representative_etfs", [])]
        ):
            try:
                snapshots.append(market_client.get_recent_snapshot(ticker))
            except PublicDataUnavailableError:
                continue
        macro_indicators = get_us_macro_indicators(market_client)
        combined_sources = tuple(
            {
                source.source_id: source
                for source in (
                    *sources,
                    *(snapshot.source for snapshot in snapshots),
                    *(indicator.snapshot.source for indicator in macro_indicators),
                )
            }.values()
        )
        us_market = USMarketReference(theme, str(market["trend"]), str(market.get("background", "")), tuple(market.get("representative_companies", [])), tuple(market.get("representative_etfs", [])), str(market.get("news_summary", "")), _parse_date(market.get("as_of")), combined_sources, tuple(snapshots), macro_indicators)
    peers = []
    for item in value.get("peers", []):
        if not item.get("name") or not item.get("ticker") or not validator.is_listed_equity(str(item["ticker"])):
            continue
        try:
            snapshot = market_client.get_recent_snapshot(str(item["ticker"]))
        except PublicDataUnavailableError:
            snapshot = None
        peers.append(
            USPeerCompany(
                str(item["name"]),
                str(item["ticker"]),
                str(item["related_business"]),
                str(item["connection"]),
                "direct" if item.get("relevance") == "direct" else "indirect",
                sources,
                snapshot,
                str(item.get("closing_news_summary") or "확인 가능한 공개자료 없음"),
            )
        )
    managers = tuple(AssetManagerReference(str(item["manager"]), str(item["etf_or_holding"]), str(item["public_view"]), str(item["recent_activity"]), _parse_date(item.get("as_of")), sources) for item in value.get("asset_managers", []) if item.get("manager"))
    return ReferenceBundle(us_market, tuple(peers), managers)


def _sources_from_response(payload: dict[str, Any], structured: dict[str, Any]) -> tuple[SourceRecord, ...]:
    source_details: list[tuple[str, str, str, date | None]] = []

    def add_source(url: object, title: object = "OpenAI 웹 검색 참고자료", publisher: object = "공개 웹 자료", published_at: object = None) -> None:
        if isinstance(url, str) and url.startswith("https://") and all(url != item[0] for item in source_details):
            source_details.append((url, str(title), str(publisher), _parse_date(published_at)))

    for source in structured.get("sources", []):
        if isinstance(source, dict):
            add_source(source.get("url"), source.get("title"), source.get("publisher"), source.get("published_at"))
    for output in payload.get("output", []):
        if output.get("type") != "web_search_call":
            continue
        for source in output.get("action", {}).get("sources", []):
            add_source(source.get("url"))
        for content in output.get("content", []):
            for annotation in content.get("annotations", []):
                add_source(annotation.get("url"))
    return tuple(SourceRecord(f"openai-web:{index}", title, publisher, url, "news", published_at=published_at) for index, (url, title, publisher, published_at) in enumerate(source_details, start=1))


def _output_text(payload: dict[str, Any]) -> str:
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("output_text가 없습니다.")


def _parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _extract_tickers(items: Sequence[object]) -> tuple[str, ...]:
    tickers = []
    for item in items:
        match = re.search(r"\(([A-Za-z0-9-]+)\)", str(item))
        if match and match.group(1) not in tickers:
            tickers.append(match.group(1))
    return tuple(tickers)


def _schema() -> dict[str, Any]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {"type": "object", "additionalProperties": False, "properties": {
        "sources": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "object", "additionalProperties": False, "properties": {"title": {"type": "string"}, "publisher": {"type": "string"}, "url": {"type": "string"}, "published_at": {"type": "string"}}, "required": ["title", "publisher", "url", "published_at"]}},
        "us_market": {"type": "object", "additionalProperties": False, "properties": {"trend": {"type": "string"}, "background": {"type": "string"}, "representative_companies": string_array, "representative_etfs": string_array, "news_summary": {"type": "string"}, "as_of": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}}, "required": ["trend", "background", "representative_companies", "representative_etfs", "news_summary", "as_of"]},
        "peers": {"type": "array", "maxItems": 5, "items": {"type": "object", "additionalProperties": False, "properties": {"name": {"type": "string"}, "ticker": {"type": "string"}, "related_business": {"type": "string"}, "connection": {"type": "string"}, "relevance": {"type": "string", "enum": ["direct", "indirect"]}, "closing_news_summary": {"type": "string"}}, "required": ["name", "ticker", "related_business", "connection", "relevance", "closing_news_summary"]}},
        "asset_managers": {"type": "array", "maxItems": 5, "items": {"type": "object", "additionalProperties": False, "properties": {"manager": {"type": "string"}, "etf_or_holding": {"type": "string"}, "public_view": {"type": "string"}, "recent_activity": {"type": "string"}, "as_of": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}}, "required": ["manager", "etf_or_holding", "public_view", "recent_activity", "as_of"]}},
    }, "required": ["sources", "us_market", "peers", "asset_managers"]}
