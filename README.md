# SOTA (Sephiria Optimal Tablet Arranger)

세피리아 게임의 석판 배치를 자동으로 최적화하는 시스템입니다.

## 주요 기능

- **스크린샷 분석**: CNN 모델을 사용하여 인벤토리 스크린샷에서 석판 자동 인식
- **최적 배치 계산**: 유전 알고리즘(GA)을 사용하여 레벨 합계를 최대화하는 배치 탐색
- **실시간 진행 표시**: WebSocket을 통한 최적화 진행 상황 실시간 스트리밍
- **웹 인터페이스**: 직관적인 UI로 석판 선택, 그리드 설정, 결과 시각화

## 기술 스택

| 분류 | 기술 |
|------|------|
| **Frontend** | Next.js 14, React, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, Python 3.10+, WebSocket |
| **ML/AI** | TensorFlow/Keras, OpenCV, MobileNetV2 |
| **최적화** | 유전 알고리즘 (Genetic Algorithm) |

## 프로젝트 구조

```
SOTA/
├── frontend/          # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/       # 페이지
│   │   ├── components/# React 컴포넌트
│   │   ├── lib/       # API 클라이언트, WebSocket
│   │   └── types/     # TypeScript 타입
│   └── package.json
│
├── server/            # FastAPI 백엔드
│   ├── app/
│   │   ├── routes/    # API 엔드포인트
│   │   ├── services/  # 비즈니스 로직
│   │   └── schemas/   # Pydantic 모델
│   └── requirements.txt
│
├── optimizer/         # 최적화 모듈
│   ├── models/        # Tablet, Grid 클래스
│   ├── effects/       # 효과 계산 엔진
│   ├── ga/            # 유전 알고리즘
│   └── integration/   # CNN 연동
│
├── CNN/               # 이미지 분류 모듈
│   ├── train.py       # 모델 학습
│   ├── fine_train.py  # Fine-tuning 학습
│   └── inven_test.py  # 인벤토리 분석
│
├── assets/            # 학습 데이터
│   ├── artifacts/     # 아티팩트 이미지
│   ├── tablets/       # 석판 이미지
│   └── empty/         # 빈 슬롯 이미지
│
├── tablet.json        # 석판 데이터 (효과, 제한 등)
└── docker-compose.yml
```

## 설치 및 실행

### 필수 요구사항

- Python 3.10+
- Node.js 18+
- (선택) Docker & Docker Compose

### 로컬 실행

#### 1. 백엔드 서버

```bash
# 의존성 설치
cd server
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

#### 2. 프론트엔드

```bash
# 의존성 설치
cd frontend
npm install

# 개발 서버 실행
npm run dev
```

#### 3. 접속

- 프론트엔드: http://localhost:3000
- API 문서 (Swagger): http://localhost:8000/docs

### Docker로 실행

```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

## 사용 방법

### 1. 석판 선택

- **수동 선택**: 석판 목록에서 직접 선택
- **스크린샷 분석**: 인벤토리 스크린샷 업로드 시 자동 인식

### 2. 그리드 설정

- 행(rows)과 열(cols) 크기 지정 (2~10)

### 3. 최적화 실행

- "최적화 시작" 버튼 클릭
- 실시간 진행 상황 확인 (세대, 적합도)

### 4. 결과 확인

- 최적 배치 그리드 시각화
- 레벨 보너스 매트릭스
- JSON 다운로드

## CLI 사용법

```bash
# 기본 최적화 (모든 석판, 6x6 그리드)
python -m optimizer.main --rows 6 --cols 6

# 특정 석판만 사용
python -m optimizer.main --rows 4 --cols 4 --tablets 기사도 건조 근사

# 스크린샷에서 석판 감지 후 최적화
python -m optimizer.main --rows 6 --cols 6 --screenshot ./CNN/test1.png

# GA 파라미터 조정
python -m optimizer.main --rows 6 --cols 6 --generations 1000 --population 200
```

## 문서

- [알고리즘 상세](./optimizer/ALGORITHM.md) - 유전 알고리즘 작동 방식
- [API 레퍼런스](./server/API.md) - REST API 및 WebSocket 문서

## 라이선스

MIT License
