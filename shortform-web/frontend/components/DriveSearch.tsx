"use client";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Clip {
  filename: string;
  path: string;
  rel_path: string;
  size_mb: number;
}

interface Props {
  onSelect: (businessName: string, clipPaths: string[]) => void;
}

export default function DriveSearch({ onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ name: string }[]>([]);
  const [selectedBiz, setSelectedBiz] = useState("");
  const [clips, setClips] = useState<Clip[]>([]);
  const [selectedClips, setSelectedClips] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/drive/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(data.businesses || []);
      setSelectedBiz("");
      setClips([]);
      setSelectedClips([]);
    } finally {
      setLoading(false);
    }
  };

  const loadClips = async (bizName: string) => {
    setSelectedBiz(bizName);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/drive/clips/${encodeURIComponent(bizName)}`);
      const data = await res.json();
      setClips(data.clips || []);
      setSelectedClips((data.clips || []).map((c: Clip) => c.path));
    } finally {
      setLoading(false);
    }
  };

  const toggleClip = (path: string) => {
    setSelectedClips((prev) =>
      prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path]
    );
  };

  const confirm = () => {
    if (selectedClips.length > 0) {
      onSelect(selectedBiz, selectedClips);
    }
  };

  return (
    <div className="space-y-3">
      {/* 검색바 */}
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="업체명 검색 (예: 그로브, 코코스키)"
          className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500"
        />
        <button
          onClick={search}
          disabled={loading}
          className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm"
        >
          {loading ? "..." : "검색"}
        </button>
      </div>

      {/* 검색 결과 */}
      {results.length > 0 && !selectedBiz && (
        <div className="bg-gray-800 rounded-lg max-h-48 overflow-y-auto">
          {results.map((biz) => (
            <button
              key={biz.name}
              onClick={() => loadClips(biz.name)}
              className="w-full text-left px-4 py-2 hover:bg-gray-700 text-sm text-gray-300 border-b border-gray-700 last:border-0"
            >
              {biz.name}
            </button>
          ))}
        </div>
      )}

      {/* 선택된 업체의 클립 목록 */}
      {selectedBiz && clips.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-blue-400">{selectedBiz} - {clips.length}개 영상</span>
            <button onClick={() => { setSelectedBiz(""); setClips([]); }} className="text-xs text-gray-500 hover:text-gray-300">
              다시 검색
            </button>
          </div>
          <ul className="space-y-1 max-h-40 overflow-y-auto">
            {clips.map((clip) => (
              <li key={clip.path} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedClips.includes(clip.path)}
                  onChange={() => toggleClip(clip.path)}
                  className="accent-blue-500"
                />
                <span className="text-gray-300 truncate">{clip.rel_path}</span>
                <span className="text-gray-500 text-xs shrink-0">{clip.size_mb}MB</span>
              </li>
            ))}
          </ul>
          <button
            onClick={confirm}
            disabled={selectedClips.length === 0}
            className={`mt-3 w-full py-2 rounded-lg text-sm font-bold
              ${selectedClips.length > 0 ? "bg-blue-600 hover:bg-blue-500" : "bg-gray-700 text-gray-500"}`}
          >
            {selectedClips.length}개 영상 선택 완료
          </button>
        </div>
      )}

      {selectedBiz && clips.length === 0 && !loading && (
        <p className="text-gray-500 text-sm">영상 파일이 없습니다</p>
      )}
    </div>
  );
}
