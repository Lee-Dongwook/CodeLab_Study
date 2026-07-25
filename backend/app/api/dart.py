from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.data_sources.dart import DartDisclosureClient, DartDisclosureQuery
from app.models.errors import DartApiError, PublicDataUnavailableError

router = APIRouter(prefix="/dart", tags=["dart"])


def get_dart_client() -> DartDisclosureClient:
    try:
        return DartDisclosureClient.from_environment()
    except PublicDataUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/disclosures")
def list_disclosures(
    bgn_de: str | None = Query(default=None, pattern="^\\d{8}$"),
    end_de: str | None = Query(default=None, pattern="^\\d{8}$"),
    corp_code: str | None = Query(default=None, min_length=8, max_length=8),
    corp_cls: str | None = Query(default=None, pattern="^[YKNE]$"),
    page_no: int = Query(default=1, ge=1),
    page_count: int = Query(default=10, ge=1, le=100),
    client: DartDisclosureClient = Depends(get_dart_client),
) -> dict:
    """OpenDART 공시 목록을 조회한다. API 키는 서버 환경변수에서만 읽는다."""
    start_date, end_date = _resolve_date_range(bgn_de, end_de)
    query = DartDisclosureQuery(
        bgn_de=start_date,
        end_de=end_date,
        corp_code=corp_code,
        corp_cls=corp_cls,
        page_no=page_no,
        page_count=page_count,
    )
    try:
        disclosures = client.list_disclosures(query)
    except DartApiError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {
        "items": disclosures,
        "count": len(disclosures),
        "bgn_de": start_date.strftime("%Y%m%d"),
        "end_de": end_date.strftime("%Y%m%d"),
    }


def _parse_dart_date(value: str | None):
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as error:
        raise HTTPException(status_code=422, detail="날짜는 YYYYMMDD 형식이어야 합니다.") from error


def _resolve_date_range(bgn_de: str | None, end_de: str | None) -> tuple[date, date]:
    """날짜가 없으면 최근 30일을 조회해 목록 API의 기간 제한을 지킨다."""
    parsed_start = _parse_dart_date(bgn_de)
    parsed_end = _parse_dart_date(end_de)
    if parsed_start and parsed_end:
        return parsed_start, parsed_end
    if parsed_start:
        return parsed_start, date.today()
    if parsed_end:
        return parsed_end - timedelta(days=30), parsed_end
    today = date.today()
    return today - timedelta(days=30), today
