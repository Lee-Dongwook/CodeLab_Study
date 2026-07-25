from __future__ import annotations

from datetime import datetime

from app.data_sources.base import PublicResearchDataSource
from app.models.domain import (
    DomesticCandidate,
    ResearchReport,
    ResearchRequest,
    SourceRecord,
)
from app.services.input_validator import validate_request

_DISCLAIMER = (
    "데이터는 공개 정보와 표시한 기준일 현재의 값이며 이후 변경될 수 있습니다. "
    "본 결과는 투자 조언이 아니며, 투자 판단 전 최신 공시와 추가 확인이 필요합니다."
)


class ResearchService:
    """Phase 1 국내 리서치 흐름을 조합한다."""

    def __init__(self, data_source: PublicResearchDataSource) -> None:
        self._data_source = data_source

    def create_report(self, theme: object, top_n: object) -> ResearchReport:
        request = validate_request(theme, top_n)
        theme_definition = self._data_source.define_theme(request.theme)

        candidates = self._select_candidates(
            self._data_source.find_domestic_candidates(theme_definition), request.top_n
        )
        metrics = []
        news_disclosures = []
        sources = list(theme_definition.sources)

        for candidate in candidates:
            sources.extend(candidate.sources)
            metric = self._data_source.get_domestic_metrics(candidate)
            if metric is not None:
                metrics.append(metric)
                sources.extend(metric.sources)

            items = self._data_source.get_news_disclosures(candidate, limit=3)
            news_disclosures.extend(items[:3])
            sources.extend(item.source for item in items[:3])

        return ResearchReport(
            request=request,
            generated_at=datetime.now(),
            theme_definition=theme_definition,
            candidates=tuple(candidates),
            metrics=tuple(metrics),
            news_disclosures=tuple(news_disclosures),
            sources=tuple(_deduplicate_sources(sources)),
            disclaimer=_DISCLAIMER,
        )

    @staticmethod
    def _select_candidates(
        candidates: object, top_n: int
    ) -> list[DomesticCandidate]:
        eligible = [
            candidate
            for candidate in candidates
            if candidate.exchange == "KRX" and candidate.security_type == "COMMON_STOCK"
        ]
        direct = [candidate for candidate in eligible if candidate.relevance == "direct"]
        indirect = [candidate for candidate in eligible if candidate.relevance == "indirect"]
        return (direct + indirect)[:top_n]


def _deduplicate_sources(sources: list[SourceRecord]) -> list[SourceRecord]:
    unique: dict[str, SourceRecord] = {}
    for source in sources:
        unique.setdefault(source.source_id, source)
    return list(unique.values())
