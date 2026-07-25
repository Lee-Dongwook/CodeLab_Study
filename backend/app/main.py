from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dart import router as dart_router
from app.api.research import router as research_router

app = FastAPI(title="테마 주식 리서치 에이전트", version="0.1.0")

# 개발 프론트엔드(Vite)에서의 API 요청만 허용한다.
# 인증 쿠키를 사용하지 않으므로 credentials는 허용하지 않는다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(research_router)
app.include_router(dart_router)
