from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="테마 주식 리서치 에이전트 API",
    version="0.1.0",
    description="공개 정보 기반 테마 주식 리서치 API입니다. 투자 조언이나 매매 권유를 제공하지 않습니다.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
    """개발 환경에서 API 실행 상태를 확인한다."""
    return {"status": "ok"}
