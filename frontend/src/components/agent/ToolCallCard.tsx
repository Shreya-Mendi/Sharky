"use client";

import { useState } from "react";
import {
  Search,
  BarChart3,
  Target,
  TrendingUp,
  Loader2,
  CheckCircle,
} from "lucide-react";

interface Props {
  tool: string;
  input?: Record<string, unknown>;
  result?: unknown;
  status: "running" | "complete";
}

const TOOL_ICONS: Record<string, typeof Search> = {
  search_deals: Search,
  get_market_stats: BarChart3,
  predict_deal: Target,
  analyze_patterns: TrendingUp,
};

export default function ToolCallCard({ tool, input, result, status }: Props) {
  const [showInput, setShowInput] = useState(false);

  const Icon = TOOL_ICONS[tool] || Search;

  const resultSummary =
    result != null ? JSON.stringify(result).slice(0, 100) : null;

  return (
    <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
      <div className="flex items-start gap-3">
        {/* Left icon */}
        <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
          <Icon size={18} className="text-blue-400" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-bold text-white/90 truncate">
              {tool}
            </span>
            {status === "running" ? (
              <Loader2 size={16} className="text-blue-400 animate-spin flex-shrink-0" />
            ) : (
              <CheckCircle size={16} className="text-emerald-400 flex-shrink-0" />
            )}
          </div>

          {/* Collapsible input params */}
          {input && Object.keys(input).length > 0 && (
            <div className="mt-2">
              <button
                onClick={() => setShowInput(!showInput)}
                className="text-xs text-white/40 hover:text-white/60 transition-colors"
              >
                {showInput ? "Hide params" : "Show params"}
              </button>
              {showInput && (
                <pre className="mt-1 text-xs text-white/30 bg-white/[0.03] rounded-lg p-2 overflow-x-auto custom-scrollbar">
                  {JSON.stringify(input, null, 2)}
                </pre>
              )}
            </div>
          )}

          {/* Result summary */}
          {status === "complete" && resultSummary && (
            <p className="mt-2 text-xs text-white/40 truncate">
              {resultSummary}
              {JSON.stringify(result).length > 100 && "..."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
