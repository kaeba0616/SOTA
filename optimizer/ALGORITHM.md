# SOTA 최적화 알고리즘

이 문서는 SOTA의 석판 배치 최적화에 사용되는 유전 알고리즘(GA)의 작동 원리를 설명합니다.

## 목차

1. [전체 흐름](#전체-흐름)
2. [염색체 인코딩](#염색체-인코딩)
3. [좌표계 변환](#좌표계-변환)
4. [효과 계산](#효과-계산)
5. [적합도 함수](#적합도-함수)
6. [유전 연산자](#유전-연산자)
7. [파라미터 설정](#파라미터-설정)
8. [사용 예시](#사용-예시)

---

## 전체 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                        유전 알고리즘 흐름                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐                                              │
│   │  초기 인구    │  랜덤 염색체 100개 생성                         │
│   │   생성       │  (석판 배치 조합)                               │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐                                              │
│   │  적합도 평가  │  각 염색체의 점수 계산                          │
│   │              │  (레벨 합계 - 패널티)                          │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐     NO                                       │
│   │  종료 조건?  │────────────┐                                  │
│   │              │            │                                  │
│   └──────┬───────┘            │                                  │
│          │ YES                │                                  │
│          ▼                    │                                  │
│   ┌──────────────┐            │                                  │
│   │  최적 해 반환 │            │                                  │
│   │              │            │                                  │
│   └──────────────┘            │                                  │
│                               │                                  │
│          ┌────────────────────┘                                  │
│          ▼                                                      │
│   ┌──────────────┐                                              │
│   │  엘리트 보존  │  상위 5개 개체 유지                             │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐                                              │
│   │  선택        │  토너먼트 방식 (3개 중 최고)                     │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐                                              │
│   │  교차        │  PMX (부분 매핑 교차)                          │
│   │              │  확률: 80%                                    │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐                                              │
│   │  돌연변이    │  스왑/회전/스크램블                             │
│   │              │  확률: 10%/15%/5%                             │
│   └──────┬───────┘                                              │
│          │                                                      │
│          └──────────────────────────────────────────────┐       │
│                                                         │       │
│                      (새로운 세대로 반복)                 ▲       │
│                                                         │       │
└─────────────────────────────────────────────────────────────────┘
```

### 종료 조건

1. **최대 세대 도달**: 기본값 500세대
2. **조기 종료**: 50세대 동안 개선이 없으면 중단

---

## 염색체 인코딩

### 기본 구조

염색체는 그리드의 각 셀에 어떤 석판이 배치되는지를 나타내는 유전자(Gene)의 배열입니다.

```
염색체 = [Gene₀, Gene₁, Gene₂, ..., Gene_{rows×cols-1}]

Gene = {
    tablet_idx: int,     # 석판 인덱스 (-1 = 빈 셀)
    position: (row, col), # 그리드 위치
    rotation: int         # 회전 각도 (0, 90, 180, 270)
}
```

### 인코딩 예시

4x4 그리드에 5개 석판을 배치하는 경우:

```
석판 목록: [기사도, 건조, 용맹, 근사, 인내]
         idx: 0    1    2    3    4

┌────────────────────────────────────┐
│ 4x4 Grid (16 cells)                │
├────┬────┬────┬────┬────────────────┤
│ 0  │ 1  │ 2  │ 3  │  ← position idx│
├────┼────┼────┼────┤                │
│ 4  │ 5  │ 6  │ 7  │                │
├────┼────┼────┼────┤                │
│ 8  │ 9  │ 10 │ 11 │                │
├────┼────┼────┼────┤                │
│ 12 │ 13 │ 14 │ 15 │                │
└────┴────┴────┴────┘                │

염색체 예시:
genes[0]  = Gene(tablet_idx=2,  position=(0,0), rotation=0)   # 용맹
genes[1]  = Gene(tablet_idx=-1, position=(0,1), rotation=0)   # 빈 셀
genes[2]  = Gene(tablet_idx=0,  position=(0,2), rotation=90)  # 기사도
genes[3]  = Gene(tablet_idx=4,  position=(0,3), rotation=0)   # 인내
...
genes[15] = Gene(tablet_idx=1,  position=(3,3), rotation=180) # 건조
```

### 순열 제약 조건

- 각 석판은 **한 번만** 사용 가능
- 석판 수 < 셀 수일 때 일부 셀은 빈 상태 (`tablet_idx = -1`)
- 회전은 `rotatable=true`인 석판만 적용

---

## 좌표계 변환

### 문제 정의

`tablet.json`의 효과 좌표와 그리드 좌표계가 다릅니다:

```
tablet.json 좌표계          그리드 좌표계
(게임 내 기준)              (배열 인덱스 기준)

      +y (위)                  row=0 ──────→
        ↑                         │  (0,0) (0,1) (0,2)
        │                         │  (1,0) (1,1) (1,2)
 -x ←───┼───→ +x                  ↓  (2,0) (2,1) (2,2)
        │                        col
        ↓
      -y (아래)
```

### 변환 공식

```
target_row = source_row - effect.dy
target_col = source_col + effect.dx
```

### 변환 예시

석판이 `(row=2, col=2)`에 있고, 효과가 `{dx: -1, dy: +1}`인 경우:

```
효과: 왼쪽 위 셀에 레벨 +2

tablet.json: dx=-1 (왼쪽), dy=+1 (위)
             ↓
변환 적용:   target_row = 2 - (+1) = 1
             target_col = 2 + (-1) = 1
             ↓
결과:        (1, 1) 셀에 레벨 +2 적용

┌────┬────┬────┬────┐
│    │    │    │    │  row=0
├────┼────┼────┼────┤
│    │ +2 │    │    │  row=1  ← 효과 적용됨
├────┼────┼────┼────┤
│    │    │ ★  │    │  row=2  ★ = 석판 위치
├────┼────┼────┼────┤
│    │    │    │    │  row=3
└────┴────┴────┴────┘
     col=0 col=1 col=2 col=3
```

### 회전 시 좌표 변환

회전 가능한 석판은 효과 좌표도 회전해야 합니다:

```
원본 (dx, dy)에 대해:

  0°: (dx, dy)     → ( dx,  dy)
 90°: (dx, dy)     → ( dy, -dx)
180°: (dx, dy)     → (-dx, -dy)
270°: (dx, dy)     → (-dy,  dx)
```

---

## 효과 계산

### 효과 타입

1. **position_effects**: 상대 위치 기반 효과
   - `level_add`: 레벨 보너스 추가
   - `restriction_remove`: 배치 제한 해제

2. **shape_effects**: 형태 기반 효과
   - `row`: 같은 행 전체
   - `column`: 같은 열 전체
   - `diagonal`: 대각선 전체
   - `top`: 위쪽 영역 전체
   - `bottom`: 아래쪽 영역 전체

### 처리 순서

**2-패스 시스템**으로 효과를 처리합니다:

```
Pass 1: restriction_remove 효과 적용
        ↓
        제한 해제된 셀 마킹
        ↓
Pass 2: level_add 효과 적용
        ↓
        최종 레벨 매트릭스 생성
```

### 효과 계산 예시

```
석판 A (row=1, col=1):
  position_effects: [{dx:1, dy:0, type:"level_add", value:2}]  # 오른쪽 +2

석판 B (row=1, col=2):
  shape_effects: [{shape:"column", type:"level_add", value:1}] # 같은 열 +1

결과:
┌────┬────┬────┬────┐
│ 0  │ 0  │ +1 │ 0  │  ← B의 column 효과
├────┼────┼────┼────┤
│ 0  │ A  │ B  │ 0  │  ← A→B로 +2 (무시: 자신에게)
├────┼────┼────┼────┤
│ 0  │ 0  │ +1 │ 0  │  ← B의 column 효과
├────┼────┼────┼────┤
│ 0  │ 0  │ +1 │ 0  │  ← B의 column 효과
└────┴────┴────┴────┘
```

---

## 적합도 함수

### 공식

```
Fitness = BaseScore + Penalty + RarityBonus

BaseScore = Σ(모든 셀의 total_level)

Penalty:
  - 제한 위반 배치: -1000 per violation

RarityBonus:
  - 미사용 전설 석판: -50 per tablet
  - 미사용 희귀 석판: -20 per tablet
```

### 점수 계산 예시

```
그리드 상태:
┌─────┬─────┬─────┐
│ Lv5 │ Lv3 │ Lv2 │
├─────┼─────┼─────┤
│ Lv4 │ Lv6 │ Lv1 │
├─────┼─────┼─────┤
│ Lv2 │ Lv3 │ Lv4 │
└─────┴─────┴─────┘

BaseScore = 5+3+2+4+6+1+2+3+4 = 30

제한 위반 1건: Penalty = -1000
미사용 전설 1개: RarityBonus = -50

Total Fitness = 30 + (-1000) + (-50) = -1020
```

### 적합도 구성 요소 (상세)

```python
{
    'base_fitness': 30,          # 레벨 합계
    'restriction_penalty': -1000, # 제한 위반 패널티
    'rarity_bonus': -50,          # 희귀도 패널티
    'total': -1020                # 최종 점수
}
```

---

## 유전 연산자

### 1. 선택 (Selection)

**토너먼트 선택**을 사용합니다:

```
Tournament Selection (k=3):

인구: [A(80), B(65), C(90), D(75), E(85), ...]

      랜덤 3개 선택: [B(65), C(90), E(85)]
                           ↓
      최고 적합도 선택:   C(90) ✓
```

### 2. 교차 (Crossover)

**PMX (Partially Mapped Crossover)**를 사용합니다:

```
Parent 1: [A, B, C, D, E, F]
Parent 2: [D, E, A, F, B, C]

교차점:      ↑     ↑
           cx1   cx2

Step 1: 세그먼트 복사
Child 1:  [_, B, C, D, _, _]
Child 2:  [_, E, A, F, _, _]

Step 2: 나머지 채우기 (유일성 유지)
Child 1:  [A, B, C, D, E, F]  ← Parent 2에서 미사용 석판
Child 2:  [D, E, A, F, B, C]  ← Parent 1에서 미사용 석판
```

### 3. 돌연변이 (Mutation)

세 가지 돌연변이 연산자를 사용합니다:

#### 스왑 돌연변이 (10%)

```
Before: [A, B, C, D, E]
              ↑     ↑
              swap
After:  [A, D, C, B, E]
```

#### 회전 돌연변이 (15%)

```
Before: Gene(tablet=A, rotation=0°)
                           ↓
After:  Gene(tablet=A, rotation=90°)  # 또는 180°, 270°
```

#### 스크램블 돌연변이 (5%)

```
Before: [A, B, C, D, E, F]
              ↑─────↑
              scramble 구간

After:  [A, D, C, B, E, F]  # 구간 내 랜덤 셔플
```

---

## 파라미터 설정

### 기본 파라미터 (GAConfig)

| 파라미터 | 기본값 | 설명 |
|---------|-------|------|
| `population_size` | 100 | 인구 크기 |
| `generations` | 500 | 최대 세대 수 |
| `crossover_rate` | 0.8 | 교차 확률 (80%) |
| `mutation_rate` | 0.1 | 스왑 돌연변이 확률 (10%) |
| `rotation_mutation_rate` | 0.15 | 회전 돌연변이 확률 (15%) |
| `scramble_mutation_rate` | 0.05 | 스크램블 돌연변이 확률 (5%) |
| `elitism_count` | 5 | 엘리트 보존 개체 수 |
| `tournament_size` | 3 | 토너먼트 크기 |
| `early_stop_generations` | 50 | 조기 종료 기준 세대 |

### 파라미터 튜닝 가이드

| 상황 | 권장 설정 |
|-----|---------|
| 빠른 결과 필요 | `generations=200`, `population=50` |
| 높은 품질 필요 | `generations=1000`, `population=200` |
| 작은 그리드 (4x4) | `population=50`, `early_stop=30` |
| 큰 그리드 (8x8+) | `population=200`, `mutation_rate=0.15` |
| 많은 석판 (30+) | `scramble_rate=0.1`, `elitism=10` |

---

## 사용 예시

### CLI 사용

```bash
# 기본 실행 (6x6 그리드, 모든 석판)
python -m optimizer.main --rows 6 --cols 6

# 특정 석판만 사용
python -m optimizer.main --rows 4 --cols 4 --tablets 기사도 건조 근사

# GA 파라미터 조정
python -m optimizer.main --rows 6 --cols 6 \
    --generations 1000 \
    --population 200 \
    --mutation-rate 0.15

# 스크린샷에서 석판 감지 후 최적화
python -m optimizer.main --rows 6 --cols 6 --screenshot ./test.png
```

### Python API 사용

```python
from optimizer.models.tablet import Tablet
from optimizer.models.grid import Grid
from optimizer.ga.algorithm import GeneticAlgorithm, GAConfig
from optimizer.ga.fitness import FitnessEvaluator

# 석판 및 그리드 설정
tablets = Tablet.load_from_json("tablet.json")
grid = Grid(rows=6, cols=6)

# GA 설정
config = GAConfig(
    population_size=100,
    generations=500,
    crossover_rate=0.8,
    mutation_rate=0.1
)

# 알고리즘 실행
ga = GeneticAlgorithm(config, grid, tablets)
best = ga.evolve(callback=lambda stats: print(f"Gen {stats['generation']}: {stats['best_fitness']:.2f}"))

# 결과 확인
print(f"최적 적합도: {best.fitness}")
best.to_grid(grid, tablets)
print(grid)
```

### 진행 콜백 사용

```python
def progress_callback(stats):
    """세대별 진행 상황 출력"""
    print(f"세대 {stats['generation']:4d} | "
          f"최고: {stats['best_fitness']:8.2f} | "
          f"평균: {stats['avg_fitness']:8.2f} | "
          f"최저: {stats['min_fitness']:8.2f}")

ga.evolve(callback=progress_callback)
```

### 수렴 데이터 시각화

```python
import matplotlib.pyplot as plt

# GA 실행 후 수렴 데이터 가져오기
data = ga.get_convergence_data()

generations = [d['generation'] for d in data]
best_fitness = [d['best_fitness'] for d in data]
avg_fitness = [d['avg_fitness'] for d in data]

plt.figure(figsize=(10, 6))
plt.plot(generations, best_fitness, label='Best')
plt.plot(generations, avg_fitness, label='Average')
plt.xlabel('Generation')
plt.ylabel('Fitness')
plt.legend()
plt.title('GA Convergence')
plt.show()
```

---

## 참고 자료

- **유전 알고리즘**: [Wikipedia - Genetic Algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm)
- **PMX 교차**: Goldberg & Lingle (1985) - "Alleles, Loci, and the Traveling Salesman Problem"
- **토너먼트 선택**: Miller & Goldberg (1995) - "Genetic Algorithms, Tournament Selection, and the Effects of Noise"
