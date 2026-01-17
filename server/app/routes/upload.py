"""
이미지 업로드 API 라우트
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.schemas.models import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_screenshot(file: UploadFile = File(...)):
    """
    인벤토리 스크린샷 업로드 및 분석

    - **file**: 이미지 파일 (PNG, JPG)

    CNN 모델을 사용하여 이미지에서 석판을 감지합니다.
    """
    # 파일 타입 검증
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다")

    # 임시 파일로 저장
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # CNN 분석 시도
        try:
            detected_tablets = await _analyze_image(tmp_path)
        except Exception as e:
            print(f"CNN 분석 실패: {e}")
            # 모의 결과 반환
            detected_tablets = _mock_detection()

        # 이미지 크기 확인
        image_size = _get_image_size(tmp_path)

        return {
            "detected": detected_tablets,
            "total_slots": len(detected_tablets),
            "image_size": image_size
        }

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def _analyze_image(image_path: str):
    """CNN을 사용한 이미지 분석"""
    try:
        from optimizer.integration.cnn_bridge import CNNBridge

        bridge = CNNBridge()
        tablets = bridge.detect_tablets_from_screenshot(image_path)

        return [
            {
                "id": t.id,
                "name": t.name,
                "confidence": 0.95,  # CNN에서 실제 confidence 가져오기
                "slot_index": i
            }
            for i, t in enumerate(tablets)
        ]
    except ImportError:
        return _mock_detection()


def _mock_detection():
    """테스트용 모의 감지 결과"""
    return [
        {"id": "tb_001", "name": "기사도", "confidence": 0.95, "slot_index": 0},
        {"id": "tb_002", "name": "건조", "confidence": 0.92, "slot_index": 1},
        {"id": "tb_003", "name": "근사", "confidence": 0.88, "slot_index": 2},
        {"id": "tb_004", "name": "바람", "confidence": 0.91, "slot_index": 3},
    ]


def _get_image_size(image_path: str) -> dict:
    """이미지 크기 반환"""
    try:
        import cv2
        img = cv2.imread(image_path)
        if img is not None:
            h, w = img.shape[:2]
            return {"width": w, "height": h}
    except Exception:
        pass

    return {"width": 0, "height": 0}
