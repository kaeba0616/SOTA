'use client';

import type { OptimizeResult, Placement } from '@/types';

interface ResultGridProps {
  result: OptimizeResult;
}

export default function ResultGrid({ result }: ResultGridProps) {
  if (!result.placements || !result.level_matrix || !result.grid_size) {
    return null;
  }

  const { rows, cols } = result.grid_size;
  const placements = result.placements;
  const levels = result.level_matrix;

  // 위치별 배치 맵 생성
  const placementMap = new Map<string, Placement>();
  placements.forEach((p) => {
    const key = `${p.position.row}-${p.position.col}`;
    placementMap.set(key, p);
  });

  // 레벨 색상 (음수~양수)
  function getLevelColor(level: number): string {
    if (level > 3) return 'bg-green-500';
    if (level > 1) return 'bg-green-600';
    if (level > 0) return 'bg-green-700';
    if (level === 0) return 'bg-gray-600';
    if (level > -2) return 'bg-red-700';
    return 'bg-red-500';
  }

  // 회전 스타일
  function getRotationStyle(rotation: number): React.CSSProperties {
    return {
      transform: `rotate(${rotation}deg)`,
    };
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">최적 배치 결과</h2>
        <div className="flex gap-4 text-sm">
          <span className="text-gray-400">
            적합도: <span className="text-green-400 font-bold">{result.fitness?.toFixed(1)}</span>
          </span>
          <span className="text-gray-400">
            총 레벨: <span className="text-white font-bold">{result.total_level}</span>
          </span>
        </div>
      </div>

      {/* 배치 그리드 */}
      <div className="mb-6">
        <h3 className="text-sm text-gray-400 mb-2">석판 배치</h3>
        <div
          className="inline-grid gap-1"
          style={{
            gridTemplateColumns: `repeat(${cols}, minmax(60px, 80px))`,
          }}
        >
          {Array.from({ length: rows * cols }).map((_, i) => {
            const row = Math.floor(i / cols);
            const col = i % cols;
            const key = `${row}-${col}`;
            const placement = placementMap.get(key);

            return (
              <div
                key={i}
                className="aspect-square bg-gray-700 rounded flex items-center justify-center p-1"
              >
                {placement ? (
                  <div
                    className="text-xs text-center"
                    style={getRotationStyle(placement.rotation)}
                  >
                    <div className="font-medium truncate">
                      {placement.tablet_name}
                    </div>
                    {placement.rotation !== 0 && (
                      <div className="text-gray-400 text-[10px]">
                        {placement.rotation}°
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-500 text-xs">-</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 레벨 매트릭스 */}
      <div>
        <h3 className="text-sm text-gray-400 mb-2">레벨 보너스</h3>
        <div
          className="inline-grid gap-1"
          style={{
            gridTemplateColumns: `repeat(${cols}, 40px)`,
          }}
        >
          {levels.flat().map((level, i) => (
            <div
              key={i}
              className={`w-10 h-10 rounded flex items-center justify-center font-bold ${getLevelColor(
                level
              )}`}
            >
              {level > 0 ? `+${level}` : level}
            </div>
          ))}
        </div>
      </div>

      {/* 다운로드 버튼 */}
      <div className="mt-6 flex gap-2">
        <button
          onClick={() => downloadResult(result)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
        >
          JSON 다운로드
        </button>
      </div>
    </div>
  );
}

function downloadResult(result: OptimizeResult) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `optimal_placement_${result.job_id}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
