from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Literal


SourceType = Literal["krx", "dart", "company_ir", "company_official", "news", "market_data"]
Relevance = Literal["direct", "indirect"]


@dataclass(frozen=True)
class ResearchRequest:
    theme: str
    top_n: int


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    publisher: str
    url: str
    source_type: SourceType
    published_at: date | None = None
    checked_at: datetime = field(default_factory=datetime.now)
    original_accessible: bool = True


@dataclass(frozen=True)
class ThemeDefinition:
    name: str
    description: str
    inclusion_criteria: str
    exclusion_criteria: str
    sources: tuple[SourceRecord, ...]
    direct_relevance_criteria: str = ""
    indirect_relevance_criteria: str = ""


@dataclass(frozen=True)
class DomesticCompanyIdentity:
    name: str
    stock_code: str
    corp_code: str | None = None


@dataclass(frozen=True)
class ThemeEvidence:
    name: str
    description: str
    inclusion_criteria: str
    exclusion_criteria: str
    direct_relevance_criteria: str
    indirect_relevance_criteria: str
    sources: tuple[SourceRecord, ...]


@dataclass(frozen=True)
class DomesticCandidate:
    name: str
    code: str
    exchange: str
    security_type: str
    related_business: str
    relevance: Relevance
    selection_reason: str
    sources: tuple[SourceRecord, ...]


@dataclass(frozen=True)
class DomesticMetrics:
    candidate_code: str
    close_price: int | float | None
    market_cap: int | float | None
    per: float | None
    pbr: float | None
    revenue_growth: float | None
    operating_margin: float | None
    market_data_as_of: date | None
    financial_period: str | None
    sources: tuple[SourceRecord, ...]


@dataclass(frozen=True)
class PriceVolumePoint:
    traded_on: date
    close_price: int | float
    volume: int


@dataclass(frozen=True)
class PriceVolumeMetrics:
    candidate_code: str
    analysis_period: str
    period_return: float | None
    volatility: float | None
    volume_change: float | None
    volume_surge: bool | None
    data_as_of: date | None


@dataclass(frozen=True)
class RiskItem:
    candidate_code: str
    category: Literal["company", "disclosure_news", "industry", "check_point"]
    fact: str
    sources: tuple[SourceRecord, ...]


@dataclass(frozen=True)
class NewsDisclosureItem:
    candidate_code: str
    category: Literal["news", "disclosure"]
    title: str
    summary: str
    url: str
    published_at: date | None
    checked_at: datetime
    source: SourceRecord


@dataclass(frozen=True)
class USMarketSnapshot:
    ticker: str
    name: str
    instrument_type: str
    close_price: float | None
    daily_change_percent: float | None
    volume: int | None
    volume_change_percent: float | None
    as_of: date | None
    source: SourceRecord


@dataclass(frozen=True)
class USMacroIndicator:
    label: str
    ticker: str
    snapshot: USMarketSnapshot
    interpretation: str
    domestic_check_point: str


@dataclass(frozen=True)
class USMarketReference:
    theme: str
    trend: str
    background: str
    representative_companies: tuple[str, ...]
    representative_etfs: tuple[str, ...]
    news_summary: str
    as_of: date | None
    sources: tuple[SourceRecord, ...]
    market_snapshots: tuple[USMarketSnapshot, ...] = ()
    macro_indicators: tuple[USMacroIndicator, ...] = ()


@dataclass(frozen=True)
class USPeerCompany:
    name: str
    ticker: str
    related_business: str
    connection: str
    relevance: Relevance
    sources: tuple[SourceRecord, ...]
    market_snapshot: USMarketSnapshot | None = None
    closing_news_summary: str = "확인 가능한 공개자료 없음"


@dataclass(frozen=True)
class AssetManagerReference:
    manager: str
    etf_or_holding: str
    public_view: str
    recent_activity: str
    as_of: date | None
    sources: tuple[SourceRecord, ...]


@dataclass(frozen=True)
class ResearchReport:
    request: ResearchRequest
    generated_at: datetime
    theme_definition: ThemeDefinition
    candidates: tuple[DomesticCandidate, ...]
    metrics: tuple[DomesticMetrics, ...]
    news_disclosures: tuple[NewsDisclosureItem, ...]
    sources: tuple[SourceRecord, ...]
    disclaimer: str
    price_volume_metrics: tuple[PriceVolumeMetrics, ...] = ()
    risks: tuple[RiskItem, ...] = ()
    us_market_reference: USMarketReference | None = None
    us_peer_companies: tuple[USPeerCompany, ...] = ()
    asset_manager_references: tuple[AssetManagerReference, ...] = ()

    def to_dict(self) -> dict:
        """API 응답과 Markdown 렌더링에 사용할 수 있는 직렬화 결과."""
        return asdict(self)
