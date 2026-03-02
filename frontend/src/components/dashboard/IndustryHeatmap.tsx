"use client";

import { motion } from "framer-motion";
import type { Industry } from "@/lib/api";

interface Props {
  industries: Industry[];
}

function getBorderColor(successRate: number): string {
  if (successRate > 0.5) return "border-emerald-500/60";
  if (successRate > 0.3) return "border-amber-500/60";
  return "border-rose-500/60";
}

function getBgColor(successRate: number): string {
  if (successRate > 0.5) return "bg-emerald-500/10";
  if (successRate > 0.3) return "bg-amber-500/10";
  return "bg-rose-500/10";
}

export default function IndustryHeatmap({ industries }: Props) {
  const sorted = [...industries].sort((a, b) => b.deal_count - a.deal_count);

  return (
    <div className="glass p-5">
      <h3 className="text-sm font-semibold text-white/50 mb-4">Industry Landscape</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {sorted.map((ind, i) => (
          <motion.div
            key={ind.industry}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.03 }}
            className={`rounded-xl border p-3 ${getBorderColor(ind.success_rate)} ${getBgColor(ind.success_rate)}`}
          >
            <div className="text-sm font-medium truncate">{ind.industry}</div>
            <div className="text-xs text-white/40 mt-1">{ind.deal_count} deals</div>
            <div className="text-xs text-white/30 mt-0.5">
              {(ind.success_rate * 100).toFixed(0)}% success
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
