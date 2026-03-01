"use client";

const COLORS = [
  { id: "", label: "기본", colors: ["#ffffff", "#e6e6e6"] },
  { id: "neon", label: "네온", colors: ["#00ffff", "#ff00ff", "#00ff80"] },
  { id: "warm", label: "따뜻한", colors: ["#ff8c50", "#ffc83c", "#ff6464"] },
  { id: "cool", label: "시원한", colors: ["#50c8ff", "#64ffdc", "#82b4ff"] },
  { id: "pastel", label: "파스텔", colors: ["#ffb4c8", "#b4c8ff", "#c8ffc8"] },
  { id: "rainbow", label: "레인보우", colors: ["#ff5050", "#ffff50", "#50ff50", "#50b4ff", "#c864ff"] },
  { id: "gold", label: "골드", colors: ["#ffd700", "#ffc850", "#ffe678"] },
  { id: "pink", label: "핑크", colors: ["#ff64c8", "#ff96b4", "#e664ff"] },
  { id: "mint", label: "민트", colors: ["#64ffc8", "#96ffdc", "#50e6b4"] },
];

interface Props {
  selected: string;
  onSelect: (color: string) => void;
}

export default function SubtitleColorSelector({ selected, onSelect }: Props) {
  return (
    <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
      {COLORS.map((c) => (
        <button
          key={c.id}
          onClick={() => onSelect(c.id)}
          className={`px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2
            ${selected === c.id
              ? "bg-purple-600 text-white ring-2 ring-purple-400"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"}`}
        >
          <span className="flex gap-0.5">
            {c.colors.map((hex, i) => (
              <span
                key={i}
                className="w-3 h-3 rounded-full inline-block"
                style={{ backgroundColor: hex }}
              />
            ))}
          </span>
          <span>{c.label}</span>
        </button>
      ))}
    </div>
  );
}
