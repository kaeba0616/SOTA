"""
Pydantic 스키마 모델
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class Rarity(str, Enum):
    NORMAL = "일반"
    ADVANCED = "고급"
    RARE = "희귀"
    LEGENDARY = "전설"


class EffectResponse(BaseModel):
    """효과 응답 모델"""
    pos: Optional[List[int]] = None
    shape: Optional[str] = None
    type: str
    value: Any


class TabletResponse(BaseModel):
    """석판 응답 모델"""
    id: str
    name: str
    image_url: str
    rotatable: bool
    rarity: str
    restriction: Optional[str] = None
    effects: List[EffectResponse]


class TabletListResponse(BaseModel):
    """석판 목록 응답"""
    tablets: List[TabletResponse]
    total: int


class DetectedTablet(BaseModel):
    """감지된 석판"""
    id: str
    name: str
    confidence: float
    slot_index: int


class UploadResponse(BaseModel):
    """이미지 업로드 응답"""
    detected: List[DetectedTablet]
    total_slots: int
    image_size: Dict[str, int]


class OptimizeRequest(BaseModel):
    """최적화 요청"""
    tablet_ids: List[str] = Field(..., description="사용할 석판 ID 목록")
    rows: int = Field(..., ge=2, le=10, description="그리드 행 수")
    cols: int = Field(..., ge=2, le=10, description="그리드 열 수")
    generations: int = Field(default=500, ge=50, le=2000, description="GA 세대 수")
    population: int = Field(default=100, ge=20, le=500, description="인구 크기")


class OptimizeResponse(BaseModel):
    """최적화 작업 생성 응답"""
    job_id: str
    status: str = "pending"
    message: str = "최적화 작업이 생성되었습니다"


class PlacementResult(BaseModel):
    """배치 결과"""
    tablet_id: str
    tablet_name: str
    position: Dict[str, int]  # {"row": 0, "col": 0}
    rotation: int


class OptimizeResult(BaseModel):
    """최적화 결과"""
    job_id: str
    status: str
    fitness: Optional[float] = None
    total_level: Optional[int] = None
    placements: Optional[List[PlacementResult]] = None
    level_matrix: Optional[List[List[int]]] = None
    grid_size: Optional[Dict[str, int]] = None
    generations_run: Optional[int] = None


class ProgressMessage(BaseModel):
    """진행상황 메시지 (WebSocket)"""
    type: str = "progress"
    generation: int
    best_fitness: float
    avg_fitness: float
    progress: float  # 0-100


class ResultMessage(BaseModel):
    """결과 메시지 (WebSocket)"""
    type: str = "complete"
    result: OptimizeResult


class ErrorMessage(BaseModel):
    """에러 메시지 (WebSocket)"""
    type: str = "error"
    message: str
