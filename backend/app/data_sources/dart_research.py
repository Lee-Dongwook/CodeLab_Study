from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence

from app.data_sources.dart import DartCompanyOverview, DartDisclosureClient, DartDisclosureQuery
from app.data_sources.dart_corporation_registry import DartCorporationRegistry
from app.data_sources.naver_market import NaverMarketDataClient
from app.models.domain import DomesticCandidate, DomesticMetrics, DomesticCompanyIdentity, NewsDisclosureItem, PriceVolumeMetrics, SourceRecord, ThemeDefinition, ThemeEvidence
from app.models.errors import DartApiError, PublicDataUnavailableError, ThemeDefinitionUnavailableError
from app.services.price_volume_service import calculate_price_volume_metrics
from app.services.theme_definition_service import ThemeDefinitionService


class DartCompanyThemeEvidenceProvider:
    """DART 기업개황을 근거로 국내 종목 입력의 최소 테마 정의를 만든다."""

    def __init__(self, dart_client: DartDisclosureClient) -> None:
        self._dart_client = dart_client

    def find_for_theme(self, normalized_theme: str) -> ThemeEvidence | None:
        # 일반 테마는 사업·제품 근거 제공처가 연결된 뒤 지원한다.
        return None

    def find_for_company(self, company: DomesticCompanyIdentity) -> ThemeEvidence | None:
        if company.corp_code is None:
            return None
        overview = self._dart_client.get_company_overview(company.corp_code)
        source = _overview_source(overview)
        industry = overview.industry_code or "업종코드 미확인"
        return ThemeEvidence(
            name=company.name,
            description=(
                f"{company.name}을 입력한 기업 중심의 국내 종목 리서치입니다. "
                f"OpenDART 기업개황의 업종코드는 {industry}입니다."
            ),
            inclusion_criteria="입력한 국내 상장 종목 본인",
            exclusion_criteria="ETF·ETN·우선주·SPAC·OTC 및 공식 근거가 없는 제3자 종목",
            direct_relevance_criteria="입력한 국내 상장 기업 자체",
            indirect_relevance_criteria="현재 단계에서는 제공하지 않음",
            sources=(source,),
        )


class DartCompanyResearchDataSource:
    """국내 상장 기업명 입력에 대한 DART 기반 최소 리서치 데이터 소스."""

    def __init__(
        self,
        registry: DartCorporationRegistry,
        dart_client: DartDisclosureClient,
        market_client: NaverMarketDataClient | None = None,
    ) -> None:
        self._registry = registry
        self._dart_client = dart_client
        self._market_client = market_client or NaverMarketDataClient()
        self._theme_service = ThemeDefinitionService(
            DartCompanyThemeEvidenceProvider(dart_client), registry
        )

    def define_theme(self, theme_or_company: str) -> ThemeDefinition:
        return self._theme_service.define(theme_or_company)

    def find_domestic_candidates(self, theme: ThemeDefinition) -> Sequence[DomesticCandidate]:
        company = self._registry.resolve(theme.name)
        if company is None or company.corp_code is None:
            raise ThemeDefinitionUnavailableError("입력한 국내 상장 종목을 확인하지 못했습니다.")
        overview = self._dart_client.get_company_overview(company.corp_code)
        industry = overview.industry_code or "업종코드 미확인"
        return [
            DomesticCandidate(
                name=company.name,
                code=company.stock_code,
                exchange="KRX",
                security_type="COMMON_STOCK",
                related_business=f"OpenDART 기업개황 업종코드: {industry}",
                relevance="direct",
                selection_reason="사용자가 직접 입력한 국내 상장 종목",
                sources=(_overview_source(overview),),
            )
        ]

    def get_domestic_metrics(self, candidate: DomesticCandidate) -> DomesticMetrics | None:
        company = self._registry.resolve(candidate.code)
        sources: list[SourceRecord] = []
        try:
            market = self._market_client.get_snapshot(candidate.code)
            sources.append(market.source)
            market_points = self._market_client.get_price_volume_points(candidate.code, trading_days=60)
            market_data_as_of = market_points[-1].traded_on if market_points else market.as_of
        except PublicDataUnavailableError:
            market = None
            market_data_as_of = None

        try:
            financial = (
                self._dart_client.get_latest_annual_financial_metrics(company.corp_code)
                if company and company.corp_code
                else None
            )
            if financial:
                sources.append(financial.source)
        except DartApiError:
            financial = None

        return DomesticMetrics(
            candidate_code=candidate.code,
            close_price=market.close_price if market else None,
            market_cap=market.market_cap if market else None,
            per=market.per if market else None,
            pbr=market.pbr if market else None,
            revenue_growth=financial.revenue_growth if financial else None,
            operating_margin=financial.operating_margin if financial else None,
            market_data_as_of=market_data_as_of,
            financial_period=financial.financial_period if financial else None,
            sources=tuple(sources),
        )

    def get_price_volume_metrics(self, candidate: DomesticCandidate) -> PriceVolumeMetrics:
        try:
            points = self._market_client.get_price_volume_points(candidate.code, trading_days=60)
        except PublicDataUnavailableError:
            points = ()
        return calculate_price_volume_metrics(
            candidate.code,
            points,
            analysis_period="최근 60거래일",
            annualization_days=252,
            volume_surge_threshold=2.0,
        )

    def get_news_disclosures(self, candidate: DomesticCandidate, limit: int) -> Sequence[NewsDisclosureItem]:
        company = self._registry.resolve(candidate.code)
        if company is None or company.corp_code is None:
            return ()
        today = date.today()
        return self._dart_client.get_candidate_disclosures(
            candidate,
            query=DartDisclosureQuery(
                corp_code=company.corp_code,
                bgn_de=today - timedelta(days=90),
                end_de=today,
                page_count=100,
            ),
            limit=limit,
        )


def _overview_source(overview: DartCompanyOverview) -> SourceRecord:
    return SourceRecord(
        source_id=f"dart:company:{overview.corp_code}",
        title=f"OpenDART 기업개황 - {overview.corp_name}",
        publisher="OpenDART",
        url=overview.ir_url or overview.homepage_url or "https://opendart.fss.or.kr/",
        source_type="dart",
    )
