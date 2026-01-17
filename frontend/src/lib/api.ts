import type {
  TabletListResponse,
  UploadResponse,
  OptimizeRequest,
  OptimizeResponse,
  OptimizeResult,
  Tablet,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// 석판 목록 조회
export async function getTablets(rarity?: string): Promise<TabletListResponse> {
  const params = rarity ? `?rarity=${rarity}` : '';
  const response = await fetch(`${API_BASE}/api/tablets${params}`);

  if (!response.ok) {
    throw new Error('석판 목록을 불러오는데 실패했습니다');
  }

  return response.json();
}

// 특정 석판 조회
export async function getTablet(tabletId: string): Promise<Tablet> {
  const response = await fetch(`${API_BASE}/api/tablets/${tabletId}`);

  if (!response.ok) {
    throw new Error('석판을 찾을 수 없습니다');
  }

  return response.json();
}

// 스크린샷 업로드
export async function uploadScreenshot(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('이미지 업로드에 실패했습니다');
  }

  return response.json();
}

// 최적화 시작
export async function startOptimization(
  request: OptimizeRequest
): Promise<OptimizeResponse> {
  const response = await fetch(`${API_BASE}/api/optimize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('최적화 시작에 실패했습니다');
  }

  return response.json();
}

// 최적화 결과 조회
export async function getOptimizationResult(
  jobId: string
): Promise<OptimizeResult> {
  const response = await fetch(`${API_BASE}/api/optimize/${jobId}`);

  if (!response.ok) {
    throw new Error('결과를 불러오는데 실패했습니다');
  }

  return response.json();
}
