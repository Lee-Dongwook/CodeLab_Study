from __future__ import annotations

from app.models.domain import RiskItem

_RECOMMENDATION_TERMS = ("매수", "매도", "목표가", "유망", "저평가 확실")


def validate_risk_items(items: tuple[RiskItem, ...]) -> tuple[RiskItem, ...]:
    """출처 없는 리스크와 추천성 표현을 결과에서 차단한다."""
    unique: dict[tuple[str, str, str], RiskItem] = {}
    for item in items:
        if not item.sources:
            raise ValueError("리스크 항목에는 최소 1개의 출처가 필요합니다.")
        if any(term in item.fact for term in _RECOMMENDATION_TERMS):
            raise ValueError("리스크 항목에는 투자 추천 표현을 사용할 수 없습니다.")
        unique.setdefault((item.candidate_code, item.category, item.fact), item)
    return tuple(unique.values())
