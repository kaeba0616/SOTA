'use client';

interface GridConfiguratorProps {
  rows: number;
  cols: number;
  onRowsChange: (rows: number) => void;
  onColsChange: (cols: number) => void;
}

export default function GridConfigurator({
  rows,
  cols,
  onRowsChange,
  onColsChange,
}: GridConfiguratorProps) {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">그리드 설정</h2>

      <div className="flex gap-8">
        <div>
          <label className="block text-sm text-gray-400 mb-2">행 (Rows)</label>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onRowsChange(Math.max(2, rows - 1))}
              className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded"
            >
              -
            </button>
            <span className="w-12 text-center text-xl font-bold">{rows}</span>
            <button
              onClick={() => onRowsChange(Math.min(10, rows + 1))}
              className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded"
            >
              +
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">열 (Cols)</label>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onColsChange(Math.max(2, cols - 1))}
              className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded"
            >
              -
            </button>
            <span className="w-12 text-center text-xl font-bold">{cols}</span>
            <button
              onClick={() => onColsChange(Math.min(10, cols + 1))}
              className="w-8 h-8 bg-gray-700 hover:bg-gray-600 rounded"
            >
              +
            </button>
          </div>
        </div>

        <div className="flex items-end">
          <div className="text-gray-400">
            총 <span className="text-white font-bold">{rows * cols}</span> 칸
          </div>
        </div>
      </div>

      {/* 미리보기 그리드 */}
      <div className="mt-4">
        <div
          className="inline-grid gap-1"
          style={{
            gridTemplateColumns: `repeat(${cols}, 24px)`,
            gridTemplateRows: `repeat(${rows}, 24px)`,
          }}
        >
          {Array.from({ length: rows * cols }).map((_, i) => (
            <div
              key={i}
              className="w-6 h-6 bg-gray-700 rounded-sm"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
