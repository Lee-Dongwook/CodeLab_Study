from __future__ import annotations

from app.models.domain import ResearchRequest
from app.models.errors import InputValidationError

_AMBIGUOUS_TERMS = {"주식", "테마", "산업", "기업", "시장"}


def validate_request(theme: object, top_n: object) -> ResearchRequest:
    """MVP 입력 계약을 검증하고 정규화한다."""
    if not isinstance(theme, str):
        raise InputValidationError("theme은 테마명 또는 국내 종목명 문자열이어야 합니다.")

    normalized_theme = " ".join(theme.split())
    if not normalized_theme:
        raise InputValidationError("theme은 비어 있을 수 없습니다.")
    if normalized_theme.isdigit():
        raise InputValidationError("종목코드만으로는 분석할 수 없습니다. 테마명 또는 종목명을 입력해 주세요.")
    if normalized_theme in _AMBIGUOUS_TERMS or len(normalized_theme) < 2:
        raise InputValidationError("theme이 모호합니다. 더 구체적인 테마명 또는 국내 종목명을 입력해 주세요.")

    if isinstance(top_n, bool) or not isinstance(top_n, int):
        raise InputValidationError("top_n은 1 이상의 정수여야 합니다.")
    if top_n < 1:
        raise InputValidationError("top_n은 1 이상이어야 합니다.")

    return ResearchRequest(theme=normalized_theme, top_n=top_n)
