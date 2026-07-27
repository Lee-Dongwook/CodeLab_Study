import unittest
from datetime import date, datetime

from app.models.domain import (
    DomesticCandidate,
    DomesticMetrics,
    NewsDisclosureItem,
    SourceRecord,
    ThemeDefinition,
)
from app.services.research_service import ResearchService
from app.services.report_service import render_markdown_report


def source(source_id: str) -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        title=f"문서 {source_id}",
        publisher="테스트 기업",
        url=f"https://example.test/{source_id}",
        source_type="company_official",
        published_at=date(2026, 7, 1),
    )


class FakePublicDataSource:
    def define_theme(self, theme_or_company: str) -> ThemeDefinition:
        return ThemeDefinition(
            name=theme_or_company,
            description="테스트용 테마 설명",
            inclusion_criteria="공식자료로 관련 사업이 확인된 KRX 보통주",
            exclusion_criteria="ETF와 우선주 제외",
            sources=(source("theme"),),
        )

    def find_domestic_candidates(self, theme: ThemeDefinition):
        return [
            DomesticCandidate("간접사", "200002", "KRX", "COMMON_STOCK", "간접 사업", "indirect", "근거", (source("indirect"),)),
            DomesticCandidate("ETF", "300003", "KRX", "ETF", "ETF", "direct", "제외", (source("etf"),)),
            DomesticCandidate("직접사", "100001", "KRX", "COMMON_STOCK", "직접 사업", "direct", "근거", (source("direct"),)),
        ]

    def get_domestic_metrics(self, candidate: DomesticCandidate):
        return DomesticMetrics(
            candidate_code=candidate.code,
            close_price=10000,
            market_cap=100000000,
            per=None,
            pbr=1.2,
            revenue_growth=10.0,
            operating_margin=5.0,
            market_data_as_of=date(2026, 7, 24),
            financial_period="2025 연간",
            sources=(source(f"metric-{candidate.code}"),),
        )

    def get_news_disclosures(self, candidate: DomesticCandidate, limit: int):
        record = source(f"news-{candidate.code}")
        return [
            NewsDisclosureItem(
                candidate_code=candidate.code,
                category="disclosure",
                title="테스트 공시",
                summary="사업 관련 공시",
                url=record.url,
                published_at=date(2026, 7, 2),
                checked_at=datetime(2026, 7, 3),
                source=record,
            )
        ]


class ResearchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ResearchService(FakePublicDataSource())

    def test_filters_non_common_stocks_and_prioritizes_direct_candidates(self) -> None:
        report = self.service.create_report("로봇", 3)

        self.assertEqual([candidate.code for candidate in report.candidates], ["100001", "200002"])
        self.assertEqual(len(report.metrics), 2)
        self.assertEqual(len(report.news_disclosures), 2)

    def test_returns_available_candidates_when_fewer_than_top_n(self) -> None:
        report = self.service.create_report("로봇", 5)

        self.assertEqual(len(report.candidates), 2)

    def test_deduplicates_candidates_before_applying_top_n(self) -> None:
        duplicate = DomesticCandidate("직접사", "100001", "KRX", "COMMON_STOCK", "중복", "direct", "중복 근거", (source("duplicate"),))
        selected = self.service._select_candidates(
            [duplicate, *FakePublicDataSource().find_domestic_candidates(ThemeDefinition("테마", "설명", "포함", "제외", (source("theme"),)))],
            3,
        )

        self.assertEqual([candidate.code for candidate in selected], ["100001", "200002"])

    def test_renders_required_phase_one_sections(self) -> None:
        markdown = render_markdown_report(self.service.create_report("로봇", 3))

        self.assertIn("## 1. 빠른 요약", markdown)
        self.assertIn("## 11. 안내 문구", markdown)
        self.assertIn("확인 불가", markdown)


if __name__ == "__main__":
    unittest.main()
