"use client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface VideoFile {
  filename: string;
  size_mb: number;
  created_at: string;
}

interface Props {
  videos: VideoFile[];
  selected: string;
  onSelect: (filename: string) => void;
}

export default function VideoSelector({ videos, selected, onSelect }: Props) {
  if (videos.length === 0) {
    return <p className="text-gray-500 text-sm">완성된 영상이 없습니다. 먼저 숏폼을 만들어주세요.</p>;
  }

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return `${d.getMonth() + 1}월 ${d.getDate()}일`;
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {videos.map((v) => {
        const isSelected = selected === v.filename;
        return (
          <button
            key={v.filename}
            onClick={() => onSelect(v.filename)}
            className={`text-left rounded-lg overflow-hidden transition-all
              ${isSelected
                ? "ring-2 ring-blue-500 bg-blue-600/10"
                : "bg-gray-800 hover:bg-gray-750"}`}
          >
            <video
              src={`${API_URL}/api/download/${v.filename}`}
              className="w-full"
              style={{ aspectRatio: "9/16", maxHeight: "200px", objectFit: "cover" }}
              preload="metadata"
              muted
            />
            <div className="p-3">
              <p className="text-sm text-gray-300 truncate">{v.filename}</p>
              <p className="text-xs text-gray-500 mt-1">
                {v.size_mb}MB{v.created_at && ` · ${formatDate(v.created_at)}`}
              </p>
              {isSelected && <p className="text-xs text-blue-400 mt-1">선택됨</p>}
            </div>
          </button>
        );
      })}
    </div>
  );
}
