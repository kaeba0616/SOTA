'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WSMessage, ProgressMessage, OptimizeResult } from '@/types';

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseOptimizationWSProps {
  jobId: string | null;
  onProgress?: (progress: ProgressMessage) => void;
  onComplete?: (result: OptimizeResult) => void;
  onError?: (error: string) => void;
}

interface UseOptimizationWSReturn {
  isConnected: boolean;
  progress: ProgressMessage | null;
  result: OptimizeResult | null;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
}

export function useOptimizationWS({
  jobId,
  onProgress,
  onComplete,
  onError,
}: UseOptimizationWSProps): UseOptimizationWSReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState<ProgressMessage | null>(null);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    if (!jobId || wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/ws/optimize/${jobId}`);

    ws.onopen = () => {
      console.log('WebSocket 연결됨');
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'progress':
            setProgress(message);
            onProgress?.(message);
            break;

          case 'complete':
            setResult(message.result);
            onComplete?.(message.result);
            break;

          case 'error':
            setError(message.message);
            onError?.(message.message);
            break;
        }
      } catch (e) {
        console.error('메시지 파싱 오류:', e);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket 오류:', event);
      setError('WebSocket 연결 오류');
      onError?.('WebSocket 연결 오류');
    };

    ws.onclose = () => {
      console.log('WebSocket 연결 종료');
      setIsConnected(false);
    };

    wsRef.current = ws;
  }, [jobId, onProgress, onComplete, onError]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // jobId 변경 시 자동 연결
  useEffect(() => {
    if (jobId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [jobId, connect, disconnect]);

  return {
    isConnected,
    progress,
    result,
    error,
    connect,
    disconnect,
  };
}
