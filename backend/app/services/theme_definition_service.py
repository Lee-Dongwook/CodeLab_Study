from __future__ import annotations

from typing import Protocol

from app.models.domain import DomesticCompanyIdentity, SourceRecord, ThemeDefinition, ThemeEvidence
from app.models.errors import InputValidationError, ThemeDefinitionUnavailableError

_AMBIGUOUS_TERMS = {"주식", "테마", "산업", "기업", "시장"}
_OFFICIAL_SOURCE_TYPES = {"dart", "company_ir", "company_official"}


class DomesticCompanyIdentifier(Protocol):
    """입력된 이름을 국내 상장 기업으로 식별하는 계약."""

    def resolve(self, normalized_input: str) -> DomesticCompanyIdentity | None: ...


class ThemeEvidenceProvider(Protocol):
    """공식 자료를 바탕으로 테마 근거를 찾아오는 계약."""

    def find_for_theme(self, normalized_theme: str) -> ThemeEvidence | None: ...

    def find_for_company(self, company: DomesticCompanyIdentity) -> ThemeEvidence | None: ...


class ThemeDefinitionService:
    """TASK-P1-03: 입력 식별과 공식 근거 기반 테마 정의를 수행한다."""

    def __init__(
        self,
        evidence_provider: ThemeEvidenceProvider,
        company_identifier: DomesticCompanyIdentifier | None = None,
    ) -> None:
        self._evidence_provider = evidence_provider
        self._company_identifier = company_identifier

    def define(self, raw_input: object) -> ThemeDefinition:
        normalized_input = normalize_theme_input(raw_input)
        company = self._company_identifier.resolve(normalized_input) if self._company_identifier else None
        evidence = (
            self._evidence_provider.find_for_company(company)
            if company is not None
            else self._evidence_provider.find_for_theme(normalized_input)
        )
        if evidence is None:
            raise ThemeDefinitionUnavailableError(
                "공식 근거를 확인하지 못했습니다. 더 구체적인 테마명 또는 국내 종목명을 입력해 주세요."
            )
        _validate_evidence(evidence)
        return ThemeDefinition(
            name=evidence.name,
            description=evidence.description,
            inclusion_criteria=evidence.inclusion_criteria,
            exclusion_criteria=evidence.exclusion_criteria,
            direct_relevance_criteria=evidence.direct_relevance_criteria,
            indirect_relevance_criteria=evidence.indirect_relevance_criteria,
            sources=evidence.sources,
        )


def normalize_theme_input(raw_input: object) -> str:
    if not isinstance(raw_input, str):
        raise InputValidationError("theme은 테마명 또는 국내 종목명 문자열이어야 합니다.")
    normalized = " ".join(raw_input.split())
    if not normalized or normalized.isdigit() or normalized in _AMBIGUOUS_TERMS or len(normalized) < 2:
        raise InputValidationError("theme이 모호합니다. 더 구체적인 테마명 또는 국내 종목명을 입력해 주세요.")
    return normalized


def _validate_evidence(evidence: ThemeEvidence) -> None:
    if not evidence.sources:
        raise ThemeDefinitionUnavailableError("테마 정의에 연결된 공식 근거 출처가 없습니다.")
    if not all(_is_official_source(source) for source in evidence.sources):
        raise ThemeDefinitionUnavailableError("테마 정의에는 공개된 기업 공식자료 또는 DART 공시만 사용할 수 있습니다.")


def _is_official_source(source: SourceRecord) -> bool:
    return source.original_accessible and source.source_type in _OFFICIAL_SOURCE_TYPES
