"""
SOTA API Server
세피리아 석판 최적화 API 서버
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.routes import tablets_router, upload_router, optimize_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 라이프사이클 이벤트"""
    # 시작 시
    print("SOTA API Server 시작")
    yield
    # 종료 시
    print("SOTA API Server 종료")


app = FastAPI(
    title="SOTA API",
    description="세피리아 석판 최적화 배치 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(tablets_router, prefix="/api", tags=["tablets"])
app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(optimize_router, prefix="/api", tags=["optimize"])


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "running",
        "name": "SOTA API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
