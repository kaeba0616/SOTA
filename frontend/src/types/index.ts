// 석판 타입
export interface Tablet {
  id: string;
  name: string;
  image_url: string;
  rotatable: boolean;
  rarity: string;
  restriction: string | null;
  effects: Effect[];
}

export interface Effect {
  pos?: number[];
  shape?: string;
  type: string;
  value: number | boolean;
}

// API 응답 타입
export interface TabletListResponse {
  tablets: Tablet[];
  total: number;
}

export interface DetectedTablet {
  id: string;
  name: string;
  confidence: number;
  slot_index: number;
}

export interface UploadResponse {
  detected: DetectedTablet[];
  total_slots: number;
  image_size: { width: number; height: number };
}

export interface OptimizeRequest {
  tablet_ids: string[];
  rows: number;
  cols: number;
  generations?: number;
  population?: number;
}

export interface OptimizeResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface Placement {
  tablet_id: string;
  tablet_name: string;
  position: { row: number; col: number };
  rotation: number;
}

export interface OptimizeResult {
  job_id: string;
  status: string;
  fitness: number | null;
  total_level: number | null;
  placements: Placement[] | null;
  level_matrix: number[][] | null;
  grid_size: { rows: number; cols: number } | null;
  generations_run: number | null;
}

// WebSocket 메시지 타입
export interface ProgressMessage {
  type: 'progress';
  generation: number;
  best_fitness: number;
  avg_fitness: number;
  progress: number;
}

export interface CompleteMessage {
  type: 'complete';
  result: OptimizeResult;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export type WSMessage = ProgressMessage | CompleteMessage | ErrorMessage;
