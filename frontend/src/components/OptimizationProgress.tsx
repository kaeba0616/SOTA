'use client';

import type { ProgressMessage } from '@/types';

interface OptimizationProgressProps {
  progress: ProgressMessage | null;
  isConnected: boolean;
}

export default function OptimizationProgress({
  progress,
  isConnected,
}: OptimizationProgressProps) {
  if (!isConnected && !progress) {
    return null;
  }

  const progressPct = progress?.progress || 0;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">최적화 진행 중...</h2>

      {/* 진행바 */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-400 mb-1">
          <span>진행률</span>
          <span>{progressPct.toFixed(1)}%</span>
        </div>
        <div className="h-4 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* 상세 정보 */}
      {progress && (
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-gray-700/50 rounded p-3">
            <div className="text-gray-400 text-sm">세대</div>
            <div className="text-xl font-bold">{progress.generation}</div>
          </div>
          <div className="bg-gray-700/50 rounded p-3">
            <div className="text-gray-400 text-sm">최고 적합도</div>
            <div className="text-xl font-bold text-green-400">
              {progress.best_fitness.toFixed(1)}
            </div>
          </div>
          <div className="bg-gray-700/50 rounded p-3">
            <div className="text-gray-400 text-sm">평균 적합도</div>
            <div className="text-xl font-bold">
              {progress.avg_fitness.toFixed(1)}
            </div>
          </div>
        </div>
      )}

      {/* 연결 상태 */}
      <div className="mt-4 flex items-center gap-2 text-sm">
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className="text-gray-400">
          {isConnected ? '서버 연결됨' : '연결 끊김'}
        </span>
      </div>
    </div>
  );
}
