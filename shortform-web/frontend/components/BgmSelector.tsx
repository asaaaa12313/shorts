"use client";

const GENRES = [
  { id: "", label: "AI 자동 추천", emoji: "🤖" },
  { id: "신남", label: "신남", emoji: "🔥" },
  { id: "잔잔", label: "잔잔", emoji: "🌊" },
  { id: "밝음", label: "밝음", emoji: "☀️" },
  { id: "강렬한", label: "강렬한", emoji: "⚡" },
  { id: "펑키", label: "펑키", emoji: "🎸" },
  { id: "클래식", label: "클래식", emoji: "🎻" },
  { id: "팝", label: "팝", emoji: "🎵" },
  { id: "일본풍", label: "일본풍", emoji: "🗾" },
  { id: "크리스마스", label: "크리스마스", emoji: "🎄" },
];

interface Props {
  selected: string;
  onSelect: (genre: string) => void;
}

export default function BgmSelector({ selected, onSelect }: Props) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
      {GENRES.map((genre) => (
        <button
          key={genre.id}
          onClick={() => onSelect(genre.id)}
          className={`px-3 py-2 rounded-lg text-sm transition-colors
            ${selected === genre.id
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
        >
          {genre.emoji} {genre.label}
        </button>
      ))}
    </div>
  );
}
