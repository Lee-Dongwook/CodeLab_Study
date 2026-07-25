from fastapi import FastAPI

from app.api.research import router as research_router

app = FastAPI(title="테마 주식 리서치 에이전트", version="0.1.0")
app.include_router(research_router)
