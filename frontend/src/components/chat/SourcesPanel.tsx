"use client";

import { FileText, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface Source {
  episode: string;
  company_name: string;
  segment_type: string;
  text_snippet: string;
}

interface SourcesPanelProps {
  sources: Source[];
}

export default function SourcesPanel({ sources }: SourcesPanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (sources.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        Sources will appear here after your first question.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
        <FileText size={14} /> Sources ({sources.length})
      </h3>
      {sources.map((src, i) => (
        <div key={i} className="bg-white/5 rounded-lg overflow-hidden">
          <button
            onClick={() => setExpanded(expanded === i ? null : i)}
            className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-white/5"
          >
            <div>
              <span className="text-blue-400 font-mono text-xs">{src.episode}</span>
              <span className="text-slate-400 text-xs ml-2">{src.company_name}</span>
            </div>
            {expanded === i ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {expanded === i && (
            <div className="px-3 pb-3">
              <span className="text-xs text-slate-500 block mb-1">{src.segment_type}</span>
              <p className="text-xs text-slate-400">{src.text_snippet}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
