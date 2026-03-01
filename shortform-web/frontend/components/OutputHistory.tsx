"use client";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface OutputFile {
  filename: string;
  size_mb: number;
  created_at: string;
}

interface Props {
  refreshKey?: string;
}

export default function OutputHistory({ refreshKey }: Props) {
  const [files, setFiles] = useState<OutputFile[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/api/output/list`)
      .then((r) => r.json())
      .then((data) => setFiles(data.files || []))
      .catch(() => {});
  }, [refreshKey]);

  if (files.length === 0) return null;

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return `${d.getMonth() + 1}월 ${d.getDate()}일 ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
  };

  return (
    <div className="mt-8 pt-8 border-t border-gray-800">
      <h2 className="text-lg font-semibold mb-4">최근 완성 영상 ({files.length}개)</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {files.map((f) => (
          <div key={f.filename} className="bg-gray-800 rounded-lg overflow-hidden">
            <video
              src={`${API_URL}/api/download/${f.filename}`}
              className="w-full"
              style={{ aspectRatio: "9/16", maxHeight: "200px", objectFit: "cover" }}
              preload="metadata"
              muted
            />
            <div className="p-3">
              <p className="text-sm text-gray-300 truncate">{f.filename}</p>
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-gray-500">
                  {f.size_mb}MB · {formatDate(f.created_at)}
                </span>
                <a
                  href={`${API_URL}/api/download/${f.filename}`}
                  download
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  다운로드
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
