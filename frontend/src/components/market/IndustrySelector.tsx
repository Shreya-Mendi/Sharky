"use client";

interface Props {
  industries: { industry: string; deal_count: number }[];
  selected: string;
  onSelect: (industry: string) => void;
}

export default function IndustrySelector({ industries, selected, onSelect }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
      <button
        onClick={() => onSelect("All Industries")}
        className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
          selected === "All Industries"
            ? "bg-blue-600 text-white"
            : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/80"
        }`}
      >
        All Industries
      </button>
      {industries.map((ind) => (
        <button
          key={ind.industry}
          onClick={() => onSelect(ind.industry)}
          className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
            selected === ind.industry
              ? "bg-blue-600 text-white"
              : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white/80"
          }`}
        >
          {ind.industry} ({ind.deal_count})
        </button>
      ))}
    </div>
  );
}
