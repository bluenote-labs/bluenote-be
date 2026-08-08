from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from app.api import auth, records, upload, user
from app.core.logger import setup_logging

setup_logging()

from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # 서버 시작 시 DB 초기화
    yield

app = FastAPI(
    title="Bluenote API Specification",
    description="블루노트(Bluenote) 서비스 REST API 문서입니다.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/users", tags=["user"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(records.router, prefix="/api/records", tags=["records"])

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")