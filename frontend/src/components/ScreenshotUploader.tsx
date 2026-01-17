'use client';

import { useState, useCallback } from 'react';
import { uploadScreenshot } from '@/lib/api';
import type { DetectedTablet } from '@/types';

interface ScreenshotUploaderProps {
  onDetected: (tablets: DetectedTablet[]) => void;
}

export default function ScreenshotUploader({
  onDetected,
}: ScreenshotUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  async function handleFile(file: File) {
    if (!file.type.startsWith('image/')) {
      setError('이미지 파일만 업로드 가능합니다');
      return;
    }

    // 미리보기 생성
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // 업로드
    try {
      setIsUploading(true);
      setError(null);
      const response = await uploadScreenshot(file);
      onDetected(response.detected);
    } catch (err) {
      setError('이미지 분석에 실패했습니다');
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">스크린샷 업로드</h2>

      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-900/20'
            : 'border-gray-600 hover:border-gray-500'
        }`}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {preview ? (
          <div className="space-y-4">
            <img
              src={preview}
              alt="Preview"
              className="max-h-48 mx-auto rounded"
            />
            {isUploading && (
              <div className="text-blue-400">분석 중...</div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-4xl">📷</div>
            <div className="text-gray-400">
              이미지를 드래그하거나 클릭하여 업로드
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileInput}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="inline-block px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded cursor-pointer"
            >
              파일 선택
            </label>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 text-red-400 text-sm">{error}</div>
      )}

      {preview && !isUploading && (
        <button
          onClick={() => {
            setPreview(null);
            onDetected([]);
          }}
          className="mt-4 text-sm text-gray-400 hover:text-white"
        >
          다른 이미지 선택
        </button>
      )}
    </div>
  );
}
