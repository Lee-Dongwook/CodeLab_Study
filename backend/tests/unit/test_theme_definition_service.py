import unittest

from app.models.domain import DomesticCompanyIdentity, SourceRecord, ThemeEvidence
from app.models.errors import ThemeDefinitionUnavailableError
from app.models.domain import ResearchReport, ResearchRequest
from app.services.report_service import render_markdown_report
from app.services.theme_definition_service import ThemeDefinitionService


def official_source() -> SourceRecord:
    return SourceRecord(
        source_id="official-1",
        title="공식 제품 소개",
        publisher="테스트기업",
        url="https://example.test/product",
        source_type="company_official",
    )


class FakeEvidenceProvider:
    def __init__(self, evidence: ThemeEvidence | None) -> None:
        self.evidence = evidence
        self.last_theme: str | None = None
        self.last_company: DomesticCompanyIdentity | None = None

    def find_for_theme(self, normalized_theme: str) -> ThemeEvidence | None:
        self.last_theme = normalized_theme
        return self.evidence

    def find_for_company(self, company: DomesticCompanyIdentity) -> ThemeEvidence | None:
        self.last_company = company
        return self.evidence


class FakeCompanyIdentifier:
    def resolve(self, normalized_input: str) -> DomesticCompanyIdentity | None:
        if normalized_input == "테스트로보틱스":
            return DomesticCompanyIdentity("테스트로보틱스", "123456", "00123456")
        return None


def evidence(sources: tuple[SourceRecord, ...] = (official_source(),)) -> ThemeEvidence:
    return ThemeEvidence(
        name="산업용 로봇",
        description="공장 자동화에 사용되는 산업용 로봇 관련 테마",
        inclusion_criteria="공식자료에서 산업용 로봇 제품 또는 서비스를 확인할 수 있는 KRX 보통주",
        exclusion_criteria="단순 기사 언급 또는 ETF",
        direct_relevance_criteria="로봇 본체·제어 소프트웨어를 직접 제공",
        indirect_relevance_criteria="로봇 공급망·핵심 부품을 제공",
        sources=sources,
    )


class ThemeDefinitionServiceTests(unittest.TestCase):
    def test_normalizes_theme_and_builds_definition_with_official_source(self) -> None:
        provider = FakeEvidenceProvider(evidence())
        service = ThemeDefinitionService(provider)

        definition = service.define("  산업용   로봇 ")

        self.assertEqual(provider.last_theme, "산업용 로봇")
        self.assertEqual(definition.name, "산업용 로봇")
        self.assertEqual(definition.direct_relevance_criteria, "로봇 본체·제어 소프트웨어를 직접 제공")
        self.assertEqual(len(definition.sources), 1)

    def test_identifies_domestic_company_before_requesting_evidence(self) -> None:
        provider = FakeEvidenceProvider(evidence())
        service = ThemeDefinitionService(provider, FakeCompanyIdentifier())

        service.define("테스트로보틱스")

        self.assertIsNotNone(provider.last_company)
        self.assertEqual(provider.last_company.stock_code, "123456")
        self.assertIsNone(provider.last_theme)

    def test_rejects_definition_without_evidence(self) -> None:
        service = ThemeDefinitionService(FakeEvidenceProvider(None))

        with self.assertRaises(ThemeDefinitionUnavailableError):
            service.define("산업용 로봇")

    def test_rejects_non_official_source(self) -> None:
        non_official = SourceRecord("news-1", "기사", "언론사", "https://example.test/news", "news")
        service = ThemeDefinitionService(FakeEvidenceProvider(evidence((non_official,))))

        with self.assertRaises(ThemeDefinitionUnavailableError):
            service.define("산업용 로봇")

    def test_report_includes_direct_and_indirect_criteria(self) -> None:
        definition = ThemeDefinitionService(FakeEvidenceProvider(evidence())).define("산업용 로봇")
        report = ResearchReport(
            request=ResearchRequest("산업용 로봇", 3),
            generated_at=official_source().checked_at,
            theme_definition=definition,
            candidates=(),
            metrics=(),
            news_disclosures=(),
            sources=definition.sources,
            disclaimer="안내 문구",
        )

        markdown = render_markdown_report(report)

        self.assertIn("직접 관련 기준", markdown)
        self.assertIn("간접 관련 기준", markdown)
