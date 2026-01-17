'use client';

import { useState } from 'react';
import TabletSelector from '@/components/TabletSelector';
import GridConfigurator from '@/components/GridConfigurator';
import ScreenshotUploader from '@/components/ScreenshotUploader';
import OptimizationProgress from '@/components/OptimizationProgress';
import ResultGrid from '@/components/ResultGrid';
import { useOptimizationWS } from '@/lib/websocket';
import { startOptimization } from '@/lib/api';
import type { DetectedTablet, OptimizeResult } from '@/types';

type InputMode = 'manual' | 'screenshot';

export default function HomePage() {
  // 입력 모드
  const [inputMode, setInputMode] = useState<InputMode>('manual');

  // 석판 선택
  const [selectedTablets, setSelectedTablets] = useState<string[]>([]);

  // 그리드 설정
  const [rows, setRows] = useState(6);
  const [cols, setCols] = useState(6);

  // 최적화 상태
  const [jobId, setJobId] = useState<string | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // WebSocket 훅
  const ws = useOptimizationWS({
    jobId,
    onComplete: (result) => {
      setResult(result);
      setIsOptimizing(false);
    },
    onError: (err) => {
      setError(err);
      setIsOptimizing(false);
    },
  });

  // 스크린샷에서 감지된 석판 처리
  function handleDetected(detected: DetectedTablet[]) {
    setSelectedTablets(detected.map((d) => d.id));
  }

  // 최적화 시작
  async function handleOptimize() {
    if (selectedTablets.length === 0) {
      setError('석판을 선택해주세요');
      return;
    }

    try {
      setError(null);
      setResult(null);
      setIsOptimizing(true);

      const response = await startOptimization({
        tablet_ids: selectedTablets,
        rows,
        cols,
      });

      setJobId(response.job_id);
    } catch (err) {
      setError('최적화 시작에 실패했습니다');
      setIsOptimizing(false);
      console.error(err);
    }
  }

  // 초기화
  function handleReset() {
    setJobId(null);
    setResult(null);
    setError(null);
    setIsOptimizing(false);
  }

  return (
    <div className="space-y-6">
      {/* 입력 모드 선택 */}
      {!isOptimizing && !result && (
        <>
          <div className="flex gap-4">
            <button
              onClick={() => setInputMode('manual')}
              className={`px-4 py-2 rounded ${
                inputMode === 'manual'
                  ? 'bg-blue-600'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              수동 선택
            </button>
            <button
              onClick={() => setInputMode('screenshot')}
              className={`px-4 py-2 rounded ${
                inputMode === 'screenshot'
                  ? 'bg-blue-600'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              스크린샷 분석
            </button>
          </div>

          {/* 입력 영역 */}
          {inputMode === 'screenshot' ? (
            <ScreenshotUploader onDetected={handleDetected} />
          ) : null}

          <TabletSelector
            selectedTablets={selectedTablets}
            onSelectionChange={setSelectedTablets}
          />

          <GridConfigurator
            rows={rows}
            cols={cols}
            onRowsChange={setRows}
            onColsChange={setCols}
          />

          {/* 최적화 버튼 */}
          <div className="flex gap-4">
            <button
              onClick={handleOptimize}
              disabled={selectedTablets.length === 0}
              className={`px-6 py-3 rounded-lg font-semibold ${
                selectedTablets.length === 0
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              최적화 시작
            </button>

            {selectedTablets.length > 0 && (
              <span className="self-center text-gray-400">
                {selectedTablets.length}개 석판 선택됨
              </span>
            )}
          </div>
        </>
      )}

      {/* 진행 상황 */}
      {isOptimizing && (
        <OptimizationProgress
          progress={ws.progress}
          isConnected={ws.isConnected}
        />
      )}

      {/* 결과 */}
      {result && (
        <>
          <ResultGrid result={result} />

          <button
            onClick={handleReset}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            다시 시작
          </button>
        </>
      )}

      {/* 에러 */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200">
          {error}
        </div>
      )}
    </div>
  );
}
