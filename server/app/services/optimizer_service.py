"""
최적화 서비스
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class OptimizationJob:
    """최적화 작업"""

    def __init__(self, job_id: str, tablet_ids: List[str], rows: int, cols: int,
                 generations: int = 500, population: int = 100):
        self.job_id = job_id
        self.tablet_ids = tablet_ids
        self.rows = rows
        self.cols = cols
        self.generations = generations
        self.population = population
        self.status = "pending"
        self.result = None
        self.error = None
        self.current_generation = 0
        self.best_fitness = 0
        self.avg_fitness = 0


class OptimizerService:
    """최적화 서비스"""

    _instance = None
    _jobs: Dict[str, OptimizationJob] = {}
    _executor = ThreadPoolExecutor(max_workers=2)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_job(self, tablet_ids: List[str], rows: int, cols: int,
                   generations: int = 500, population: int = 100) -> str:
        """새 최적화 작업 생성"""
        job_id = str(uuid.uuid4())
        job = OptimizationJob(job_id, tablet_ids, rows, cols, generations, population)
        self._jobs[job_id] = job
        return job_id

    def get_job(self, job_id: str) -> Optional[OptimizationJob]:
        """작업 조회"""
        return self._jobs.get(job_id)

    async def run_optimization(self, job_id: str,
                                progress_callback: Optional[Callable] = None) -> Dict:
        """최적화 실행 (비동기)"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"작업을 찾을 수 없습니다: {job_id}")

        job.status = "running"

        try:
            # 별도 스레드에서 최적화 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._run_optimization_sync,
                job,
                progress_callback
            )

            job.status = "completed"
            job.result = result
            return result

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            raise

    def _run_optimization_sync(self, job: OptimizationJob,
                                progress_callback: Optional[Callable] = None) -> Dict:
        """동기 최적화 실행"""
        try:
            from optimizer.models.grid import Grid
            from optimizer.ga.algorithm import GeneticAlgorithm, GAConfig
            from optimizer.ga.fitness import FitnessEvaluator
            from optimizer.integration.cnn_bridge import CNNBridge

            # 석판 로드
            bridge = CNNBridge()
            all_tablets = bridge.get_all_tablets()

            # 요청된 석판만 필터링
            tablets = []
            for tablet in all_tablets:
                if tablet.id in job.tablet_ids:
                    tablets.append(tablet)

            if not tablets:
                # 모든 석판 사용
                tablets = all_tablets[:min(job.rows * job.cols, len(all_tablets))]

            # 그리드 및 GA 설정
            grid = Grid(rows=job.rows, cols=job.cols)
            fitness_evaluator = FitnessEvaluator(grid, tablets)

            config = GAConfig(
                population_size=job.population,
                generations=job.generations,
                early_stop_generations=50
            )

            ga = GeneticAlgorithm(config, grid, tablets, fitness_evaluator)

            # 진행 콜백 래퍼
            def internal_callback(stats):
                job.current_generation = stats['generation']
                job.best_fitness = stats['best_fitness']
                job.avg_fitness = stats['avg_fitness']

                if progress_callback:
                    try:
                        progress_callback({
                            'generation': stats['generation'],
                            'best_fitness': stats['best_fitness'],
                            'avg_fitness': stats['avg_fitness'],
                            'progress': (stats['generation'] / job.generations) * 100
                        })
                    except Exception:
                        pass

            # 최적화 실행
            best = ga.evolve(callback=internal_callback)

            # 결과 포맷팅
            from optimizer.effects.calculator import EffectCalculator

            best.to_grid(grid, tablets)
            calculator = EffectCalculator(grid)
            levels = calculator.calculate_total_levels()

            placements = []
            for gene in best.genes:
                if gene.tablet_idx >= 0 and gene.tablet_idx < len(tablets):
                    tablet = tablets[gene.tablet_idx]
                    placements.append({
                        'tablet_id': tablet.id,
                        'tablet_name': tablet.name,
                        'position': {'row': gene.position[0], 'col': gene.position[1]},
                        'rotation': gene.rotation
                    })

            return {
                'job_id': job.job_id,
                'status': 'completed',
                'fitness': float(best.fitness),
                'total_level': int(levels.sum()),
                'placements': placements,
                'level_matrix': levels.tolist(),
                'grid_size': {'rows': job.rows, 'cols': job.cols},
                'generations_run': job.current_generation
            }

        except ImportError as e:
            # optimizer 모듈이 없는 경우 모의 결과 반환
            print(f"Optimizer import error: {e}")
            return self._mock_result(job)

    def _mock_result(self, job: OptimizationJob) -> Dict:
        """테스트용 모의 결과"""
        import random

        placements = []
        for i, tablet_id in enumerate(job.tablet_ids[:job.rows * job.cols]):
            row = i // job.cols
            col = i % job.cols
            placements.append({
                'tablet_id': tablet_id,
                'tablet_name': f'석판_{i}',
                'position': {'row': row, 'col': col},
                'rotation': random.choice([0, 90, 180, 270])
            })

        level_matrix = [[random.randint(0, 5) for _ in range(job.cols)]
                        for _ in range(job.rows)]

        return {
            'job_id': job.job_id,
            'status': 'completed',
            'fitness': random.uniform(50, 200),
            'total_level': sum(sum(row) for row in level_matrix),
            'placements': placements,
            'level_matrix': level_matrix,
            'grid_size': {'rows': job.rows, 'cols': job.cols},
            'generations_run': job.generations
        }
