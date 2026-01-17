# SOTA API Reference

SOTA 서버의 REST API 및 WebSocket 프로토콜 문서입니다.

## 기본 정보

| 항목 | 값 |
|-----|---|
| Base URL | `http://localhost:8000` |
| WebSocket URL | `ws://localhost:8000` |
| API Prefix | `/api` |
| Content-Type | `application/json` |

## 목차

1. [석판 API](#석판-api)
2. [이미지 업로드 API](#이미지-업로드-api)
3. [최적화 API](#최적화-api)
4. [WebSocket 프로토콜](#websocket-프로토콜)
5. [에러 코드](#에러-코드)
6. [데이터 모델](#데이터-모델)

---

## 석판 API

### GET /api/tablets

모든 석판 목록을 조회합니다.

#### Query Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|-----|-----|------|
| `rarity` | string | No | 희귀도 필터 (`일반`, `고급`, `희귀`, `전설`) |

#### Request

```bash
curl http://localhost:8000/api/tablets
curl http://localhost:8000/api/tablets?rarity=전설
```

#### Response

```json
{
  "tablets": [
    {
      "id": "tb_001",
      "name": "기사도",
      "image_url": "/assets/tablets/tb_001.png",
      "rotatable": true,
      "rarity": "희귀",
      "restriction": null,
      "effects": [
        {
          "pos": [1, 0],
          "shape": null,
          "type": "level_add",
          "value": 2
        }
      ]
    }
  ],
  "total": 42
}
```

---

### GET /api/tablets/{tablet_id}

특정 석판의 상세 정보를 조회합니다.

#### Path Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|-----|-----|------|
| `tablet_id` | string | Yes | 석판 ID (예: `tb_001`) |

#### Request

```bash
curl http://localhost:8000/api/tablets/tb_001
```

#### Response

```json
{
  "id": "tb_001",
  "name": "기사도",
  "image_url": "/assets/tablets/tb_001.png",
  "rotatable": true,
  "rarity": "희귀",
  "restriction": null,
  "effects": [
    {
      "pos": [1, 0],
      "shape": null,
      "type": "level_add",
      "value": 2
    },
    {
      "pos": [-1, 0],
      "shape": null,
      "type": "level_add",
      "value": 1
    }
  ]
}
```

#### Error Response

```json
{
  "detail": "석판을 찾을 수 없습니다"
}
```

---

## 이미지 업로드 API

### POST /api/upload

인벤토리 스크린샷을 업로드하고 CNN으로 석판을 감지합니다.

#### Request

```bash
curl -X POST \
  http://localhost:8000/api/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@screenshot.png"
```

#### Request Body (multipart/form-data)

| 필드 | 타입 | 필수 | 설명 |
|-----|-----|-----|------|
| `file` | file | Yes | 이미지 파일 (PNG, JPG) |

#### Response

```json
{
  "detected": [
    {
      "id": "tb_001",
      "name": "기사도",
      "confidence": 0.95,
      "slot_index": 0
    },
    {
      "id": "tb_002",
      "name": "건조",
      "confidence": 0.92,
      "slot_index": 1
    }
  ],
  "total_slots": 2,
  "image_size": {
    "width": 1920,
    "height": 1080
  }
}
```

#### Error Response

```json
{
  "detail": "이미지 파일만 업로드 가능합니다"
}
```

---

## 최적화 API

### POST /api/optimize

최적화 작업을 시작합니다. 비동기로 실행되며 job_id를 반환합니다.

#### Request

```bash
curl -X POST \
  http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "tablet_ids": ["tb_001", "tb_002", "tb_003"],
    "rows": 6,
    "cols": 6,
    "generations": 500,
    "population": 100
  }'
```

#### Request Body

| 필드 | 타입 | 필수 | 설명 | 기본값 | 범위 |
|-----|-----|-----|------|-------|------|
| `tablet_ids` | string[] | Yes | 사용할 석판 ID 목록 | - | - |
| `rows` | int | Yes | 그리드 행 수 | - | 2-10 |
| `cols` | int | Yes | 그리드 열 수 | - | 2-10 |
| `generations` | int | No | GA 세대 수 | 500 | 50-2000 |
| `population` | int | No | 인구 크기 | 100 | 20-500 |

#### Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "최적화 작업이 생성되었습니다. WebSocket으로 진행상황을 확인하세요."
}
```

---

### GET /api/optimize/{job_id}

최적화 결과를 조회합니다.

#### Path Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|-----|-----|------|
| `job_id` | string | Yes | 최적화 작업 ID |

#### Request

```bash
curl http://localhost:8000/api/optimize/550e8400-e29b-41d4-a716-446655440000
```

#### Response (진행 중)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "fitness": 125.5,
  "total_level": null,
  "placements": null,
  "level_matrix": null,
  "grid_size": {
    "rows": 6,
    "cols": 6
  },
  "generations_run": 150
}
```

#### Response (완료)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "fitness": 256.0,
  "total_level": 256,
  "placements": [
    {
      "tablet_id": "tb_001",
      "tablet_name": "기사도",
      "position": {"row": 0, "col": 0},
      "rotation": 0
    },
    {
      "tablet_id": "tb_002",
      "tablet_name": "건조",
      "position": {"row": 0, "col": 1},
      "rotation": 90
    }
  ],
  "level_matrix": [
    [5, 3, 2, 4, 1, 2],
    [3, 6, 4, 3, 2, 1],
    [2, 4, 5, 4, 3, 2],
    [4, 3, 4, 6, 4, 3],
    [1, 2, 3, 4, 5, 4],
    [2, 1, 2, 3, 4, 5]
  ],
  "grid_size": {
    "rows": 6,
    "cols": 6
  },
  "generations_run": 500
}
```

---

## WebSocket 프로토콜

### WS /ws/optimize/{job_id}

최적화 진행상황을 실시간으로 스트리밍합니다.

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/optimize/550e8400-e29b-41d4-a716-446655440000');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

#### Message Types

##### 1. Progress Message

최적화 진행 중 세대별 상태를 전송합니다.

```json
{
  "type": "progress",
  "generation": 150,
  "best_fitness": 125.5,
  "avg_fitness": 98.3,
  "progress": 30.0
}
```

| 필드 | 타입 | 설명 |
|-----|-----|------|
| `type` | string | 항상 `"progress"` |
| `generation` | int | 현재 세대 |
| `best_fitness` | float | 최고 적합도 |
| `avg_fitness` | float | 평균 적합도 |
| `progress` | float | 진행률 (0-100) |

##### 2. Complete Message

최적화 완료 시 결과를 전송합니다.

```json
{
  "type": "complete",
  "result": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "fitness": 256.0,
    "total_level": 256,
    "placements": [...],
    "level_matrix": [...],
    "grid_size": {"rows": 6, "cols": 6},
    "generations_run": 500
  }
}
```

##### 3. Error Message

에러 발생 시 전송합니다.

```json
{
  "type": "error",
  "message": "작업을 찾을 수 없습니다"
}
```

#### WebSocket 사용 예시

```javascript
function runOptimization(tabletIds, rows, cols) {
  // 1. 작업 생성
  fetch('/api/optimize', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      tablet_ids: tabletIds,
      rows: rows,
      cols: cols
    })
  })
  .then(res => res.json())
  .then(data => {
    const jobId = data.job_id;

    // 2. WebSocket 연결
    const ws = new WebSocket(`ws://localhost:8000/ws/optimize/${jobId}`);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case 'progress':
          console.log(`Generation ${msg.generation}: ${msg.best_fitness}`);
          updateProgressBar(msg.progress);
          break;

        case 'complete':
          console.log('Optimization complete!', msg.result);
          displayResult(msg.result);
          break;

        case 'error':
          console.error('Error:', msg.message);
          break;
      }
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };
  });
}
```

---

## 에러 코드

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|-----|-----|------|
| 200 | OK | 요청 성공 |
| 400 | Bad Request | 잘못된 요청 (파라미터 오류 등) |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 422 | Unprocessable Entity | 유효성 검사 실패 |
| 500 | Internal Server Error | 서버 내부 오류 |

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

### 유효성 검사 오류

```json
{
  "detail": [
    {
      "loc": ["body", "rows"],
      "msg": "ensure this value is greater than or equal to 2",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

## 데이터 모델

### Tablet

| 필드 | 타입 | 설명 |
|-----|-----|------|
| `id` | string | 석판 고유 ID |
| `name` | string | 석판 이름 |
| `image_url` | string | 이미지 경로 |
| `rotatable` | boolean | 회전 가능 여부 |
| `rarity` | string | 희귀도 (`일반`, `고급`, `희귀`, `전설`) |
| `restriction` | string? | 배치 제한 (`edge`, `corner`, `center`) |
| `effects` | Effect[] | 효과 목록 |

### Effect

| 필드 | 타입 | 설명 |
|-----|-----|------|
| `pos` | [int, int]? | 상대 위치 [dx, dy] |
| `shape` | string? | 형태 (`row`, `column`, `diagonal`) |
| `type` | string | 효과 타입 (`level_add`, `restriction_remove`) |
| `value` | any | 효과 값 |

### DetectedTablet

| 필드 | 타입 | 설명 |
|-----|-----|------|
| `id` | string | 석판 ID |
| `name` | string | 석판 이름 |
| `confidence` | float | 신뢰도 (0-1) |
| `slot_index` | int | 슬롯 인덱스 |

### OptimizeResult

| 필드 | 타입 | 설명 |
|-----|-----|------|
| `job_id` | string | 작업 ID |
| `status` | string | 상태 (`pending`, `running`, `completed`, `failed`) |
| `fitness` | float? | 최종 적합도 |
| `total_level` | int? | 총 레벨 합계 |
| `placements` | Placement[]? | 배치 결과 |
| `level_matrix` | int[][]? | 레벨 매트릭스 |
| `grid_size` | {rows, cols} | 그리드 크기 |
| `generations_run` | int? | 실행된 세대 수 |

### Placement

| 필드 | 타입 | 설명 |
|-----|-----|------|
| `tablet_id` | string | 석판 ID |
| `tablet_name` | string | 석판 이름 |
| `position` | {row, col} | 배치 위치 |
| `rotation` | int | 회전 각도 (0, 90, 180, 270) |

---

## Swagger UI

자동 생성된 API 문서를 확인하려면:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
