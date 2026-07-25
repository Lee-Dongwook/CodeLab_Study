from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.data_sources.dart_corporation_registry import DartCorporationRegistry
from app.models.errors import PublicDataUnavailableError

router = APIRouter(prefix="/dart", tags=["dart"])


def get_dart_corporation_registry() -> DartCorporationRegistry:
    try:
        return DartCorporationRegistry.from_environment()
    except PublicDataUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/companies/resolve")
def resolve_company(
    query: str = Query(min_length=2),
    registry: DartCorporationRegistry = Depends(get_dart_corporation_registry),
) -> dict:
    """국내 종목명 또는 6자리 종목코드를 DART 고유번호로 해석한다."""
    company = registry.resolve(" ".join(query.split()))
    if company is None:
        raise HTTPException(status_code=404, detail="국내 상장 종목을 찾지 못했습니다.")
    return {
        "name": company.name,
        "stock_code": company.stock_code,
        "corp_code": company.corp_code,
    }
