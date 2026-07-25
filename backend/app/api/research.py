"""FastAPI 어댑터.

실제 공개 데이터 제공처가 연결되면 `get_research_service`에 주입한다.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.errors import InputValidationError, PublicDataUnavailableError
from app.services.research_service import ResearchService
from app.services.report_service import render_markdown_report

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequestBody(BaseModel):
    theme: str
    top_n: int


def get_research_service() -> ResearchService:
    # Depends 단계의 일반 예외는 서버 500으로 변환되어 CORS 헤더가 누락될 수 있다.
    # HTTPException으로 반환하면 CORS 미들웨어가 정상 응답에 허용 헤더를 추가한다.
    raise HTTPException(
        status_code=503,
        detail=(
            "국내 후보·정량 데이터 제공처가 아직 연결되지 않았습니다. "
            "DART 공시 목록은 /dart/disclosures 엔드포인트에서 조회할 수 있습니다."
        ),
    )


@router.post("")
def create_research_report(
    body: ResearchRequestBody,
    service: Annotated[ResearchService, Depends(get_research_service)],
) -> dict:
    try:
        report = service.create_report(body.theme, body.top_n)
    except InputValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except PublicDataUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return {"report": report.to_dict(), "markdown": render_markdown_report(report)}
