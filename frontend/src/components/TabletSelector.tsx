'use client';

import { useState, useEffect } from 'react';
import type { Tablet } from '@/types';
import { getTablets } from '@/lib/api';

interface TabletSelectorProps {
  selectedTablets: string[];
  onSelectionChange: (tablets: string[]) => void;
}

const RARITY_COLORS: Record<string, string> = {
  '일반': 'bg-gray-600',
  '고급': 'bg-green-600',
  '희귀': 'bg-blue-600',
  '전설': 'bg-purple-600',
};

export default function TabletSelector({
  selectedTablets,
  onSelectionChange,
}: TabletSelectorProps) {
  const [tablets, setTablets] = useState<Tablet[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadTablets();
  }, []);

  async function loadTablets() {
    try {
      setLoading(true);
      const response = await getTablets();
      setTablets(response.tablets);
    } catch (error) {
      console.error('석판 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  }

  function toggleTablet(tabletId: string) {
    if (selectedTablets.includes(tabletId)) {
      onSelectionChange(selectedTablets.filter((id) => id !== tabletId));
    } else {
      onSelectionChange([...selectedTablets, tabletId]);
    }
  }

  function selectAll() {
    const filtered = getFilteredTablets();
    onSelectionChange(filtered.map((t) => t.id));
  }

  function deselectAll() {
    onSelectionChange([]);
  }

  function getFilteredTablets() {
    if (filter === 'all') return tablets;
    return tablets.filter((t) => t.rarity === filter);
  }

  const filteredTablets = getFilteredTablets();

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-4 gap-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">
          석판 선택 ({selectedTablets.length}/{tablets.length})
        </h2>
        <div className="flex gap-2">
          <button
            onClick={selectAll}
            className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 rounded"
          >
            전체 선택
          </button>
          <button
            onClick={deselectAll}
            className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-700 rounded"
          >
            선택 해제
          </button>
        </div>
      </div>

      {/* 필터 */}
      <div className="flex gap-2 mb-4">
        {['all', '일반', '고급', '희귀', '전설'].map((rarity) => (
          <button
            key={rarity}
            onClick={() => setFilter(rarity)}
            className={`px-3 py-1 text-sm rounded ${
              filter === rarity
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {rarity === 'all' ? '전체' : rarity}
          </button>
        ))}
      </div>

      {/* 석판 그리드 */}
      <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2 max-h-64 overflow-y-auto">
        {filteredTablets.map((tablet) => (
          <button
            key={tablet.id}
            onClick={() => toggleTablet(tablet.id)}
            className={`p-2 rounded border-2 transition-all ${
              selectedTablets.includes(tablet.id)
                ? 'border-blue-500 bg-blue-900/30'
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="text-xs truncate">{tablet.name}</div>
            <div
              className={`text-xs mt-1 px-1 rounded ${
                RARITY_COLORS[tablet.rarity] || 'bg-gray-600'
              }`}
            >
              {tablet.rarity}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
