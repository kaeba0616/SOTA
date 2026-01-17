"""
석판 API 라우트
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.tablet_service import TabletService
from app.schemas.models import TabletListResponse

router = APIRouter()
tablet_service = TabletService()


@router.get("/tablets", response_model=TabletListResponse)
async def get_tablets(rarity: Optional[str] = None):
    """
    모든 석판 목록 조회

    - **rarity**: 필터링할 희귀도 (일반, 고급, 희귀, 전설)
    """
    tablets = tablet_service.get_all_formatted()

    if rarity:
        tablets = [t for t in tablets if t['rarity'] == rarity]

    return {
        "tablets": tablets,
        "total": len(tablets)
    }


@router.get("/tablets/{tablet_id}")
async def get_tablet(tablet_id: str):
    """
    특정 석판 조회

    - **tablet_id**: 석판 ID (예: tb_001)
    """
    tablet = tablet_service.get_tablet_by_id(tablet_id)

    if not tablet:
        raise HTTPException(status_code=404, detail="석판을 찾을 수 없습니다")

    return tablet_service.format_tablet_response(tablet)
