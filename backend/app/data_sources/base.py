from __future__ import annotations

from typing import Protocol, Sequence

from app.models.domain import (
    DomesticCandidate,
    DomesticMetrics,
    NewsDisclosureItem,
    ThemeDefinition,
)


class PublicResearchDataSource(Protocol):
    """공개 데이터 제공처를 서비스 로직과 분리하는 계약.

    실제 KRX·DART·기업 공식자료 연결은 이 계약을 구현하는 어댑터로 추가한다.
    """

    def define_theme(self, theme_or_company: str) -> ThemeDefinition: ...

    def find_domestic_candidates(self, theme: ThemeDefinition) -> Sequence[DomesticCandidate]: ...

    def get_domestic_metrics(self, candidate: DomesticCandidate) -> DomesticMetrics | None: ...

    def get_news_disclosures(
        self, candidate: DomesticCandidate, limit: int
    ) -> Sequence[NewsDisclosureItem]: ...
