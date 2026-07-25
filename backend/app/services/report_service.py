from __future__ import annotations

from app.models.domain import DomesticMetrics, PriceVolumeMetrics, ResearchReport


def render_markdown_report(report: ResearchReport) -> str:
    """Phase 1 보고서에 사용 가능한 Phase 2 확장 정보를 함께 렌더링한다."""
    lines = [
        "# 테마 주식 리서치 결과",
        "",
        "## 1. 빠른 요약",
        f"- 분석 대상: {report.theme_definition.name}",
        f"- 확인된 국내 후보: {len(report.candidates)}개",
        "- 본 결과는 공개자료를 기반으로 한 리서치 보조 정보입니다.",
        "",
        "## 2. 국내 테마 정의",
        report.theme_definition.description,
        "",
        f"- 포함 기준: {report.theme_definition.inclusion_criteria}",
        f"- 제외 기준: {report.theme_definition.exclusion_criteria}",
    ]
    if report.theme_definition.direct_relevance_criteria:
        lines.append(f"- 직접 관련 기준: {report.theme_definition.direct_relevance_criteria}")
    if report.theme_definition.indirect_relevance_criteria:
        lines.append(f"- 간접 관련 기준: {report.theme_definition.indirect_relevance_criteria}")
    lines.extend(["", "## 3. 국내 후보 종목 및 선정 근거"])
    if report.candidates:
        for candidate in report.candidates:
            relevance = "직접 관련" if candidate.relevance == "direct" else "간접 관련"
            lines.extend(
                [
                    f"### {candidate.name} ({candidate.code})",
                    f"- 관련 사업: {candidate.related_business}",
                    f"- 관련 여부: {relevance}",
                    f"- 선정 근거: {candidate.selection_reason}",
                ]
            )
    else:
        lines.append("- 확인된 적격 국내 후보가 없습니다.")

    lines.extend(["", "## 4. 국내 정량 비교", _metrics_table(report.metrics)])
    if report.price_volume_metrics:
        lines.extend(["", _price_volume_table(report.price_volume_metrics)])

    lines.extend(["", "## 5. 상세 리스크 분석"])
    if report.risks:
        for risk in report.risks:
            lines.append(f"- [{risk.category}] {risk.fact}")
    else:
        lines.append("- 확인 가능한 공개자료 기반 리스크 항목이 없습니다.")

    lines.extend(["", "## 6. 최근 뉴스 및 공시"])
    if report.news_disclosures:
        for item in report.news_disclosures:
            date_text = item.published_at.isoformat() if item.published_at else "발행일 미확인"
            lines.append(f"- [{item.category}] {item.title} ({date_text}): {item.summary}")
            lines.append(f"  - {item.url}")
    else:
        lines.append("- 확인 가능한 최근 뉴스 또는 공시가 없습니다.")

    lines.extend(["", "## 7. 미국 시장 선행 동향 (참고)"])
    if report.us_market_reference:
        reference = report.us_market_reference
        lines.extend([f"- 기준일: {_display(reference.as_of)}", f"- 동향: {reference.trend}", f"- 배경: {reference.background}", f"- 대표 종목: {', '.join(reference.representative_companies) or '확인 가능한 자료 없음'}", f"- 대표 ETF: {', '.join(reference.representative_etfs) or '확인 가능한 자료 없음'}", f"- 뉴스 요약: {reference.news_summary}"])
    else:
        lines.append("- 확인 가능한 공개 참고자료가 없습니다.")

    lines.extend(["", "## 8. 관련 미국 Peer Company (참고)"])
    if report.us_peer_companies:
        for peer in report.us_peer_companies:
            lines.append(f"- {peer.name} ({peer.ticker}) | {peer.related_business} | {peer.connection} | {peer.relevance}")
    else:
        lines.append("- 확인 가능한 공개 참고자료가 없습니다.")

    lines.extend(["", "## 9. 글로벌 운용사 동향 (참고)"])
    if report.asset_manager_references:
        for manager in report.asset_manager_references:
            lines.append(f"- {manager.manager} | {manager.etf_or_holding} | {manager.public_view} | {manager.recent_activity} | {_display(manager.as_of)}")
    else:
        lines.append("- 확인 가능한 공개 참고자료가 없습니다.")

    lines.extend(["", "## 10. 참고자료 및 출처"])
    for source in report.sources:
        published = source.published_at.isoformat() if source.published_at else "발행일 미확인"
        lines.append(f"- {source.title} | {source.publisher} | {published} | {source.url}")

    lines.extend(["", "## 11. 안내 문구", report.disclaimer])
    return "\n".join(lines)


def _metrics_table(metrics: tuple[DomesticMetrics, ...]) -> str:
    header = "| 종목코드 | 최근 종가 | 시가총액 | PER | PBR | 매출 성장률 | 영업이익률 | 시장 기준일 | 재무 기준 기간 |"
    divider = "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"
    if not metrics:
        return "\n".join([header, divider, "| 확인 가능한 지표 없음 | - | - | - | - | - | - | - | - |"])

    rows = [header, divider]
    for metric in metrics:
        rows.append(
            "| {code} | {close} | {cap} | {per} | {pbr} | {growth} | {margin} | {market_date} | {financial_period} |".format(
                code=metric.candidate_code,
                close=_display(metric.close_price),
                cap=_display(metric.market_cap),
                per=_display(metric.per),
                pbr=_display(metric.pbr),
                growth=_display(metric.revenue_growth),
                margin=_display(metric.operating_margin),
                market_date=_display(metric.market_data_as_of),
                financial_period=_display(metric.financial_period),
            )
        )
    return "\n".join(rows)


def _display(value: int | float | None) -> str:
    return "확인 불가" if value is None else str(value)


def _price_volume_table(metrics: tuple[PriceVolumeMetrics, ...]) -> str:
    rows = [
        "| 종목코드 | 기준 기간 | 기간 수익률 | 변동성 | 거래량 변화 | 거래량 급증 여부 | 기준일 |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for metric in metrics:
        surge = "확인 불가" if metric.volume_surge is None else ("예" if metric.volume_surge else "아니오")
        rows.append(
            "| {code} | {period} | {return_} | {volatility} | {volume_change} | {surge} | {as_of} |".format(
                code=metric.candidate_code,
                period=metric.analysis_period,
                return_=_display(metric.period_return),
                volatility=_display(metric.volatility),
                volume_change=_display(metric.volume_change),
                surge=surge,
                as_of=_display(metric.data_as_of),
            )
        )
    return "\n".join(rows)
