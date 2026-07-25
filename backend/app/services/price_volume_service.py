from __future__ import annotations

from math import sqrt
from statistics import stdev
from typing import Sequence

from app.models.domain import PriceVolumeMetrics, PriceVolumePoint


def calculate_price_volume_metrics(
    candidate_code: str,
    points: Sequence[PriceVolumePoint],
    *,
    analysis_period: str,
    annualization_days: int,
    volume_surge_threshold: float,
) -> PriceVolumeMetrics:
    """호출부가 전달한 동일 기간·기준으로 가격과 거래량 지표를 계산한다.

    기본 기간, 연환산 일수, 급증 임계값은 MVP 미결정 사항이므로 이 함수에서 고정하지 않는다.
    """
    ordered = sorted(points, key=lambda point: point.traded_on)
    as_of = ordered[-1].traded_on if ordered else None
    if len(ordered) < 2:
        return PriceVolumeMetrics(candidate_code, analysis_period, None, None, None, None, as_of)

    period_return = ((ordered[-1].close_price / ordered[0].close_price) - 1) * 100
    daily_returns = [
        (current.close_price / previous.close_price) - 1
        for previous, current in zip(ordered, ordered[1:])
        if previous.close_price > 0
    ]
    volatility = stdev(daily_returns) * sqrt(annualization_days) * 100 if len(daily_returns) >= 2 else None

    split = len(ordered) // 2
    prior = ordered[:split]
    recent = ordered[split:]
    prior_average = sum(point.volume for point in prior) / len(prior)
    recent_average = sum(point.volume for point in recent) / len(recent)
    volume_change = ((recent_average / prior_average) - 1) * 100 if prior_average > 0 else None
    volume_surge = recent_average >= prior_average * volume_surge_threshold if prior_average > 0 else None

    return PriceVolumeMetrics(
        candidate_code=candidate_code,
        analysis_period=analysis_period,
        period_return=period_return,
        volatility=volatility,
        volume_change=volume_change,
        volume_surge=volume_surge,
        data_as_of=as_of,
    )
