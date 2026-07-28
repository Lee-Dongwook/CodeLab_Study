import json
import unittest

from app.data_sources.openai_references import OpenAIReferenceResearcher
from app.models.domain import DomesticCandidate, SourceRecord, USMarketSnapshot


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class FakeUSMarketValidator:
    def is_listed_equity(self, ticker: str) -> bool:
        return ticker == "ABC"


class FakeUSMarketClient:
    def get_recent_snapshot(self, ticker: str) -> USMarketSnapshot:
        source = _source()
        return USMarketSnapshot(ticker, "Company", "EQUITY", 100.0, 1.0, 1000, 10.0, None, source)


class OpenAIReferenceResearcherTests(unittest.TestCase):
    def test_parses_web_search_references(self) -> None:
        output = {
            "sources": [{"title": "공개 자료", "publisher": "Example", "url": "https://example.test/source", "published_at": "2026-07-24"}],
            "us_market": {"trend": "상승", "background": "자동화 투자 확대", "representative_companies": ["Company (ABC)"], "representative_etfs": ["ETF (ROBO)"], "news_summary": "관련 종목이 상승", "as_of": "2026-07-24"},
            "peers": [{"name": "Company", "ticker": "ABC", "related_business": "산업용 로봇", "connection": "협동로봇 사업", "relevance": "direct", "closing_news_summary": "실적 발표 후 상승", "closing_news_url": "https://example.test/news"}],
            "asset_managers": [{"manager": "Example Asset", "market": "KR", "etf_or_holding": "국내 로봇 ETF", "public_view": "공개 ETF 구성", "recent_activity": "최근 구성 기준", "as_of": "2026-07-24", "source_url": "https://example.test/etf"}],
        }
        client = OpenAIReferenceResearcher(
            "test-key",
            opener=lambda *_args, **_kwargs: FakeResponse({"output": [{"type": "web_search_call", "action": {"sources": [{"url": "https://example.test/source"}]}}, {"content": [{"type": "output_text", "text": json.dumps(output)}]}]}),
            us_market_validator=FakeUSMarketValidator(),
            us_market_client=FakeUSMarketClient(),
        )
        candidate = DomesticCandidate("테스트", "000001", "KRX", "COMMON_STOCK", "사업", "direct", "근거", (_source(),))

        bundle = client.research("로봇", [candidate])

        self.assertEqual(bundle.us_market.trend, "상승")
        self.assertEqual(bundle.peers[0].ticker, "ABC")
        self.assertEqual(bundle.peers[0].closing_news_url, "https://example.test/news")
        self.assertEqual(bundle.asset_managers[0].manager, "Example Asset")
        self.assertEqual(bundle.asset_managers[0].market, "KR")
        self.assertEqual(bundle.asset_managers[0].source_url, "https://example.test/etf")
        self.assertEqual(bundle.us_market.sources[0].url, "https://example.test/source")
        self.assertEqual(bundle.us_market.market_snapshots[0].ticker, "ABC")


def _source() -> SourceRecord:
    return SourceRecord("test", "테스트", "테스트", "https://example.test", "company_official")
