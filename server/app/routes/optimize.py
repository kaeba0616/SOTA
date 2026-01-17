"""
최적화 API 라우트 + WebSocket
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import asyncio
import json

from app.services.optimizer_service import OptimizerService
from app.schemas.models import OptimizeRequest, OptimizeResponse, OptimizeResult

router = APIRouter()
optimizer_service = OptimizerService()


@router.post("/optimize", response_model=OptimizeResponse)
async def start_optimization(request: OptimizeRequest):
    """
    최적화 작업 시작

    비동기로 최적화를 실행하고 job_id를 반환합니다.
    WebSocket으로 진행상황을 확인하거나, GET /api/optimize/{job_id}로 결과를 조회하세요.
    """
    job_id = optimizer_service.create_job(
        tablet_ids=request.tablet_ids,
        rows=request.rows,
        cols=request.cols,
        generations=request.generations,
        population=request.population
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "최적화 작업이 생성되었습니다. WebSocket으로 진행상황을 확인하세요."
    }


@router.get("/optimize/{job_id}", response_model=OptimizeResult)
async def get_optimization_result(job_id: str):
    """
    최적화 결과 조회

    - **job_id**: 최적화 작업 ID
    """
    job = optimizer_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    if job.result:
        return job.result

    return {
        "job_id": job_id,
        "status": job.status,
        "fitness": job.best_fitness,
        "total_level": None,
        "placements": None,
        "level_matrix": None,
        "grid_size": {"rows": job.rows, "cols": job.cols},
        "generations_run": job.current_generation
    }


@router.websocket("/ws/optimize/{job_id}")
async def optimize_websocket(websocket: WebSocket, job_id: str):
    """
    최적화 진행상황 WebSocket

    연결 후 자동으로 최적화를 시작하고 진행상황을 실시간으로 전송합니다.

    메시지 타입:
    - progress: 진행상황 업데이트
    - complete: 최적화 완료
    - error: 에러 발생
    """
    await websocket.accept()

    job = optimizer_service.get_job(job_id)
    if not job:
        await websocket.send_json({
            "type": "error",
            "message": "작업을 찾을 수 없습니다"
        })
        await websocket.close()
        return

    # 진행상황 전송 큐
    progress_queue = asyncio.Queue()

    def progress_callback(stats):
        """진행상황 콜백"""
        try:
            asyncio.get_event_loop().call_soon_threadsafe(
                progress_queue.put_nowait,
                {
                    "type": "progress",
                    "generation": stats['generation'],
                    "best_fitness": stats['best_fitness'],
                    "avg_fitness": stats['avg_fitness'],
                    "progress": stats['progress']
                }
            )
        except Exception:
            pass

    async def send_progress():
        """진행상황 전송 태스크"""
        while True:
            try:
                msg = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                await websocket.send_json(msg)
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                break
            except Exception:
                break

    try:
        # 진행상황 전송 태스크 시작
        progress_task = asyncio.create_task(send_progress())

        # 최적화 실행
        result = await optimizer_service.run_optimization(job_id, progress_callback)

        # 진행상황 태스크 종료
        progress_task.cancel()

        # 결과 전송
        await websocket.send_json({
            "type": "complete",
            "result": result
        })

    except WebSocketDisconnect:
        print(f"WebSocket 연결 종료: {job_id}")
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
